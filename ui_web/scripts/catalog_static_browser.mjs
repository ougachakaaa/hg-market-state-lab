// D2-C verification only: built artifact served as files; no backend or dev proxy.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { createServer } from 'node:http'
import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const web = fileURLToPath(new URL('../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'd2c-catalog-'))
const prefix = '/hg-market-state-lab/'
const disclosure = '静态测试数据 · 非正式 D3 Capability Example · 非在线发现 · 浏览器未执行认证 GET，也未探测 Provider、Token 或缓存。'
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let server; let browser; let page
const pass = message => { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  const descriptor = JSON.parse(await readFile(resolve(web, 'src/features/research_catalog/api/catalog.fixture.json'), 'utf8'))
  const built = spawnSync('npm', ['run', 'test:catalog-static'], { cwd: web, encoding: 'utf8', shell: process.platform === 'win32' })
  assert.equal(built.status, 0, built.stdout + built.stderr)
  const artifact = resolve(web, '.build/tests/catalog')
  const graph = JSON.parse(await readFile(resolve(artifact, 'presentation-dependencies.json'), 'utf8'))
  assert.ok(graph.includes('src/features/research_catalog/page/ResearchOverviewPresentation.tsx'))
  assert.ok(graph.includes('src/features/research_catalog/api/validateCatalog.ts'))
  assert.ok(graph.includes('src/features/research_catalog/static/useStaticCatalog.ts'))
  assert.ok(graph.includes('src/features/research_catalog/model/localCases.ts'))
  assert.ok(graph.includes('src/demo/shell/hashRoutes.ts'))
  assert.ok(!graph.some(id => /shared\/http|app\/auth|api\/catalog\.ts|hooks\/useCatalog\.ts|page\/ResearchWorkspacePage\.tsx|research_explorer|futures_basis_research|backtesting/.test(id)))
  evidence.dependencyGraph = graph
  pass('Shared presentation/validator/static controller load without Auth, HTTP or production controller; D1 hash router is the intentional composition module')
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

  await page.goto(base)
  await page.getByRole('heading', { name: '研究总览', exact: true }).waitFor()
  await page.getByText(disclosure, { exact: true }).waitFor()
  await page.getByText(descriptor.name, { exact: true }).waitFor()
  assert.equal(await page.getByText('实现：supported', { exact: true }).count(), 1)
  assert.equal(await page.getByText('live readiness: not_probed', { exact: true }).count(), 1)
  assert.equal(await page.getByText('嵌入能力示例', { exact: true }).count(), 1)
  assert.equal(await page.getByText('Price Segmentation', { exact: true }).count(), 1)
  assert.equal(await page.getByText('独立在线页面 · 独立离线报告生成', { exact: true }).count(), 1)
  assert.equal(await page.getByRole('button', { name: '重试目录' }).count(), 0)
  pass('Validated embedded list renders name/status/readiness and official local cases with explicit static origin')

  const online = page.getByRole('region', { name: '在线能力发现' })
  await online.getByRole('button', { name: '查看详情' }).click()
  const selected = page.getByRole('region', { name: '所选研究详情' })
  await selected.getByText(descriptor.id, { exact: true }).waitFor()
  await selected.getByText(/supported · live readiness: not_probed/).waitFor()
  await selected.getByText(/静态演示不执行认证 GET/).waitFor()
  await selected.getByText(/不是默认值/).waitFor()
  assert.equal(await selected.getByText(/Embedded Capability Example · 静态能力描述/).count(), 1)
  await selected.getByRole('button', { name: '完整能力描述（原始字段）' }).click()
  const raw = await selected.locator('pre').textContent()
  assert.deepEqual(JSON.parse(raw), descriptor)
  pass('Selected capability shows its matching validated detail, access disclosure and complete raw descriptor')

  const local = page.getByRole('region', { name: '本地研究与离线工作流' })
  await local.getByRole('button', { name: '查看详情' }).first().click()
  await selected.getByText(/observe_price_segments/).waitFor()
  await selected.getByText(/静态演示不执行 Python、在线 Run 或报告生成/).waitFor()
  assert.equal(await selected.getByText(/supported · live readiness: not_probed/).count(), 0)
  assert.equal(await selected.getByText('静态能力详情未嵌入').count(), 0)
  pass('Local case selection replaces online detail locally and shows formal case instructions without a request')

  await local.getByRole('button', { name: '进入历史基差研究' }).click()
  await page.getByRole('heading', { name: '静态导航目标', exact: true }).waitFor()
  assert.equal(new URL(page.url()).hash, '#/research/futures-basis')
  await page.getByTestId('static-route').getByText('/research/futures-basis', { exact: true }).waitFor()
  await page.getByRole('button', { name: '返回研究总览' }).click()
  await page.getByRole('heading', { name: '研究总览', exact: true }).waitFor()

  await page.getByRole('button', { name: '浏览已发布研究结果' }).click()
  await page.getByRole('heading', { name: '静态导航目标', exact: true }).waitFor()
  assert.equal(new URL(page.url()).hash, '#/research/publications')
  await page.getByTestId('static-route').getByText('/research/publications', { exact: true }).waitFor()
  await page.goBack()
  await page.getByRole('heading', { name: '研究总览', exact: true }).waitFor()
  pass('Explorer and Futures Basis callbacks use the D1 hash adapter and Back returns to the catalog')

  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 })
    await page.screenshot({ path: resolve(output, `presentation-${width}.png`), fullPage: true })
  }
  await page.reload()
  await page.getByRole('heading', { name: '研究总览', exact: true }).waitFor()
  await page.getByText(descriptor.name, { exact: true }).waitFor()
  await page.waitForLoadState('networkidle')
  assert.deepEqual(await context.cookies(), [])
  assert.equal(evidence.requests.some(request => /\/api\/|\/auth\/|research\/capabilities/.test(new URL(request.url).pathname)), false)
  assert.deepEqual(evidence.errors, [])
  pass('Only static assets requested throughout; zero Auth/API/provider network activity and no browser errors')
  evidence.status = 'PASS'
} catch (error) {
  evidence.status = 'FAIL'; evidence.errors.push(error.stack || String(error)); process.exitCode = 1
  if (page) await page.screenshot({ path: resolve(output, 'failure.png') }).catch(() => {})
} finally {
  if (browser) await browser.close()
  if (server) await new Promise(done => server.close(done))
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(evidence, null, 2))
  console.log(`Static Research Overview: ${evidence.status}; artifacts: ${output}`)
  if (evidence.status !== 'PASS') console.error(evidence.errors)
}
