import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdir, mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'
import { build, preview } from 'vite'
import { previewDemo } from '../../demo/build/preview.mjs'
import { onlineHarness, unusedPort } from './online_harness.mjs'

const root = fileURLToPath(new URL('../../../', import.meta.url))
const web = resolve(root, 'ui_web')
const map = JSON.parse(await readFile(resolve(root, 'docs/strategy-research/map.json'), 'utf8'))
const mode = process.argv[2]
assert.ok(mode === 'online' || mode === 'static', 'Choose online or static')
const screenshotDir = process.env.LAB_RESEARCH_MAP_SCREENSHOTS
const strategyId = map.nodes.find(node => node.kind === 'strategy').id
const defaultStrategy = map.nodes.find(node => node.id === strategyId)
const defaultStrategyPath = `/roadmap/${strategyId}`
const baselineId = 'baseline-futures-long'
const basisStudy = 'study-basis-historical'
const errors = []
const businessRequests = []
const staticRequests = []
const heading = (page, name) => page.getByRole('heading', { name, exact: true })
const nodeById = (page, id) => page.getByTestId(`rf__node-${id}`)
const inspector = page => page.getByRole('region', { name: '研究详情' })
const inspectorTitle = (page, id) => heading(inspector(page), map.nodes.find(node => node.id === id).title)

async function waitForActiveEdges(page, graph, nodeId) {
  const selector = '.research-map__edge--active'
  const expected = graph.edges
    .filter(({ from, to }) => from === nodeId || to === nodeId)
    .map(({ from, to, kind }) => `${from}:${to}:${kind}`)
    .sort()
  try {
    await page.waitForFunction(({ selector, expected }) => {
      const actual = Array.from(document.querySelectorAll(selector), edge => edge.getAttribute('data-id')).sort()
      return actual.length === expected.length && actual.every((id, index) => id === expected[index])
    }, { selector, expected }, { timeout: 4000 })
  } catch (error) {
    if (error.name !== 'TimeoutError') throw error
    const actual = await page.locator(selector).evaluateAll(edges => edges.map(edge => edge.getAttribute('data-id')).sort())
    throw new Error(`Active edges did not match for ${nodeId}. Expected ${JSON.stringify(expected)}, actual ${JSON.stringify(actual)}`, { cause: error })
  }
}

async function verifyGraph(page) {
  await heading(page, '策略研究地图').waitFor()
  await verifyStrategyLocation(page, defaultStrategy)
  for (const { id } of map.nodes) await nodeById(page, id).waitFor()
  for (const { from, to, kind } of map.edges) {
    const edge = page.getByTestId(`rf__edge-${from}:${to}:${kind}`).locator('path.react-flow__edge-path')
    await edge.waitFor({ state: 'attached' })
    assert.ok(await edge.evaluate(path => path.getTotalLength() > 0 && getComputedStyle(path).stroke !== 'none'))
  }
  await checkReadableFrame(page)
  const cards = await page.locator('.research-map__card').evaluateAll(cards => cards.map(card => {
    const { x, y, width, height } = card.getBoundingClientRect()
    return { id: card.closest('[data-id]').dataset.id, x, y, width, height }
  }))
  for (const [i, a] of cards.entries()) {
    for (const b of cards.slice(i + 1)) {
      const overlap = a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y
      assert.equal(overlap, false, `Cards overlap: ${a.id} and ${b.id}`)
    }
  }
  const canvas = await page.locator('.research-map__canvas').boundingBox()
  for (const card of cards) {
    assert.ok(card.x >= canvas.x && card.x + card.width <= canvas.x + canvas.width, `Desktop clips ${card.id}`)
  }
  for (const { from, to } of map.edges) {
    const parent = cards.find(card => card.id === from)
    const child = cards.find(card => card.id === to)
    assert.ok(parent.y + parent.height < child.y)
  }
  await verifyEdgeClearance(page)
  await screenshot(page, 'desktop')
  const view = page.locator('.react-flow__viewport')
  const transform = () => view.evaluate(el => el.style.transform)
  const initial = await transform()
  await page.getByRole('button', { name: '放大', exact: true }).click()
  await page.waitForFunction(start => document.querySelector('.react-flow__viewport').style.transform !== start, initial)
  const box = await page.locator('.research-map__canvas').boundingBox()
  await page.mouse.move(box.x + box.width / 2, box.y + 8)
  await page.mouse.down()
  const beforePan = await transform()
  await page.mouse.move(box.x + box.width / 2 + 30, box.y + 28, { steps: 5 })
  await page.mouse.up()
  assert.notEqual(await transform(), beforePan)
  const afterPan = await transform()
  await page.getByRole('button', { name: '适应视图', exact: true }).click()
  await page.waitForFunction(start => document.querySelector('.react-flow__viewport').style.transform !== start, afterPan)

  await nodeById(page, baselineId).press('Enter')
  await inspectorTitle(page, baselineId).waitFor()
  await inspector(page).getByText('expiry_to_M1_v1', { exact: true }).waitFor()
  await waitForActiveEdges(page, map, baselineId)
  assert.ok(await nodeById(page, strategyId).evaluate(node => node.classList.contains('research-map__node--related')))
  await nodeById(page, basisStudy).click()
  await inspectorTitle(page, basisStudy).waitFor()
  await waitForActiveEdges(page, map, basisStudy)
  await heading(inspector(page), '统计分析计划').waitFor()
  await heading(inspector(page), '研究结论').waitFor()
  await inspector(page).getByRole('link', { name: 'Static Demo 描述性结果捕获' }).waitFor()
  await screenshot(page, 'study')
  await inspector(page).getByRole('button', { name: '基差变化贡献', exact: true }).click()
  await inspectorTitle(page, 'dimension-futures-long-basis').waitFor()

  for (const node of map.nodes.filter(({ kind }) => kind === 'study')) {
    await nodeById(page, node.id).press('Enter')
    await inspectorTitle(page, node.id).waitFor()
    for (const { name } of node.analyses) await inspector(page).getByRole('listitem').filter({ hasText: `${name} ·` }).waitFor()
    await waitForActiveEdges(page, map, node.id)
  }
}

async function screenshot(page, name) {
  if (!screenshotDir) return
  await mkdir(screenshotDir, { recursive: true })
  await page.screenshot({ path: resolve(screenshotDir, `${mode}-${name}.png`), fullPage: true })
}

async function checkReadableFrame(page) {
  await page.waitForFunction(() => {
    const view = document.querySelector('.react-flow__viewport')
    return view && new DOMMatrix(getComputedStyle(view).transform).a >= 0.79
  })
  const box = await nodeById(page, strategyId).boundingBox()
  const canvas = await page.locator('.research-map__canvas').boundingBox()
  assert.ok(box.x >= canvas.x && box.x + box.width <= canvas.x + canvas.width)
  assert.ok(box.y >= canvas.y && box.y + box.height <= canvas.y + canvas.height)
  assert.deepEqual(await page.locator('.research-map__node-title').evaluateAll(titles =>
    titles.filter(title => title.scrollHeight > title.clientHeight + 1).map(title => title.textContent)), [])
}

async function verifyNarrow(page) {
  const size = page.viewportSize()
  await page.setViewportSize({ width: 700, height: 960 })
  await page.reload()
  await inspectorTitle(page, strategyId).waitFor()
  await checkReadableFrame(page)
  const graph = await page.locator('.research-map__graph').boundingBox()
  const details = await inspector(page).boundingBox()
  assert.ok(details.y >= graph.y + graph.height)
  await screenshot(page, 'narrow')
  await page.setViewportSize(size)
}

async function verifyEdgeClearance(page) {
  const intersections = await page.locator('path.react-flow__edge-path').evaluateAll(paths => {
    const cards = [...document.querySelectorAll('.research-map__card')].map(card => card.getBoundingClientRect())
    return paths.flatMap(path => {
      const transform = path.getScreenCTM()
      const length = path.getTotalLength()
      return Array.from({ length: Math.ceil(length / 2) }, (_, i) => (i + 0.5) * 2)
        .map(distance => new DOMPoint(path.getPointAtLength(distance).x, path.getPointAtLength(distance).y).matrixTransform(transform))
        .some(({ x, y }) => cards.some(card => x > card.left + 2 && x < card.right - 2 && y > card.top + 2 && y < card.bottom - 2))
        ? [path.id] : []
    })
  })
  assert.deepEqual(intersections, [], 'Connectors avoid card interiors')
}

function multiStrategyFixture() {
  const fixture = structuredClone(map)
  const [strategy, , dimension] = fixture.nodes
  const shared = fixture.nodes.find(node => node.id === basisStudy)
  const secondSource = fixture.nodes.find(node => node.id === 'study-market-regime')
  const review = { status: 'inconclusive', summary: '合成浏览器测试结论', review: '合成验收说明' }
  for (const source of [shared, secondSource]) {
    source.evidence = 'accepted'
    source.conclusion = review
    source.references = shared.references
  }
  fixture.nodes.push(
    { ...strategy, id: 'strategy-planned-example', title: '规划中测试策略',
      planning: 'planned', implementation: 'none', parameters: undefined, references: [] },
    { ...strategy, id: 'finding-browser-example', kind: 'finding', title: '合成测试发现',
      parameters: undefined, evidence: 'accepted', conclusion: review, references: [] },
  )
  fixture.edges.push(
    { from: dimension.id, to: shared.id, kind: 'attach' },
    { from: shared.id, to: 'finding-browser-example', kind: 'derived_from' },
    { from: secondSource.id, to: 'finding-browser-example', kind: 'derived_from' },
  )
  return fixture
}

const strategyUrl = (base, id) => new URL((mode === 'static' ? '#/roadmap' : '/roadmap') + (id ? `/${id}` : ''), base).href
const strategyLocation = url => mode === 'static' ? url.hash.slice(1) : url.pathname
const strategyMenu = page => page.getByRole('menu', { name: '业务导航' })
const strategyGroup = page => strategyMenu(page).getByRole('menuitem', { name: '策略', exact: true })
const strategyLink = (page, strategy, collapsed = false) =>
  (collapsed ? page.locator('.ant-menu-submenu-popup:visible') : strategyMenu(page))
    .getByRole('link', { name: strategy.title, exact: true })

async function verifyStrategyLocation(page, strategy, collapsed = false) {
  const path = `/roadmap/${strategy.id}`
  await page.waitForURL(url => strategyLocation(url) === path)
  await nodeById(page, strategy.id).waitFor()
  await heading(inspector(page), strategy.title).waitFor()
  assert.deepEqual(await page.locator('.ant-breadcrumb li:not(.ant-breadcrumb-separator)').allTextContents(), ['策略', strategy.title])
  if (collapsed) await strategyGroup(page).click()
  const link = strategyLink(page, strategy, collapsed)
  await link.waitFor()
  assert.equal(await link.getAttribute('href'), mode === 'static' ? '#' + path : path)
  assert.ok(await link.evaluate(el => el.closest('li').classList.contains('ant-menu-item-selected')))
}

async function verifyMultipleStrategies(page, base, fixture) {
  const [first, second] = fixture.nodes.filter(node => node.kind === 'strategy')
  await page.goto(strategyUrl(base, first.id))
  await verifyStrategyLocation(page, first)
  assert.deepEqual(await strategyMenu(page).locator('a[href*="/roadmap/"]').allTextContents(), [first.title, second.title])
  assert.equal(await page.getByRole('combobox', { name: '选择策略' }).count(), 0)
  await verifyEdgeClearance(page)
  assert.equal(await nodeById(page, basisStudy).count(), 1)
  const accents = await page.locator('.research-map__card').evaluateAll(cards =>
    cards.map(card => getComputedStyle(card).getPropertyValue('--map-accent').trim()))
  assert.equal(new Set(accents).size, 5)
  await nodeById(page, basisStudy).press('Enter')
  await inspectorTitle(page, basisStudy).waitFor()
  await waitForActiveEdges(page, fixture, basisStudy)
  assert.equal(await page.locator('.research-map__node--related [data-kind="dimension"]').count(), 2)
  await nodeById(page, 'finding-browser-example').press('Enter')
  await heading(inspector(page), '合成测试发现').waitFor()
  await waitForActiveEdges(page, fixture, 'finding-browser-example')
  assert.equal(await inspector(page).getByRole('link', { name: 'Static Demo 描述性结果捕获' }).count(), 2)
  await screenshot(page, 'multi-strategy')

  await strategyLink(page, second).click()
  await verifyStrategyLocation(page, second)
  assert.equal(await page.locator('.research-map__card').count(), 1)
  await page.reload()
  await verifyStrategyLocation(page, second)
  await page.goBack()
  await verifyStrategyLocation(page, first)
  await page.goForward()
  await verifyStrategyLocation(page, second)
  await screenshot(page, 'planned-strategy')

  await page.getByRole('button', { name: '折叠导航' }).click()
  await verifyStrategyLocation(page, second, true)
  await strategyLink(page, first, true).click()
  await page.waitForURL(url => strategyLocation(url) === defaultStrategyPath)
  await page.getByRole('button', { name: '展开导航' }).click()
  await verifyStrategyLocation(page, first)

  for (const id of ['strategy-unknown', undefined]) {
    await page.goto(strategyUrl(base, id))
    await verifyStrategyLocation(page, first)
  }
}

async function verifyStaticFixture(browser, fixture) {
  const outDir = await mkdtemp(resolve(web, '.build/research-map-fixture-'))
  let server
  try {
    await build({
      configFile: resolve(web, 'demo/build/vite.config.ts'),
      logLevel: 'error',
      build: { outDir },
      plugins: [{
        name: 'research-map-browser-fixture',
        enforce: 'pre',
        resolveId(id) {
          if (id === 'virtual:strategy-research-map' || id === 'virtual:demo-data') return '\0research-map-fixture:' + id
        },
        load(id) {
          if (id === '\0research-map-fixture:virtual:strategy-research-map') return `export default ${JSON.stringify(fixture)}`
          if (id === '\0research-map-fixture:virtual:demo-data') return 'export default {}'
        },
      }],
    })
    server = await preview({
      configFile: false, root: web, base: '/hg-market-state-lab/', publicDir: false, envDir: false,
      build: { outDir }, preview: { host: '127.0.0.1', port: 0 },
    })
    const base = `http://127.0.0.1:${server.httpServer.address().port}/hg-market-state-lab/`
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
    page.on('pageerror', error => errors.push(error.message))
    page.on('request', request => {
      if (/^\/(api|auth)\//.test(new URL(request.url()).pathname)) errors.push('Unexpected Static fixture API request')
    })
    await verifyMultipleStrategies(page, base, fixture)
  } finally {
    await server?.close()
    await rm(outDir, { recursive: true, force: true })
  }
}

async function verifyLinks(page) {
  const target = path => mode === 'static' ? `#${path}` : path
  const locations = [
    [strategyId, '查看日常数据', '/data', '数据总览'],
    [basisStudy, '查看历史基差研究', '/research/futures-basis', 'Futures Basis Research'],
    [baselineId, '查看期货展期做多回测', '/backtesting/futures-roll-long', '期货展期做多回测'],
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
    await page.waitForURL(url => url.hash === '#' + defaultStrategyPath)
    await verifyGraph(page)
    await verifyNarrow(page)
    const { bundles } = JSON.parse(await readFile(resolve(web, 'demo/bundles/manifest.json'), 'utf8'))
    assert.ok(!staticRequests.some(url => bundles.some(({ bundle_id }) => new URL(url).pathname.includes(`/assets/${bundle_id}-`))))
    await verifyLinks(page)
    await verifyStaticFixture(browser, multiStrategyFixture())
  } else {
    temporary = await mkdtemp(resolve(tmpdir(), 'strategy-research-map-auth-'))
    const backendPort = await unusedPort()
    const origin = 'http://127.0.0.1:5173'
    const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http', LAB_AUTH_ORIGIN: origin,
      LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'), LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'),
      LAB_BROWSER_API_ORIGIN: `http://127.0.0.1:${backendPort}` }
    harness = onlineHarness(env, root, resolve(web, '.build/strategy-research-map-acceptance'))
    const backend = harness.start('poetry', ['run', 'python', '-m', 'uvicorn', '--app-dir', 'ui_http/tests',
      'http_support.auth_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', String(backendPort), '--no-proxy-headers'])
    const frontend = harness.start(process.execPath, ['node_modules/vite/bin/vite.js', '--config', 'tests/config/vite.browser.config.ts',
      '--strictPort'], web)
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
    await page.waitForURL(url => url.pathname === defaultStrategyPath)
    await verifyGraph(page)
    await verifyNarrow(page)
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
    await page.getByRole('button', { name: '退出登录' }).click()
    await page.getByRole('button', { name: '登录', exact: true }).waitFor()
    const fixture = multiStrategyFixture()
    const planned = fixture.nodes.find(node => node.id === 'strategy-planned-example')
    await page.route(url => url.pathname.includes('__x00__virtual:strategy-research-map'), route => route.fulfill({
      contentType: 'application/javascript', body: `export default ${JSON.stringify(fixture)}`,
    }))
    await page.goto(strategyUrl(origin, planned.id))
    await page.getByRole('button', { name: '登录', exact: true }).waitFor()
    assert.equal(await heading(page, '策略研究地图').count(), 0)
    assert.equal(new URL(page.url()).pathname, `/roadmap/${planned.id}`)
    await login()
    await verifyStrategyLocation(page, planned)
    await verifyMultipleStrategies(page, origin, fixture)
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
