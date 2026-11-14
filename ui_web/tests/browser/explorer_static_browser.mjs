// D2-D verification only: built artifact served as files; no backend or dev proxy.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { createServer } from 'node:http'
import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const web = fileURLToPath(new URL('../../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'd2d-explorer-'))
const prefix = '/hg-market-state-lab/'
const disclosure = '静态测试数据 · 非正式 D3 Publication Example · 未查询在线 Publication Store · 未执行研究 · 不代表实时服务或 Provider 状态；示例 Provenance / Source Metadata 不证明真实市场来源。'
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let server; let browser; let page
const pass = message => { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  const built = spawnSync('npm', ['run', 'test:explorer-static'], { cwd: web, encoding: 'utf8', shell: process.platform === 'win32' })
  assert.equal(built.status, 0, built.stdout + built.stderr)
  const artifact = resolve(web, '.build/tests/explorer')
  const graph = JSON.parse(await readFile(resolve(artifact, 'presentation-dependencies.json'), 'utf8'))
  for (const module of [
    'src/features/research_explorer/page/ResearchExplorerPresentation.tsx',
    'src/features/research_explorer/api/validateResearch.ts',
    'src/features/research_explorer/api/validateEmbeddedPublication.ts',
    'src/features/research_explorer/static/useStaticExplorer.ts',
    'src/features/research_explorer/components/AnalysisDetails.tsx',
    'src/shared/visualization/ChartView.tsx',
    '../market_research/tests/fixtures/publication_visualization_v1.json',
  ]) assert.ok(graph.includes(module), `dependency graph must include ${module}`)
  assert.ok(!graph.some(id => /shared\/http|app\/auth|api\/research\.ts|hooks\/useExplorer\.ts|page\/ResearchExplorerPage\.tsx|research_catalog|futures_basis|backtesting/.test(id)))
  evidence.dependencyGraph = graph
  pass('Shared Reader/validator/static controller load without Auth, HTTP, Production controller or sibling features; test-only ChartView fixture is explicit')
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
  page.setDefaultTimeout(15000)
  page.on('pageerror', error => evidence.errors.push(String(error)))
  page.on('requestfailed', request => evidence.errors.push(`Request failed: ${request.url()}`))
  page.on('console', message => { if (message.type() === 'error') evidence.errors.push(message.text()) })
  page.on('response', response => { if (response.status() >= 400) evidence.errors.push(`HTTP ${response.status()}: ${response.url()}`) })

  await page.goto(base)
  await page.getByRole('heading', { name: '研究结果浏览', exact: true }).waitFor()
  await page.getByText(disclosure, { exact: true }).waitFor()
  await page.getByText('pub-static-one', { exact: true }).waitFor()
  assert.equal(await page.getByText('嵌入示例 · 发布状态：success', { exact: true }).count(), 1)
  assert.equal(await page.getByText('当前第 1 页', { exact: true }).count(), 1)
  assert.equal(await page.getByRole('button', { name: '上一页', exact: true }).isDisabled(), true)
  assert.equal(await page.getByRole('button', { name: '下一页', exact: true }).isDisabled(), true)
  assert.equal(await page.getByRole('button', { name: '刷新', exact: true }).count(), 0)
  pass('Embedded Publication list, origin disclosure, page controls and no online Refresh')

  await page.getByRole('button', { name: /^选\s*择$/ }).click()
  await page.getByText('声明的 Research scope', { exact: true }).waitFor()
  await page.getByText('Jobs 与 Analysis', { exact: true }).waitFor()
  assert.equal(await page.getByText('Job 1 — Success', { exact: true }).count(), 1)
  assert.equal(await page.getByText('Job 2 — Success', { exact: true }).count(), 1)
  await page.getByRole('button', { name: 'Publication 来源证据', exact: true }).click()
  await page.getByText('a'.repeat(64), { exact: true }).waitFor()
  await page.getByText(/以上为嵌入示例的 Provenance/).waitFor()
  pass('Manifest scope, published Jobs, source metadata and explicit static provenance disclosure')

  const interval = page.locator('.ant-list-item').filter({ hasText: 'interval-request' }).first()
  await interval.getByRole('button', { name: '选择 Analysis', exact: true }).click()
  await page.getByText('Bin 1', { exact: true }).waitFor()
  await page.getByText('观察总体与覆盖（原始比例）', { exact: true }).waitFor()
  await page.getByRole('button', { name: '展开覆盖与来源证据', exact: true }).click()
  await page.getByText('test-only-input-fingerprint', { exact: true }).waitFor()
  await page.getByRole('button', { name: 'count', exact: true }).click()
  await page.locator('.js-plotly-plot').waitFor()
  await page.getByText('View ID: count-id', { exact: true }).waitFor()
  assert.deepEqual(await page.locator('.js-plotly-plot').evaluate(plot => Array.from(plot.data[0].y)), [1, 1, 1, 1])
  await page.getByRole('button', { name: 'frequency', exact: true }).click()
  await page.getByText('View ID: frequency-id', { exact: true }).waitFor()
  await page.waitForFunction(() => {
    const plot = document.querySelector('.js-plotly-plot')
    return plot && plot.data?.[0]?.y?.[0] === 0.25
  })
  assert.deepEqual(await page.locator('.js-plotly-plot').evaluate(plot => Array.from(plot.data[0].y)), [0.25, 0.25, 0.25, 0.25])
  pass('IntervalCount result, coverage/provenance, published count and frequency View identities and real Plotly rendering')

  const quantile = page.locator('.ant-list-item').filter({ hasText: 'quantile-request' }).first()
  await quantile.getByRole('button', { name: '选择 Analysis', exact: true }).click()
  await page.getByText('325.0%', { exact: true }).waitFor()
  assert.equal(await page.getByText('View ID: frequency-id', { exact: true }).count(), 0)
  assert.equal(await page.locator('.js-plotly-plot').count(), 0)
  await page.getByRole('button', { name: 'quantile', exact: true }).click()
  await page.getByText('View ID: quantile-id', { exact: true }).waitFor()
  await page.locator('.js-plotly-plot').waitFor()
  assert.deepEqual(await page.locator('.js-plotly-plot').evaluate(plot => Array.from(plot.data[0].y)), [-1, 0, 3.25])
  pass('Quantile semantics and selection reset: changing Analysis removes the prior View before the new published View loads')

  await page.goto(`${base}?empty=1`)
  await page.getByText('当前静态示例未嵌入 Publication；不代表在线 Publication Store 为空。', { exact: true }).waitFor()
  assert.equal(await page.getByRole('button', { name: /^选\s*择$/ }).count(), 0)
  assert.equal(await page.getByRole('button', { name: '刷新', exact: true }).count(), 0)
  pass('Explicit static empty state without claiming an online Store result or retry')

  for (const width of [1440, 1024]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto(base)
    await page.getByText('pub-static-one', { exact: true }).waitFor()
    await page.screenshot({ path: resolve(output, `presentation-${width}.png`), fullPage: true })
  }
  await page.reload()
  await page.getByText('pub-static-one', { exact: true }).waitFor()
  await page.waitForLoadState('networkidle')
  assert.deepEqual(await context.cookies(), [])
  assert.equal(evidence.requests.some(request => /\/api\/|\/auth\/|research\/publications/.test(new URL(request.url).pathname)), false)
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
  console.log(`Static Research Explorer: ${evidence.status}; artifacts: ${output}`)
  if (evidence.status !== 'PASS') console.error(evidence.errors)
}
