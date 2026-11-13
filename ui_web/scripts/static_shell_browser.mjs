// D1 verification only: built artifact served as files; no backend or dev proxy.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { createServer } from 'node:http'
import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const web = fileURLToPath(new URL('../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'd1-shell-browser-'))
const prefix = '/hg-market-state-lab/'
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let server; let browser; let page
const pass = message => { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  const built = spawnSync('npm', ['run', 'test:static-shell'], { cwd: web, encoding: 'utf8', shell: process.platform === 'win32' })
  assert.equal(built.status, 0, built.stdout + built.stderr)
  const artifact = resolve(web, '.build/tests/shell')
  const inventory = JSON.parse(await readFile(resolve(artifact, 'shell-routes.json'), 'utf8'))
  const graph = JSON.parse(await readFile(resolve(artifact, 'shell-dependencies.json'), 'utf8'))
  assert.equal(inventory.routes.length, 7)
  assert.ok(graph.projectModules.some(module => module.id === 'src/app/ApplicationShell.tsx'))
  assert.ok(graph.projectModules.some(module => module.id === 'src/app/DailyDataLanding.tsx'))
  assert.ok(graph.projectModules.every(module => !/auth|features|shared\/http|app\/App\.tsx|app\/routes\.ts/.test(module.id)))
  evidence.dependencyGraph = graph
  pass('Built shared Shell/Landing graph excludes Auth, feature controllers and HTTP, including dynamic edges')
  server = createServer(async (request, response) => {
    const pathname = new URL(request.url, 'http://static.local').pathname
    if (!pathname.startsWith(prefix) || pathname.includes('..')) { response.writeHead(404).end(); return }
    const file = pathname.slice(prefix.length) || 'index.html'
    try {
      const body = await readFile(resolve(artifact, file))
      const type = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json' }[extname(file)] || 'application/octet-stream'
      response.writeHead(200, { 'Content-Type': type }).end(body)
    } catch { response.writeHead(404).end() }
  })
  await new Promise(done => server.listen(0, '127.0.0.1', done))
  const base = `http://127.0.0.1:${server.address().port}${prefix}`
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  evidence.browser = browser.version()
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  await context.route('**/*', async route => {
    const request = route.request()
    const url = new URL(request.url())
    evidence.requests.push({ url: url.href, type: request.resourceType(), method: request.method() })
    const allowed = url.origin === new URL(base).origin && url.pathname.startsWith(prefix) &&
      request.method() === 'GET' && ['document', 'script', 'stylesheet', 'font', 'image'].includes(request.resourceType())
    if (!allowed) { evidence.errors.push(`Forbidden network activity: ${url.href}`); await route.abort() }
    else await route.continue()
  })
  page = await context.newPage()
  page.setDefaultTimeout(10000)
  page.on('pageerror', error => evidence.errors.push(String(error)))
  page.on('requestfailed', request => evidence.errors.push(`Request failed: ${request.url()}`))
  page.on('console', message => { if (message.type() === 'error') evidence.errors.push(message.text()) })
  page.on('response', response => { if (response.status() >= 400) evidence.errors.push(`HTTP ${response.status()}: ${response.url()}`) })
  const current = async path => {
    const route = inventory.routes.find(route => route.path === path)
    await page.getByRole('heading', { name: route.title, exact: true }).waitFor()
    assert.equal(new URL(page.url()).pathname, prefix)
    assert.equal(new URL(page.url()).hash, `#${path}`)
    assert.ok((await page.locator('.ant-breadcrumb').textContent()).includes(route.title))
    assert.equal(await page.getByRole('button', { name: '退出登录' }).count(), 0)
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
  }
  const choose = async path => {
    const route = inventory.routes.find(route => route.path === path)
    const collapsed = await page.getByRole('button', { name: '展开导航', exact: true }).isVisible()
    const scope = collapsed && route.area !== '/backtesting'
      ? page.locator('.ant-menu-submenu-popup:visible') : page.getByRole('menu', { name: '业务导航' })
    const leaf = scope.getByRole('menuitem', { name: route.title, exact: true })
    if (route.area !== '/backtesting' && (collapsed || !await leaf.isVisible())) {
      await page.getByRole('menuitem', { name: inventory.areas[route.area].title, exact: true }).click()
    }
    await leaf.waitFor({ state: 'visible' })
    assert.equal(await leaf.getByRole('link').getAttribute('href'), `#${path}`)
    await leaf.click()
    await current(path)
  }
  await page.goto(base)
  await current('/research')
  for (const route of inventory.routes) {
    await choose(route.path)
    // Direct URL and reload use the same built HTML under the Pages base.
    await page.goto(`${base}#${route.path}`)
    await current(route.path)
    await page.reload()
    await current(route.path)
    const selected = page.locator('.ant-menu-item-selected')
    assert.equal(await selected.count(), 1)
    assert.equal(await selected.textContent(), route.title)
    for (const href of await page.locator('a[href]').evaluateAll(links => links.map(link => link.href))) {
      assert.equal(new URL(href).pathname, prefix)
      assert.equal(new URL(href).origin, new URL(base).origin)
    }
  }
  pass('All seven canonical identities: menu hrefs, direct hash load, reload, selected leaf, breadcrumb and base containment')
  await choose('/data')
  await page.getByRole('button', { name: '打开 MO Option Chain' }).click()
  await current('/data/mo-option-chain')
  await page.goBack(); await current('/data')
  await page.goForward(); await current('/data/mo-option-chain')
  await page.locator('.ant-breadcrumb').getByRole('link', { name: '日常数据', exact: true }).click()
  await current('/data')
  await page.getByRole('button', { name: '打开 MO Premium Plane' }).click()
  await current('/data/mo-premium-plane')
  await choose('/research/publications')
  await page.locator('.ant-breadcrumb').getByRole('link', { name: '研究', exact: true }).click()
  await current('/research')
  pass('Shared Daily Landing, both product buttons, parent breadcrumbs and real Back/Forward')
  for (const hash of ['', '#unknown', '#/unknown', '#/backtesting?run_id=server']) {
    await page.goto(`${base}${hash}`)
    await current(hash.includes('backtesting') ? '/backtesting' : '/research')
  }
  await page.evaluate(() => { location.hash = '#/unknown' })
  await current('/research')
  pass('Empty/unknown hashes normalize; static routing discards server run_id')
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto(`${base}#/research`)
    await current('/research')
    await page.getByRole('button', { name: width === 390 ? '展开导航' : '折叠导航', exact: true }).waitFor()
    // Explicit collapse/expand, then navigate all leaves in collapsed mode.
    if (width === 1440) await page.getByRole('button', { name: '折叠导航', exact: true }).click()
    for (const route of inventory.routes) await choose(route.path)
    await choose('/research/publications')
    await page.screenshot({ path: resolve(output, `explorer-collapsed-${width}.png`) })
    await page.getByRole('button', { name: '展开导航', exact: true }).click()
    await page.getByRole('button', { name: '折叠导航', exact: true }).waitFor()
    await choose('/research/publications')
    await page.screenshot({ path: resolve(output, `explorer-expanded-${width}.png`) })
  }
  pass('Collapsed/expanded desktop and narrow navigation keeps Explorer and every page accessible')
  await page.waitForLoadState('networkidle')
  assert.deepEqual(await context.cookies(), [])
  assert.deepEqual(evidence.errors, [])
  pass('Only static assets requested throughout; zero Auth/API/external network activity and no browser errors')
  evidence.status = 'PASS'
} catch (error) {
  evidence.status = 'FAIL'; evidence.errors.push(error.stack || String(error)); process.exitCode = 1
  if (page) await page.screenshot({ path: resolve(output, 'failure.png') }).catch(() => {})
} finally {
  if (browser) await browser.close()
  if (server) await new Promise(done => server.close(done))
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(evidence, null, 2))
  console.log(`Static Shell: ${evidence.status}; artifacts: ${output}`)
  if (evidence.status !== 'PASS') console.error(evidence.errors)
}
