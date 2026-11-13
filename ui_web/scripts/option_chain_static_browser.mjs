// D2-A verification only: built artifact served as files; no backend or dev proxy.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { createServer } from 'node:http'
import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const web = fileURLToPath(new URL('../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'd2a-option-chain-'))
const prefix = '/hg-market-state-lab/'
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let server; let browser; let page
const pass = message => { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  const built = spawnSync('npm', ['run', 'test:option-chain-static'], { cwd: web, encoding: 'utf8', shell: process.platform === 'win32' })
  assert.equal(built.status, 0, built.stdout + built.stderr)
  const artifact = resolve(web, 'dist-option-chain-test')
  const graph = JSON.parse(await readFile(resolve(artifact, 'presentation-dependencies.json'), 'utf8'))
  assert.ok(graph.includes('src/features/mo_option_chain/page/OptionChainPresentation.tsx'))
  assert.ok(graph.includes('src/features/mo_option_chain/api/validateOptionChain.ts'))
  assert.ok(!graph.some(id => /shared\/http|app\/auth|api\/moOptionChain\.ts|hooks\/useOptionChain\.ts|page\/OptionChainPage\.tsx/.test(id)))
  evidence.dependencyGraph = graph
  pass('Shared presentation and validator load without HTTP/Auth/production controller')
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
  await context.grantPermissions(['clipboard-read', 'clipboard-write'])
  await page.goto(base)
  await page.getByRole('region', { name: '期权链结果' }).waitFor()
  assert.equal(await page.getByLabel('观察日期').isDisabled(), true)
  await page.getByRole('form', { name: '期权链查询' }).evaluate(form => form.requestSubmit())
  assert.match(await page.getByRole('note').textContent(), /静态测试数据/)
  await page.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
  await page.getByText('Copied', { exact: true }).waitFor()
  const raw = await page.evaluate(() => navigator.clipboard.readText())
  const payload = JSON.parse(raw)
  assert.equal(payload.expiries.length, 3)
  assert.equal(payload.expiries[0].puts[0].price, 0)
  assert.equal(payload.expiries[0].puts[1].price, null)
  assert.equal(payload.expiries[2].futures, null)
  await page.getByRole('checkbox', { name: '2026-10-23' }).uncheck()
  await page.getByRole('checkbox', { name: '2026-11-27' }).uncheck()
  assert.equal(await page.getByRole('checkbox', { name: '2026-09-25' }).isDisabled(), true)
  await page.getByRole('button', { name: '扩大行权价视窗' }).click()
  await page.getByText('行权价视窗：±400 点', { exact: true }).waitFor()
  await page.getByText('高级设置 · 图表颜色', { exact: true }).click()
  await page.getByRole('button', { name: 'Call 颜色' }).click()
  const color = page.locator('.ant-color-picker-hex-input input')
  await color.fill('e11d48'); await color.press('Enter')
  await page.getByRole('button', { name: 'Call 颜色' }).click()
  assert.match(await page.getByRole('button', { name: 'Call 颜色' }).textContent(), /#e11d48/)
  await page.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
  assert.equal(await page.evaluate(() => navigator.clipboard.readText()), raw)
  await page.getByRole('button', { name: 'Copy Context JSON', exact: true }).click()
  await page.waitForFunction(() => navigator.clipboard.readText().then(text => text.includes('daily-data-context-v1')))
  const contextText = await page.evaluate(() => navigator.clipboard.readText())
  const envelope = JSON.parse(contextText)
  assert.deepEqual(envelope.data, payload)
  assert.deepEqual(Object.keys(envelope).sort(), ['data', 'format_version', 'metadata'])
  const download = async name => {
    const pending = page.waitForEvent('download')
    await page.getByRole('button', { name, exact: true }).click()
    const file = await pending
    return { filename: file.suggestedFilename(), bytes: await readFile(await file.path()) }
  }
  const csv = await download('Export CSV')
  assert.equal(csv.filename, 'mo-option-chain_2026-09-17_close.csv')
  assert.deepEqual([...csv.bytes.subarray(0, 3)], [239, 187, 191])
  const rows = csv.bytes.toString('utf8').replace(/^\uFEFF/, '').trimEnd().split('\r\n')
  assert.equal(rows.length, 1 + payload.expiries.reduce((sum, group) => sum + group.calls.length + group.puts.length, 0))
  assert.ok(rows.some(row => row.includes('A-out,8000,2000')))
  assert.ok(rows.some(row => row.includes('A-null,7300,null')))
  assert.ok(rows.some(row => row.includes('A-zero,7100,0')))
  const exported = await download('Export Context JSON')
  // Windows clipboard text uses CRLF while the downloaded UTF-8 file preserves LF.
  assert.equal(exported.bytes.toString('utf8').replaceAll('\r\n', '\n'), contextText.replaceAll('\r\n', '\n'))
  pass('Fixed query; expiry, last-selection guard, colors, viewport; full Raw/Context JSON and CSV retain hidden/outside/null/zero data')
  await page.locator('.js-plotly-plot').waitFor()
  // Production deliberately fixes both axes and hides the modebar. Preserve that
  // behavior; hover and the feature-owned viewport are its Plotly interactions.
  await page.locator('.scatterlayer .trace .point').first().hover({ force: true })
  await page.locator('.hoverlayer').getByText(/A-call/).waitFor()
  const plot = await page.locator('.js-plotly-plot').evaluate(plot => ({
    fixedX: plot._fullLayout.xaxis.fixedrange, fixedY: plot._fullLayout.yaxis.fixedrange,
    dragmode: plot._fullLayout.dragmode, modebar: plot._context.displayModeBar,
  }))
  assert.deepEqual(plot, { fixedX: true, fixedY: true, dragmode: false, modebar: false })
  pass('Real Plotly hover works; production fixed-axis and disabled modebar behavior retained')
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 })
    await page.screenshot({ path: resolve(output, `presentation-${width}.png`), fullPage: true })
  }
  await page.reload()
  await page.getByRole('region', { name: '期权链结果' }).waitFor()
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
  console.log(`Static Option Chain: ${evidence.status}; artifacts: ${output}`)
  if (evidence.status !== 'PASS') console.error(evidence.errors)
}
