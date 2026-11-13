// D2-B verification only: built artifact served as files; no backend or dev proxy.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { createServer } from 'node:http'
import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const web = fileURLToPath(new URL('../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'd2b-premium-'))
const prefix = '/hg-market-state-lab/'
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let server; let browser; let page
const pass = message => { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  const built = spawnSync('npm', ['run', 'test:premium-static'], { cwd: web, encoding: 'utf8', shell: process.platform === 'win32' })
  assert.equal(built.status, 0, built.stdout + built.stderr)
  const artifact = resolve(web, 'dist-premium-test')
  const graph = JSON.parse(await readFile(resolve(artifact, 'presentation-dependencies.json'), 'utf8'))
  assert.ok(graph.includes('src/features/mo_option_premium/page/PremiumPlanePresentation.tsx'))
  assert.ok(graph.includes('src/features/mo_option_premium/api/validatePremiumPlane.ts'))
  assert.ok(!graph.some(id => /shared\/http|app\/auth|api\/moOptionPremium\.ts|hooks\/usePremiumPlane\.ts|page\/PremiumPlanePage\.tsx/.test(id)))
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
  await page.getByRole('region', { name: 'Premium plane results' }).waitFor()
  assert.equal(await page.getByLabel('观察日期').isDisabled(), true)
  assert.equal(await page.getByRole('combobox', { name: '价格口径' }).isDisabled(), true)
  assert.equal(await page.getByLabel('观察日期').inputValue(), '2026-09-21')
  assert.match(await page.getByRole('form', { name: '权利金平面查询' }).textContent(), /MO · close/)
  await page.getByRole('form', { name: '权利金平面查询' }).evaluate(form => form.requestSubmit())
  for (const name of ['Call', 'Underlying spot', 'Total value', 'Annualized', 'Points']) {
    assert.equal(await page.getByRole('radio', { name, exact: true }).isChecked(), true)
  }
  assert.equal(await page.getByRole('cell', { name: '2026-09-25 no Point' }).textContent(), '')
  await page.getByText('0.0', { exact: true }).waitFor()
  await page.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
  await page.getByText('Copied', { exact: true }).waitFor()
  const raw = await page.evaluate(() => navigator.clipboard.readText())
  const payload = JSON.parse(raw)
  assert.equal(payload.points.length, 3)
  assert.equal(payload.points[0].premium, 0)
  assert.equal(payload.expiries[1].futures, null)
  const classes = await page.locator('.premium-table td').evaluateAll(cells => cells.map(cell => cell.className))
  await page.getByRole('radio', { name: 'Same-expiry futures' }).check()
  await page.getByRole('radio', { name: 'Time value' }).check()
  await page.getByRole('radio', { name: 'Unannualized' }).check()
  await page.getByRole('radio', { name: 'Yield' }).check()
  await page.getByText('-0.20%', { exact: true }).waitFor()
  assert.equal(await page.getByRole('cell', { name: '2026-10-23 metric unavailable' }).textContent(), '—')
  assert.deepEqual(await page.locator('.premium-table td').evaluateAll(cells => cells.map(cell => cell.className)), classes)
  await page.getByText('Put', { exact: true }).click()
  // Hiding the only expiry containing Put is a legal empty projection, not a failure.
  await page.getByRole('checkbox', { name: '2026-09-25' }).uncheck()
  await page.getByText('当前选择下无 analytical observation；可调整期权类型或显示到期日。', { exact: true }).waitFor()
  assert.equal(await page.getByRole('checkbox', { name: '2026-10-23' }).isDisabled(), true)
  await page.getByText('View embedded payload', { exact: true }).click()
  await page.getByText('Validated embedded Example payload', { exact: true }).waitFor()
  assert.equal(await page.getByText('Raw backend response', { exact: true }).count(), 0)
  assert.equal(await page.getByRole('note').count(), 2)
  assert.equal(await page.locator('.raw-response-code').textContent(), raw.replaceAll('\r\n', '\n'))
  await page.getByRole('button', { name: 'Copy JSON', exact: true }).click()
  await page.waitForFunction(raw => navigator.clipboard.readText().then(text => text === raw), raw)
  await page.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
  assert.equal(await page.evaluate(() => navigator.clipboard.readText()), raw)
  await page.getByRole('button', { name: 'Copy Context JSON', exact: true }).click()
  await page.waitForFunction(() => navigator.clipboard.readText().then(text => text.includes('daily-data-context-v1')))
  const contextText = await page.evaluate(() => navigator.clipboard.readText())
  const envelope = JSON.parse(contextText)
  assert.deepEqual(envelope.data, payload)
  assert.deepEqual(Object.keys(envelope).sort(), ['data', 'format_version', 'metadata'])
  assert.equal(envelope.metadata.product, 'MO Premium Plane')
  const download = async name => {
    const pending = page.waitForEvent('download')
    await page.getByRole('button', { name, exact: true }).click()
    const file = await pending
    return { filename: file.suggestedFilename(), bytes: await readFile(await file.path()) }
  }
  const csv = await download('Export CSV')
  assert.equal(csv.filename, 'mo-premium-plane_2026-09-21_close.csv')
  assert.deepEqual([...csv.bytes.subarray(0, 3)], [239, 187, 191])
  const rows = csv.bytes.toString('utf8').replace(/^\uFEFF/, '').trimEnd().split('\r\n').map(row => row.split(','))
  assert.equal(rows.length, payload.points.length + 1)
  assert.equal(rows[0].length, 31)
  for (const [index, point] of payload.points.entries()) {
    const expiry = payload.expiries.find(expiry => expiry.expiry_date === point.expiry_date)
    const metrics = ['underlying_spot', 'expiry_futures'].flatMap(reference => ['total', 'time_value'].flatMap(value =>
      ['unannualized', 'annualized'].flatMap(time => ['points', 'yield'].map(representation => point.metrics[reference][value][time][representation]))))
    const expected = [payload.observation.kind, payload.observation.value, payload.option_product, payload.price_type,
      payload.underlying.instrument_id, payload.underlying.price, point.expiry_date, expiry.dte,
      expiry.futures !== null, expiry.futures?.instrument_id ?? null, expiry.futures?.price ?? null,
      point.instrument_id, point.option_type, point.strike, point.premium, ...metrics].map(String)
    assert.deepEqual(rows[index + 1], expected)
  }
  const exported = await download('Export Context JSON')
  // Windows clipboard text uses CRLF while the downloaded UTF-8 file preserves LF.
  assert.equal(exported.bytes.toString('utf8').replaceAll('\r\n', '\n'), contextText.replaceAll('\r\n', '\n'))
  pass('Fixed query and Form submit; default/four-axis/side/expiry controls; sparse absent/null/zero and reference coloring; complete Inspector/Clipboard/31-column CSV/Context downloads')
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 })
    await page.screenshot({ path: resolve(output, `presentation-${width}.png`), fullPage: true })
  }
  await page.reload()
  await page.getByRole('region', { name: 'Premium plane results' }).waitFor()
  assert.equal(await page.getByRole('radio', { name: 'Call', exact: true }).isChecked(), true)
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
  console.log(`Static Premium Plane: ${evidence.status}; artifacts: ${output}`)
  if (evidence.status !== 'PASS') console.error(evidence.errors)
}
