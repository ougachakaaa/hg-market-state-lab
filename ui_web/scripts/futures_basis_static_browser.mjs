// D2-E verification only: built artifact served as files; no backend, proxy or Auth.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { createServer } from 'node:http'
import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const web = fileURLToPath(new URL('../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'd2e-futures-basis-'))
const prefix = '/hg-market-state-lab/'
const disclosure = '静态测试数据 · 非正式 D3 Research Example · 固定 2024 Synthetic Fixture 请求 · 未创建服务器 Run · 未执行 Preflight 或研究 · 不代表当前市场数据或在线服务状态。'
const fixture = JSON.parse(await readFile(resolve(web, 'src/demo/futures_basis/report.v1.json'), 'utf8'))
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let server; let browser; let page
const pass = message => { evidence.checks.push(message); console.log(`PASS: ${message}`) }
const hash = async () => page.evaluate(() => window.location.hash)
try {
  const built = spawnSync('npm', ['run', 'test:futures-basis-static'], { cwd: web, encoding: 'utf8', shell: process.platform === 'win32' })
  assert.equal(built.status, 0, built.stdout + built.stderr)
  const artifact = resolve(web, '.build/tests/futures-basis')
  const graph = JSON.parse(await readFile(resolve(artifact, 'presentation-dependencies.json'), 'utf8'))
  for (const module of [
    'src/features/futures_basis_research/page/FuturesBasisPresentation.tsx',
    'src/features/futures_basis_research/report/Report.tsx',
    'src/features/futures_basis_research/report/validate.ts',
    'src/features/futures_basis_research/api/validateResult.ts',
    'src/features/futures_basis_research/static/useStaticFuturesBasis.ts',
    'src/demo/shell/hashRoutes.ts',
    'src/demo/futures_basis/report.v1.json',
  ]) assert.ok(graph.includes(module), `dependency graph must include ${module}`)
  assert.ok(!graph.some(id => /shared\/http|app\/auth|api\/futuresBasis\.ts|hooks\/useFuturesBasis\.ts|hooks\/usePreflight\.ts|page\/FuturesBasisPage\.tsx|demo\/futures_basis\/main\.tsx|research_explorer|mo_option|backtesting/.test(id)))
  evidence.dependencyGraph = graph
  pass('Shared page/reader/validator/static controller load without Auth, HTTP, Production Run hooks, Preflight or sibling features')

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
  page.setDefaultTimeout(20000)
  page.on('pageerror', error => evidence.errors.push(String(error)))
  page.on('requestfailed', request => evidence.errors.push(`Request failed: ${request.url()}`))
  page.on('console', message => { if (message.type() === 'error') evidence.errors.push(message.text()) })
  page.on('response', response => { if (response.status() >= 400) evidence.errors.push(`HTTP ${response.status()}: ${response.url()}`) })

  await page.goto(`${base}#/research/futures-basis`)
  await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
  await page.getByText(disclosure, { exact: true }).waitFor()
  assert.equal(await page.getByText(disclosure, { exact: true }).count(), 1)
  await page.getByText('固定研究参数', { exact: true }).waitFor()
  await page.getByText('Example 参数固定，不可编辑、不可提交；本页不会创建服务器 Run。', { exact: true }).waitFor()
  await page.getByText('请求窗口与实际观测覆盖', { exact: true }).waitFor()
  await page.getByText('IM · 2024-09-02 至 2024-10-31', { exact: true }).waitFor()
  await page.getByText('44 个候选交易日；2024-09-02..2024-10-31', { exact: true }).waitFor()
  await page.getByText('complete / futures_basis_definition_v1', { exact: true }).waitFor()
  await page.getByText('futures_basis_report_evidence_v1', { exact: true }).waitFor()
  await page.getByText(fixture.report.fingerprint, { exact: true }).first().waitFor()
  assert.equal(await page.getByText(fixture.report.fingerprint, { exact: true }).count(), 2)
  await page.getByText(/请求窗口 ≠ 实际观测覆盖/).waitFor()
  await page.getByText('Embedded Report 已通过静态校验', { exact: true }).waitFor()
  assert.equal(await page.getByRole('button', { name: /生成研究/ }).count(), 0)
  assert.equal(await page.getByRole('button', { name: '重新检查输入', exact: true }).count(), 0)
  assert.equal(await page.getByText(/Run ID/).count(), 0)
  const sections = await page.locator('[id^="section-"]').count()
  assert.equal(sections, 6)
  for (let i = 0; i < 6; i++) assert.equal(await page.locator(`#section-${i}`).count(), 1)
  pass('Fixed request identity, requested-vs-observed coverage, explicit static disclosure, six shared sections and no Submit/Preflight/Run identity')

  const history = page.locator('#section-1 .js-plotly-plot')
  assert.equal(await history.count(), 3)
  await history.first().locator('.nsewdrag').waitFor()
  assert.equal(await history.first().locator('.legend .traces').count(), 4)
  await page.waitForFunction(() => document.querySelectorAll('#section-1 .js-plotly-plot')[0]?._fullLayout?.xaxis?.type === 'linear')
  await page.locator('#section-1').getByText('Calendar Days', { exact: true }).click()
  await page.waitForFunction(() => document.querySelectorAll('#section-1 .js-plotly-plot')[0]?._fullLayout?.xaxis?.type === 'date')
  await page.locator('#section-1').getByText('Trading Days', { exact: true }).click()
  await page.waitForFunction(() => document.querySelectorAll('#section-1 .js-plotly-plot')[0]?._fullLayout?.xaxis?.type === 'linear')
  pass('Shared six-section reader renders real producer Views with Plotly and the local Trading/Calendar control')

  const basisRatio = fixture.report.distributions.find(item => item.request.metric === 'basis_ratio' && item.request.slot === 'Q1')
  const expectedTitle = fixture.report.views.histograms[`${basisRatio.request.analysis_id}/count`].layout.title
  await page.getByRole('combobox', { name: 'Distribution metric', exact: true }).click()
  await page.getByTitle('basis_ratio', { exact: true }).click()
  await page.getByRole('combobox', { name: 'Distribution slot', exact: true }).click()
  await page.getByTitle('Q1', { exact: true }).click()
  await page.waitForFunction(title => document.querySelector('#section-2 .js-plotly-plot')?.layout?.title?.text === title, expectedTitle)
  await page.locator('#section-3 .ant-table-row-expand-icon').first().click()
  await page.locator('#section-3').getByText('共同日期', { exact: false }).first().waitFor()
  await page.locator('#section-2').scrollIntoViewIfNeeded()
  pass('Local Metric/Slot selection switches published Views and the comparison table without any request')

  const nav = page.getByRole('navigation', { name: '报告章节' })
  assert.equal(await nav.getByRole('button').count(), 6)
  assert.equal(await nav.locator('a').count(), 0)
  const historyLength = await page.evaluate(() => history.length)
  for (let i = 0; i < 6; i++) {
    await nav.getByRole('button').nth(i).click()
    await page.locator(`#section-${i}`).getByRole('heading').first().waitFor({ state: 'visible' })
    assert.equal(await hash(), '#/research/futures-basis')
  }
  assert.equal(await page.evaluate(() => history.length), historyLength)
  await nav.getByRole('button').nth(5).focus()
  assert.equal(await page.evaluate(() => document.activeElement?.textContent?.includes('证据与限制')), true)
  await page.keyboard.press('Enter')
  assert.equal(await hash(), '#/research/futures-basis')
  assert.ok(await page.evaluate(() => window.scrollY) > 0)
  pass('Hash Router coexists with section navigation: six local section controls, keyboard activation, no fragment replacement and no history entries')

  await page.getByRole('button', { name: '导航到研究总览（路由验证）', exact: true }).click()
  await page.getByTestId('static-route').waitFor()
  assert.equal((await page.getByTestId('static-route').textContent()), '/research')
  assert.equal(await hash(), '#/research')
  await page.goBack()
  await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
  assert.equal(await page.locator('[id^="section-"]').count(), 6)
  assert.equal(await hash(), '#/research/futures-basis')
  await page.goForward()
  await page.getByTestId('static-route').waitFor()
  assert.equal(await hash(), '#/research')
  await page.goBack()
  await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
  await page.reload()
  await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
  assert.equal(await hash(), '#/research/futures-basis')
  assert.equal(await page.locator('#section-1 .js-plotly-plot').count(), 3)
  pass('Browser Back/Forward and reload keep the static Research route and the embedded report')

  const runId = 'a'.repeat(32)
  await page.goto(`${base}?run_id=${runId}#/research/futures-basis`)
  await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
  assert.equal(await page.getByText(/Run ID/).count(), 0)
  assert.equal(await page.getByRole('button', { name: /重新读取/ }).count(), 0)
  pass('Production run_id input is ignored: no Run restore, no fake Run identity and no read attempt')

  await page.goto(`${base}?invalid=1#/research/futures-basis`)
  await page.getByText('静态研究报告未通过校验', { exact: true }).waitFor()
  assert.equal(await page.locator('[id^="section-"]').count(), 0)
  assert.equal(await page.locator('.js-plotly-plot').count(), 0)
  assert.equal(await page.getByText('Embedded Report 已通过静态校验', { exact: true }).count(), 0)
  assert.equal(await page.getByText('固定研究参数', { exact: true }).count(), 0)
  pass('A mismatched fixed request rejects the embedded set with an explicit static error and no report')

  for (const width of [1440, 1024]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto(`${base}#/research/futures-basis`)
    await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
    await page.locator('#section-1 .js-plotly-plot').first().scrollIntoViewIfNeeded()
    await page.screenshot({ path: resolve(output, `presentation-${width}.png`), fullPage: true })
  }
  await page.waitForLoadState('networkidle')
  assert.deepEqual(await context.cookies(), [])
  assert.equal(evidence.requests.some(request => /\/api\/|\/auth\/|\/research\/futures-basis\/runs/.test(new URL(request.url).pathname)), false)
  assert.deepEqual(evidence.errors, [])
  pass('Only static assets requested throughout; zero Auth/API/Preflight/Run network activity and no browser errors')
  evidence.status = 'PASS'
} catch (error) {
  evidence.status = 'FAIL'; evidence.errors.push(error.stack || String(error)); process.exitCode = 1
  if (page) await page.screenshot({ path: resolve(output, 'failure.png') }).catch(() => {})
} finally {
  if (browser) await browser.close()
  if (server) await new Promise(done => server.close(done))
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(evidence, null, 2))
  console.log(`Static Futures Basis: ${evidence.status}; artifacts: ${output}`)
  if (evidence.status !== 'PASS') console.error(evidence.errors)
}
