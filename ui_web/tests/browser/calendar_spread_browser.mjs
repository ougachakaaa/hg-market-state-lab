// WP6: real Chromium/Vite/composed Auth + HTTP; synthetic public Research services.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdtemp, mkdir, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'
import { onlineHarness, unusedPort } from './online_harness.mjs'
const root = fileURLToPath(new URL('../../../', import.meta.url))
const temporary = await mkdtemp(resolve(tmpdir(), 'calendar-spread-wp6-'))
const output = resolve(root, 'ui_web/.build/calendar-spread-acceptance')
const backendPort = await unusedPort(), frontendPort = await unusedPort()
const origin = `http://127.0.0.1:${frontendPort}`
const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http', LAB_AUTH_ORIGIN: origin,
  LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'), LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'),
  LAB_BROWSER_API_ORIGIN: `http://127.0.0.1:${backendPort}` }
const harness = onlineHarness(env, root, output)
const requests = [], errors = [], evidence = []
let browser
function cli(...args) {
  const r = spawnSync('poetry', ['run', 'lab', 'auth', ...args], { cwd: root, env, encoding: 'utf8' })
  assert.equal(r.status, 0, r.stderr); return r.stdout
}
try {
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  const backend = harness.start('poetry', ['run', 'python', '-m', 'uvicorn', '--app-dir', 'ui_web/tests/fixtures', 'calendar_spread_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', String(backendPort), '--no-proxy-headers'])
  const frontend = harness.start(process.execPath, ['node_modules/vite/bin/vite.js', '--config', 'tests/config/vite.browser.config.ts', '--strictPort', '--port', String(frontendPort)], resolve(root, 'ui_web'))
  await harness.ready(`${env.LAB_BROWSER_API_ORIGIN}/auth/me`, backend, 401)
  await harness.ready(origin, frontend, 200)
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
  const page = await context.newPage(); page.setDefaultTimeout(20000)
  page.on('pageerror', e => errors.push(String(e)))
  page.on('request', r => { if (new URL(r.url()).pathname.startsWith('/api/')) requests.push(`${r.method()} ${new URL(r.url()).pathname}`) })
  for (const path of ['/data/futures-calendar-spread', '/research/calendar-spread-relative-value']) {
    const html = await context.request.get(origin + path)
    assert.equal(html.status(), 200); assert.match(html.headers()['content-type'], /text\/html/)
  }
  assert.equal((await context.request.get(`${origin}/api/data/futures-calendar-spread?product_code=IM&trade_date=2024-10-18`)).status(), 401)
  await page.goto(`${origin}/data/futures-calendar-spread`)
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  const password = randomBytes(24).toString('base64url')
  assert.equal((await context.request.post(`${origin}/auth/register`, { headers: { Origin: origin }, data: { username: 'wp6_browser', password } })).status(), 202)
  const id = cli('pending').match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i)?.[0]; assert.ok(id); cli('approve', id)
  await page.getByLabel('用户名', { exact: true }).fill('wp6_browser')
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await page.getByRole('heading', { name: 'Futures Calendar Spread', exact: true }).waitFor()
  assert.equal(new URL(page.url()).pathname, '/data/futures-calendar-spread')
  async function product() { await page.getByRole('combobox', { name: 'Product', exact: true }).click(); await page.locator('.ant-select-item-option[title="IM"]').click() }
  async function date(label, value) { const input = page.getByRole('textbox', { name: label, exact: true }); await input.fill(value); await input.press('Enter'); await input.press('Tab') }
  await product(); await date('Trade Date', '2024-10-18'); assert.equal(requests.length, 0)
  const dailyResponse = page.waitForResponse(r => r.url().includes('/api/data/futures-calendar-spread'))
  await page.getByRole('button', { name: '查询', exact: true }).click()
  const dr = await dailyResponse; assert.equal(dr.status(), 200); assert.equal((await dr.json()).day.observations.length, 6)
  await page.getByText('已查询数据', { exact: true }).waitFor()
  await page.reload(); await page.getByRole('heading', { name: 'Futures Calendar Spread', exact: true }).waitFor()
  assert.equal(requests.length, 1, 'reload mounts idle query controls')
  await page.goto(`${origin}/research/calendar-spread-relative-value`)
  await page.getByRole('heading', { name: 'Calendar Spread Historical Relative Value', exact: true }).waitFor()
  await product(); await date('History Start', '2024-09-06'); await date('Evaluation Date', '2024-10-18')
  await page.getByLabel('Histogram Edges', { exact: true }).fill('[-0.1,0,0.1]')
  const historyResponse = page.waitForResponse(r => r.url().includes('/api/research/calendar-spread-relative-value/query'))
  await page.getByRole('button', { name: '开始研究', exact: true }).click()
  const hr = await historyResponse; assert.equal(hr.status(), 200); const history = await hr.json()
  const plot = page.locator('.js-plotly-plot').first()
  await plot.waitFor(); await page.waitForFunction(() => document.querySelector('.js-plotly-plot')?._fullLayout?.xaxis.type === 'linear')
  const domain = [...history.historical_days.filter(d => d.status === 'open').map(d => d.trade_date), history.current_day.trade_date]
  async function snapshot() { return plot.evaluate(el => ({ type: el._fullLayout.xaxis.type, x: el.data.map(t => t.x), y: el.data.map(t => t.y), range: Array.from(el._fullLayout.xaxis.range), visible: el.data.map(t => t.visible) })) }
  const trading = await snapshot()
  assert.deepEqual(trading.x[0], history.pairs[0].samples.map(s => domain.indexOf(s.trade_date)))
  assert.deepEqual(trading.y[0], history.pairs[0].samples.map(s => s.metric.value))
  const count = requests.length
  await page.getByText('Calendar Days', { exact: true }).click()
  await page.waitForFunction(() => document.querySelector('.js-plotly-plot')._fullLayout.xaxis.type === 'date')
  const calendar = await snapshot(); assert.deepEqual(calendar.x[0], history.pairs[0].samples.map(s => s.trade_date)); assert.deepEqual(calendar.y, trading.y)
  async function settle() {
    await plot.scrollIntoViewIfNeeded()
    await plot.locator('.nsewdrag').evaluate(el => new Promise(done => {
      let last = '', stable = 0
      function frame() { const b = el.getBoundingClientRect(), key = `${b.x},${b.y},${scrollY}`; stable = key === last ? stable + 1 : 0; last = key; if (stable >= 8) done(); else requestAnimationFrame(frame) }
      frame()
    }))
  }
  async function drag(a, b) { await settle(); const box = await plot.locator('.nsewdrag').boundingBox(); await page.mouse.move(box.x + box.width * a, box.y + box.height * .5); await page.mouse.down(); await page.mouse.move(box.x + box.width * b, box.y + box.height * .5, { steps: 12 }); await page.mouse.up() }
  for (const mode of ['calendar', 'trading']) {
    if (mode === 'trading') { await page.getByText('Trading Days', { exact: true }).click(); await page.waitForFunction(() => document.querySelector('.js-plotly-plot')._fullLayout.xaxis.type === 'linear') }
    const initial = (await snapshot()).range
    await settle(); await plot.locator('[data-title="Zoom"]').click(); await drag(.2,.7)
    await page.waitForFunction(old => JSON.stringify(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range) !== JSON.stringify(old), initial)
    const zoomed = (await snapshot()).range
    await plot.locator('[data-title="Pan"]').click(); await drag(.5,.6)
    await page.waitForFunction(old => JSON.stringify(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range) !== JSON.stringify(old), zoomed)
    await plot.locator('[data-title="Reset axes"]').click()
    await page.waitForFunction(old => JSON.stringify(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range) === JSON.stringify(old), initial)
  }
  await plot.locator('.scatterlayer .trace .point').first().hover({ force: true })
  await page.waitForFunction(() => /IM24/.test(document.querySelector('.js-plotly-plot .hoverlayer')?.textContent ?? ''))
  const hover = await plot.locator('.hoverlayer').textContent(); assert.match(hover, /2024-/); assert.match(hover, /Raw value/)
  await plot.locator('.legend .legendtoggle').first().click()
  await page.waitForFunction(() => document.querySelector('.js-plotly-plot').data[0].visible === 'legendonly')
  await page.getByText('Calendar Days', { exact: true }).click()
  await page.waitForFunction(() => document.querySelector('.js-plotly-plot')._fullLayout.xaxis.type === 'date')
  assert.equal((await snapshot()).visible[0], 'legendonly')
  await page.getByRole('combobox', { name: 'Pair', exact: true }).click()
  await page.locator('.ant-select-item-option[title="Q1/Q2"]').click()
  assert.equal(requests.length, count, 'local Pair/axis/viewport interactions do not query')
  await page.getByLabel('Histogram Edges', { exact: true }).fill('[-1,0,1]')
  await page.getByText(/参数已修改/).waitFor(); assert.equal(requests.length, count)
  await mkdir(output, { recursive: true }); await page.screenshot({ path: resolve(output, 'research.png'), fullPage: true })
  await page.reload(); await page.getByRole('heading', { name: 'Calendar Spread Historical Relative Value', exact: true }).waitFor(); assert.equal(requests.length, count)
  await page.goBack(); await page.getByRole('heading', { name: 'Futures Calendar Spread', exact: true }).waitFor()
  await page.goForward(); await page.getByRole('heading', { name: 'Calendar Spread Historical Relative Value', exact: true }).waitFor()
  await page.getByRole('button', { name: '退出登录', exact: true }).click(); await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  assert.deepEqual(errors, [])
  evidence.push('PASS: composed Auth, Daily /api/data and Research /api/research rewrites, SPA deep reload/history, explicit submit, Pair/axis local-only, exact dates/values/contracts, hover, Zoom/Pan/Reset both modes, legend retention, logout')
  console.log(evidence[0])
} finally {
  await harness.save(evidence, errors)
  await browser?.close(); await harness.stop()
  await rm(temporary, { recursive: true, force: true })
}
