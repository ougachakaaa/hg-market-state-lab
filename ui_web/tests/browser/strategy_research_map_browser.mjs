import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'
import { previewDemo } from '../../demo/build/preview.mjs'
import { onlineHarness, unusedPort } from './online_harness.mjs'

const root = fileURLToPath(new URL('../../../', import.meta.url))
const web = resolve(root, 'ui_web')
const map = JSON.parse(await readFile(resolve(web, 'research-map/map.json'), 'utf8'))
const mode = process.argv[2]
assert.ok(mode === 'online' || mode === 'static', 'Choose online or static')
const errors = []
const businessRequests = []
const staticRequests = []
const heading = (page, name) => page.getByRole('heading', { name, exact: true })
const nodeById = (page, id) => page.getByTestId(`rf__node-${id}`)
const inspector = page => page.getByRole('region', { name: '研究详情' })
const inspectorTitle = (page, id) => heading(inspector(page), `${id} · ${map.nodes.find(node => node.id === id).title}`)

async function verifyGraph(page) {
  await heading(page, '策略研究地图').waitFor()
  assert.equal(await page.getByRole('menu', { name: '业务导航' }).getByRole('menuitem').first().innerText(), '策略研究地图')
  for (const { id } of map.nodes) await nodeById(page, id).waitFor()
  for (const { from, to, kind } of map.edges) {
    const edge = page.getByTestId(`rf__edge-${from}:${to}:${kind}`).locator('path.react-flow__edge-path')
    await edge.waitFor({ state: 'attached' })
    assert.ok(await edge.evaluate(path => path.getTotalLength() > 0 && getComputedStyle(path).stroke !== 'none'))
  }
  const view = page.locator('.react-flow__viewport')
  const transform = () => view.evaluate(el => el.style.transform)
  const initial = await transform()
  await page.getByRole('button', { name: '放大', exact: true }).click()
  await page.waitForFunction(start => document.querySelector('.react-flow__viewport').style.transform !== start, initial)
  const box = await page.locator('.research-map__canvas').boundingBox()
  await page.mouse.move(box.x + box.width / 2, box.y + 25)
  await page.mouse.down()
  const beforePan = await transform()
  await page.mouse.move(box.x + box.width / 2 + 30, box.y + 45, { steps: 5 })
  await page.mouse.up()
  assert.notEqual(await transform(), beforePan)
  const afterPan = await transform()
  await page.getByRole('button', { name: '适应视图', exact: true }).click()
  await page.waitForFunction(start => document.querySelector('.react-flow__viewport').style.transform !== start, afterPan)

  await nodeById(page, 'B0').press('Enter')
  await inspectorTitle(page, 'B0').waitFor()
  await inspector(page).getByText('expiry_to_M1_v1', { exact: true }).waitFor()
  assert.equal(await page.locator('.research-map__edge--active').count(), 3)
  assert.ok(await nodeById(page, 'D0').evaluate(node => node.classList.contains('research-map__node--dependency')))
  await nodeById(page, 'A1').click()
  await inspectorTitle(page, 'A1').waitFor()
  await inspector(page).getByText('待研究或验收', { exact: true }).waitFor()
  await inspector(page).getByRole('button', { name: /^O1 / }).click()
  await inspectorTitle(page, 'O1').waitFor()

  // Also exercises any new Study added by editing just the document.
  for (const node of map.nodes.filter(({ kind }) => kind === 'study')) {
    await nodeById(page, node.id).press('Enter')
    await inspectorTitle(page, node.id).waitFor()
    for (const { name } of node.metrics) await inspector(page).getByRole('listitem').filter({ hasText: name }).waitFor()
    assert.equal(await page.locator('.research-map__edge--active').count(),
      map.edges.filter(edge => edge.from === node.id || edge.to === node.id).length)
  }
}

async function verifyLinks(page) {
  const target = path => mode === 'static' ? `#${path}` : path
  const locations = [
    ['S0', '查看日常数据', '/data', '数据总览'],
    ['A1', '查看历史基差研究', '/research/futures-basis', 'Futures Basis Research'],
    ['B0', '查看期货展期做多回测', '/backtesting/futures-roll-long', '期货展期做多回测'],
  ]
  for (const [node, label, path, title] of locations) {
    await nodeById(page, node).press('Enter')
    const link = inspector(page).getByRole('link', { name: label })
    assert.equal(await link.getAttribute('href'), target(path))
    await link.click()
    await page.waitForURL(url => (mode === 'static' ? url.hash : url.pathname) === target(path))
    await heading(page, title).waitFor()
    await page.goBack()
    await heading(page, '策略研究地图').waitFor()
  }
  await page.goto(mode === 'static' ? new URL('#/research', page.url()).href : new URL('/research', page.url()).href)
  await heading(page, '研究总览').waitFor()
  await page.goto(mode === 'static' ? new URL('#/backtesting', page.url()).href : new URL('/backtesting', page.url()).href)
  await heading(page, '回测总览').waitFor()
}

let browser, server, harness, temporary
try {
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
    ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  page.on('pageerror', error => errors.push(error.message))
  if (mode === 'static') {
    server = await previewDemo(0, { outputRoot: process.argv[3] })
    const base = `http://127.0.0.1:${server.httpServer.address().port}/hg-market-state-lab/`
    await page.route('**/*', async route => {
      const request = route.request()
      staticRequests.push(request.url())
      if (request.method() === 'GET' && request.url().startsWith(base) && ['document', 'script', 'stylesheet', 'image', 'font'].includes(request.resourceType())) await route.continue()
      else {
        errors.push(`Unexpected Static Demo request: ${request.method()} ${new URL(request.url()).pathname}`)
        await route.abort()
      }
    })
    await page.goto(base)
    await page.waitForURL('**/#/roadmap')
    await verifyGraph(page)
    const { bundles } = JSON.parse(await readFile(resolve(web, 'demo/bundles/manifest.json'), 'utf8'))
    assert.ok(!staticRequests.some(url => bundles.some(({ bundle_id }) => new URL(url).pathname.includes(`/assets/${bundle_id}-`))))
    await verifyLinks(page)
  } else {
    temporary = await mkdtemp(resolve(tmpdir(), 'strategy-research-map-auth-'))
    const backendPort = await unusedPort()
    const frontendPort = await unusedPort()
    const origin = `http://127.0.0.1:${frontendPort}`
    const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http', LAB_AUTH_ORIGIN: origin,
      LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'), LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'),
      LAB_BROWSER_API_ORIGIN: `http://127.0.0.1:${backendPort}` }
    harness = onlineHarness(env, root, resolve(web, '.build/strategy-research-map-acceptance'))
    const backend = harness.start('poetry', ['run', 'python', '-m', 'uvicorn', '--app-dir', 'ui_http/tests',
      'http_support.auth_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', String(backendPort), '--no-proxy-headers'])
    const frontend = harness.start(process.execPath, ['node_modules/vite/bin/vite.js', '--config', 'tests/config/vite.browser.config.ts',
      '--strictPort', '--port', String(frontendPort)], web)
    await harness.ready(`${env.LAB_BROWSER_API_ORIGIN}/auth/me`, backend, 401)
    await harness.ready(origin, frontend, 200)
    page.on('request', request => {
      if (new URL(request.url()).pathname.startsWith('/api/')) businessRequests.push(request.url())
    })
    await page.goto(origin)
    await page.getByRole('button', { name: '登录', exact: true }).waitFor()
    assert.equal(await heading(page, '策略研究地图').count(), 0)
    const password = randomBytes(24).toString('base64url')
    const registration = await page.request.post(`${origin}/auth/register`, {
      headers: { Origin: origin }, data: { username: 'research_map_browser', password },
    })
    assert.equal(registration.status(), 202)
    function cli(...args) {
      const result = spawnSync('poetry', ['run', 'lab', 'auth', ...args], { cwd: root, env, encoding: 'utf8' })
      assert.equal(result.status, 0, result.stderr)
      return result.stdout
    }
    const id = cli('pending').match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i)?.[0]
    assert.ok(id)
    cli('approve', id)
    async function login() {
      await page.getByLabel('用户名', { exact: true }).fill('research_map_browser')
      await page.getByLabel('密码', { exact: true }).fill(password)
      await page.getByRole('button', { name: '登录', exact: true }).click()
    }
    await login()
    await page.waitForURL('**/roadmap')
    await verifyGraph(page)
    assert.deepEqual(businessRequests, [], 'The map does not fetch business data')
    await verifyLinks(page)
    await page.getByRole('button', { name: '退出登录' }).click()
    await page.getByRole('button', { name: '登录', exact: true }).waitFor()
    await page.goto(`${origin}/research`)
    await page.getByRole('button', { name: '登录', exact: true }).waitFor()
    assert.equal(await heading(page, '研究总览').count(), 0)
    await login()
    await heading(page, '研究总览').waitFor()
    assert.equal(new URL(page.url()).pathname, '/research')
  }
  assert.deepEqual(errors, [])
  console.log(`PASS ${mode}: ${map.nodes.length} nodes, ${map.edges.length} edges, Inspector, keyboard, canvas, routes`)
} catch (error) {
  if (harness) await harness.save([], errors)
  throw error
} finally {
  await browser?.close()
  await server?.close()
  await harness?.stop()
  if (temporary) await rm(temporary, { recursive: true, force: true })
}
