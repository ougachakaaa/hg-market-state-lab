// D2-F verification only: built artifact served as files; no backend, proxy or Auth.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { createServer } from 'node:http'
import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const web = fileURLToPath(new URL('../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'd2f-backtesting-'))
const prefix = '/hg-market-state-lab/'
const disclosure = 'Test-only 静态测试数据 · 非正式 D3 Backtesting Example · 复用既有生产者 Test Fixture（2025-02-17 至 2025-03-25，5 个 CFFEX 交易日）· 非真实市场业绩 · 非 2026 目标窗口 · 未创建服务器 Run · 未执行 Preflight 或 W2 回测。'
const fixture = JSON.parse(await readFile(resolve(web, 'src/features/backtesting/api/result.fixture.json'), 'utf8'))
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let server; let browser; let page
const pass = message => { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  const built = spawnSync('npm', ['run', 'test:backtesting-static'], { cwd: web, encoding: 'utf8', shell: process.platform === 'win32' })
  assert.equal(built.status, 0, built.stdout + built.stderr)
  const artifact = resolve(web, 'dist-backtesting-test')
  const graph = JSON.parse(await readFile(resolve(artifact, 'presentation-dependencies.json'), 'utf8'))
  for (const module of [
    'src/features/backtesting/page/BacktestingPresentation.tsx',
    'src/features/backtesting/components/Result.tsx',
    'src/features/backtesting/api/validateResult.ts',
    'src/features/backtesting/static/useStaticBacktesting.ts',
    'src/features/backtesting/testing/backtestingFixture.ts',
  ]) assert.ok(graph.includes(module), `dependency graph must include ${module}`)
  assert.ok(!graph.some(id => /shared\/http|app\/auth|api\/backtesting\.ts|hooks\/useBacktesting\.ts|hooks\/usePreflight\.ts|page\/BacktestingPage\.tsx|demo\/futures_basis\/main\.tsx|futures_basis_research|research_explorer|mo_option/.test(id)))
  evidence.dependencyGraph = graph
  pass('Shared page/Result/validator/static controller load without Auth, HTTP, Production Run hooks, Preflight or sibling features')

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
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
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

  await page.goto(base)
  await page.getByRole('heading', { name: '期货展期做多回测', exact: true }).waitFor()
  await page.getByText(disclosure, { exact: true }).waitFor()
  assert.equal(await page.getByText(disclosure, { exact: true }).count(), 1)
  await page.getByText('固定回测参数', { exact: true }).waitFor()
  await page.getByText('Example 参数固定，不可编辑、不可提交；本页不会创建服务器 Run，也不会执行 Preflight。', { exact: true }).waitFor()
  await page.getByText('IM', { exact: true }).first().waitFor()
  await page.getByText('expiry_to_M1_v1', { exact: true }).first().waitFor()
  await page.getByText('futures_roll_long_v1', { exact: true }).first().waitFor()
  assert.equal(await page.locator('form').count(), 0)
  assert.equal(await page.locator('input, textarea, select, [role="combobox"]').count(), 0)
  assert.equal(await page.getByRole('button', { name: '开始回测' }).count(), 0)
  assert.equal(await page.getByRole('button', { name: '重新检查数据' }).count(), 0)
  pass('Shared static page renders a fixed, non-editable and non-submittable request with no Query/Preflight controls')

  await page.getByText('请求窗口与实际观测', { exact: true }).waitFor()
  await page.getByText('2025-02-17 至 2025-03-25', { exact: true }).first().waitFor()
  await page.getByText('2025-02-17 至 2025-03-25（5 个 CFFEX 交易日）', { exact: true }).waitFor()
  await page.getByText('futures_roll_long_result_v1', { exact: true }).waitFor()
  await page.getByText('futures_roll_long_definition_v1', { exact: true }).waitFor()
  await page.getByText('Embedded Backtest Result 已通过正式契约校验', { exact: true }).waitFor()
  await page.getByText(/不代表浏览器运行过 W2 Backtest Core/).first().waitFor()
  pass('Fixed request, Result Profile, Definition Version, requested-vs-observed window and static validation meaning are explicit')

  await page.getByText('回测结果 · Result Summary', { exact: true }).waitFor()
  await page.getByText('¥22,000.00', { exact: true }).waitFor()
  await page.getByText('1.8%', { exact: true }).first().waitFor()
  await page.getByText('Benchmark Return', { exact: true }).waitFor()
  await page.getByText('Excess Return', { exact: true }).waitFor()
  await page.getByText('Execution Count', { exact: true }).waitFor()
  await page.getByText('Roll Count', { exact: true }).waitFor()
  assert.equal(await page.getByTestId('backtest-result').count(), 1)
  pass('Result Summary keeps producer Gross/Benchmark/Excess Return, PnL, drawdowns, execution/roll counts and initial notional')

  const plots = page.locator('.js-plotly-plot')
  assert.equal(await plots.count(), 2)
  await plots.first().locator('.nsewdrag').waitFor()
  const chart = await plots.first().evaluate(el => ({
    ys: el.data.filter(t => t.type === 'scatter' && t.showlegend !== false).map(t => t.y),
    events: el.layout.shapes.length,
    tickformat: el.layout.yaxis.tickformat,
    title: el.layout.title.text,
    layers: el.data.filter(t => t.type === 'scatter' && t.showlegend !== false).length,
  }))
  assert.equal(chart.events, fixture.views.returns.events.length)
  assert.equal(chart.tickformat, '.1%')
  assert.equal(chart.title, 'Cumulative returns')
  assert.equal(chart.layers, fixture.views.returns.layers.length)
  assert.ok(chart.ys.some(ys => JSON.stringify(ys) === JSON.stringify(fixture.views.returns.layers[0].layer.data.map(m => m.y))))
  const drawdown = await plots.nth(1).evaluate(el => ({ title: el.layout.title.text, layers: el.data.filter(t => t.type === 'scatter' && t.showlegend !== false).length }))
  assert.equal(drawdown.title, 'Drawdown')
  assert.equal(drawdown.layers, fixture.views.drawdown.layers.length)
  pass('Both published V2 Views render through the shared ChartView with producer coordinates, events and percent axes')

  await plots.first().scrollIntoViewIfNeeded()
  const initialRange = await plots.first().evaluate(el => el._fullLayout.xaxis.range.map(String))
  const box = await plots.first().boundingBox()
  assert.ok(box)
  await page.mouse.move(box.x + box.width * 0.3, box.y + box.height * 0.5)
  await page.mouse.down()
  await page.mouse.move(box.x + box.width * 0.7, box.y + box.height * 0.5, { steps: 8 })
  await page.mouse.up()
  await page.waitForFunction(before => {
    const plot = document.querySelector('.js-plotly-plot')
    const range = plot?._fullLayout?.xaxis?.range
    return range && (String(range[0]) !== before[0] || String(range[1]) !== before[1])
  }, initialRange)
  await page.locator('.modebar-btn[data-title="Reset axes"]').first().click()
  await page.waitForFunction(before => {
    const plot = document.querySelector('.js-plotly-plot')
    const range = plot?._fullLayout?.xaxis?.range
    return range && String(range[0]) === before[0] && String(range[1]) === before[1]
  }, initialRange)
  await page.locator('.modebar-btn[data-title="Pan"]').first().click()
  await page.waitForFunction(() => document.querySelector('.js-plotly-plot')?._fullLayout?.dragmode === 'pan')
  pass('Real Chromium Plotly Zoom, Pan mode and Reset interactions operate on the embedded Views only')

  await page.getByRole('cell', { name: fixture.trades[0].contract_code, exact: true }).first().waitFor()
  assert.ok(await page.getByRole('cell', { name: fixture.trades[0].contract_code, exact: true }).count() > 0)
  await page.getByRole('cell', { name: fixture.rolls[0].new_contract_code, exact: true }).first().waitFor()
  assert.ok(await page.getByRole('cell', { name: fixture.rolls[0].new_contract_code, exact: true }).count() > 0)
  assert.ok(await page.getByRole('cell', { name: fixture.rolls[0].old_contract_code, exact: true }).count() > 0)
  pass('Trades and Rolls tables preserve complete producer rows and published contract identities')

  await page.getByText('研究证据与限制 · Evidence / Limitations', { exact: true }).click()
  await page.getByText(fixture.evidence.input_fingerprint, { exact: true }).waitFor()
  await page.getByText(/Embedded Synthetic Example/).waitFor()
  await page.getByText(/未执行服务器回测/).waitFor()
  await page.getByText(/不包含手续费、滑点和保证金机制/).waitFor()
  await page.getByText(/Historical decision-time metadata and active-set availability are explicit assumptions/).first().waitFor()
  pass('Evidence/Limitations retain the producer payload and disclose the static Synthetic origin, ideal Close gross execution and no fee/slippage/margin')

  assert.equal(await page.getByText('当前 Run 状态', { exact: true }).count(), 0)
  assert.equal(await page.getByText(/Run ID/).count(), 0)
  assert.equal(await page.getByText(/PENDING|RUNNING|COMPLETED/).count(), 0)
  assert.equal(await page.getByRole('button', { name: /重新读取/ }).count(), 0)
  assert.equal(await page.getByText(/SUBMITTING/).count(), 0)
  pass('No fake Run phase, Run ID, polling control, Submit feedback or manual read retry is rendered')

  await page.goto(`${base}?invalid=result`)
  await page.getByText('静态回测结果未通过校验', { exact: true }).waitFor()
  await page.getByText(/已拒绝展示/).waitFor()
  assert.equal(await page.getByTestId('backtest-result').count(), 0)
  assert.equal(await page.locator('.js-plotly-plot').count(), 0)
  assert.equal(await page.getByText('固定回测参数', { exact: true }).count(), 0)
  assert.equal(await page.getByText('Embedded Backtest Result 已通过正式契约校验', { exact: true }).count(), 0)
  pass('A Result outside the formal published profile is rejected with an explicit static error and no Result region')

  await page.goto(`${base}?invalid=request`)
  await page.getByText('静态回测结果未通过校验', { exact: true }).waitFor()
  assert.equal(await page.getByTestId('backtest-result').count(), 0)
  assert.equal(await page.getByText('固定回测参数', { exact: true }).count(), 0)
  assert.equal(await page.getByText('Embedded Backtest Result 已通过正式契约校验', { exact: true }).count(), 0)
  pass('A fixed request that does not answer the embedded Result is rejected without rendering either identity')

  const productionRunId = 'a'.repeat(32)
  await page.goto(`${base}?run_id=${productionRunId}`)
  await page.getByTestId('backtest-result').waitFor()
  assert.equal(await page.getByText(/Run ID/).count(), 0)
  assert.equal(await page.getByText(productionRunId, { exact: true }).count(), 0)
  pass('A Production run_id input is ignored: no URL Run restore, read attempt or fabricated identity')

  await page.goto(base)
  await page.getByTestId('backtest-result').waitFor()
  for (const width of [1440, 1024]) {
    await page.setViewportSize({ width, height: 1000 })
    await page.locator('.js-plotly-plot').first().scrollIntoViewIfNeeded()
    await page.screenshot({ path: resolve(output, `presentation-${width}.png`), fullPage: true })
  }
  await page.waitForLoadState('networkidle')
  assert.deepEqual(await context.cookies(), [])
  assert.equal(evidence.requests.some(request => /\/api\/|\/auth\/|\/backtesting\/futures-roll/.test(new URL(request.url).pathname)), false)
  assert.equal(evidence.requests.some(request => request.method !== 'GET'), false)
  assert.deepEqual(evidence.errors, [])
  pass('Only static assets requested throughout; zero Auth/API/Preflight/Submit network activity, no cookies and no browser errors')
  evidence.status = 'PASS'
} catch (error) {
  evidence.status = 'FAIL'; evidence.errors.push(error.stack || String(error)); process.exitCode = 1
  if (page) await page.screenshot({ path: resolve(output, 'failure.png') }).catch(() => {})
} finally {
  if (browser) await browser.close()
  if (server) await new Promise(done => server.close(done))
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(evidence, null, 2))
  console.log(`Static Backtesting: ${evidence.status}; artifacts: ${output}`)
  if (evidence.status !== 'PASS') console.error(evidence.errors)
}
