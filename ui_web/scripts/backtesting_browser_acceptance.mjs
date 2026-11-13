// Real browser -> Vite proxy -> FastAPI -> temporary SQLite. Only market public
// providers are deterministic fixtures; Auth, Cookie and CLI are real.
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdtemp, rm, mkdir, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const root = fileURLToPath(new URL('../../', import.meta.url))
const temporary = await mkdtemp(resolve(tmpdir(), 'wp7-backtesting-'))
const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http',
  LAB_AUTH_ORIGIN: 'http://127.0.0.1:5173',
  LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'),
  LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'), LAB_BACKTESTING_RUN_ROOT: resolve(temporary, 'runs') }
const processes = []
let browser
let page
const evidence = []
const states = []
const errors = []
function start(command, args, cwd = root) {
  const child = spawn(command, args, { cwd, env, stdio: ['ignore', 'pipe', 'pipe'] })
  processes.push(child)
  let output = ''
  child.stdout.on('data', (chunk) => { output += chunk })
  child.stderr.on('data', (chunk) => { output += chunk })
  child.on('exit', (code) => { if (code) process.stderr.write(output) })
  return child
}
async function ready(url, child, expected) {
  for (let attempt = 0; attempt < 120; attempt++) {
    if (child.exitCode !== null) throw new Error(`Server exited: ${child.exitCode}`)
    try {
      const res = await fetch(url)
      if (res.status === expected) return
    } catch { /* starting */ }
    await new Promise((done) => setTimeout(done, 250))
  }
  throw new Error(`Timed out waiting for ${url}`)
}
function cli(...args) {
  const result = spawnSync('poetry', ['run', 'lab', 'auth', ...args], { cwd: root, env, encoding: 'utf8' })
  assert.equal(result.status, 0, result.stderr)
  return result.stdout
}
try {
  // Fail instead of attaching to an unrelated developer's running servers.
  const { createServer } = await import('node:net')
  for (const port of [8011, 5173]) {
    const server = createServer()
    await new Promise((done, reject) => server.once('error', reject).listen(port, '127.0.0.1', done))
    await new Promise((done) => server.close(done))
  }
  const backend = start('poetry', ['run', 'python', '-m', 'uvicorn', '--app-dir', 'ui_web/scripts',
    'backtesting_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', '8011', '--no-proxy-headers'])
  const frontend = start(process.execPath, ['node_modules/vite/bin/vite.js', '--strictPort'], resolve(root, 'ui_web'))
  await ready('http://127.0.0.1:8011/auth/me', backend, 401)
  await ready('http://127.0.0.1:5173/', frontend, 200)
  browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  const context = await browser.newContext()
  page = await context.newPage()
  page.setDefaultTimeout(15000)
  page.on('pageerror', error => errors.push(String(error)))
  page.on('response', async (res) => {
    const path = new URL(res.url()).pathname
    if (path.startsWith('/auth/') || path.startsWith('/api/backtesting/futures-roll')) evidence.push(`${path} ${res.status()}`)
    if (/\/runs\/[a-f0-9]+$/.test(path) && res.status() === 200) states.push((await res.json()).status)
  })
  const anonymous = await context.request.get('http://127.0.0.1:5173/mo-option-chain')
  assert.equal(anonymous.status(), 401)
  await page.goto('http://127.0.0.1:5173/')
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'MO Option Chain', exact: true }).count(), 0)
  assert.equal(evidence.some((entry) => entry.startsWith('/mo-option')), false)
  await page.getByRole('button', { name: '注册', exact: true }).click()
  await page.getByLabel('用户名', { exact: true }).fill('g3_browser_user')
  const password = randomBytes(24).toString('base64url')
  await page.getByLabel('密码', { exact: true }).fill(password)
  const registration = page.waitForResponse((res) => res.url().endsWith('/auth/register'))
  await page.getByRole('button', { name: '提交注册申请', exact: true }).click()
  const registered = await registration
  assert.equal(registered.status(), 202)
  assert.equal((await registered.allHeaders())['set-cookie'], undefined)
  await page.getByText('注册申请已提交，请等待管理员审批后登录。').waitFor()
  assert.equal((await context.cookies()).length, 0)
  const pending = cli('pending')
  assert.match(pending, /g3_browser_user/)
  const userId = pending.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i)?.[0]
  assert.ok(userId, 'CLI pending must expose an approval identity')
  cli('approve', userId)
  await page.getByRole('button', { name: '返回登录', exact: true }).click()
  await page.getByLabel('用户名', { exact: true }).fill('g3_browser_user')
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await page.getByRole('menuitem', { name: '研究总览', exact: true }).waitFor()
  const cookie = (await context.cookies()).find(value => value.name === 'lab_access_token')
  assert.ok(cookie?.httpOnly)
  assert.equal(cookie.sameSite, 'Strict')
  assert.equal(cookie.secure, false)
  assert.equal(await page.evaluate(() => document.cookie.includes('lab_access_token')), false)
  const output = resolve(process.argv[2] || '/tmp/wp7-backtesting-browser')
  await mkdir(output, { recursive: true })
  await page.getByRole('menuitem', { name: '回测', exact: true }).click()
  await page.getByRole('heading', { name: '期货展期做多回测', exact: true }).waitFor()
  const submit = page.getByRole('button', { name: /开始回测/ })
  assert.equal(await submit.isEnabled(), false)
  async function fill(profile) {
    await page.getByRole('combobox', { name: '产品', exact: true }).click()
    await page.locator('.ant-select-item-option[title="IM"]').click()
    for (const [label, value] of [['开始日期', '2025-02-17'], ['结束日期', '2025-03-25']]) {
      await page.getByRole('textbox', { name: label, exact: true }).fill(value)
      await page.getByRole('textbox', { name: label, exact: true }).press('Enter')
    }
    await page.getByRole('combobox', { name: '策略', exact: true }).click()
    await page.locator(`.ant-select-item-option[title="${profile}"]`).click()
    await page.getByText('ready=true', { exact: true }).waitFor()
  }
  // Real Chromium date-axis acceptance for the cumulative return and drawdown charts.
  async function dateAxisAcceptance(result) {
    const plots = page.locator('.js-plotly-plot')
    const dates = result.daily.map(row => row.trade_date)
    const views = [result.views.returns, result.views.drawdown]
    const evidenceBefore = evidence.length
    const statesBefore = states.length
    assert.ok(dates.length > 3)
    async function chartState(index) {
      return plots.nth(index).evaluate(el => ({
        type: el._fullLayout.xaxis.type,
        x: el.data.map(trace => trace.x),
        y: el.data.map(trace => trace.y),
        shapes: el.layout.shapes.map(shape => shape.x0),
        annotations: el.layout.annotations.map(annotation => [annotation.text, annotation.x]),
        range: Array.from(el._fullLayout.xaxis.range),
        ticktext: el._fullLayout.xaxis.ticktext,
      }))
    }
    async function pointXs(index) {
      return plots.nth(index).evaluate(el => Array.from(el.querySelectorAll('.scatterlayer .trace')[0]
        .querySelectorAll('.point')).slice(0, 4).map(point => point.getBoundingClientRect().x))
    }
    async function assertMode(mode) {
      for (const [index, view] of views.entries()) {
        const actual = await chartState(index)
        assert.equal(actual.type, mode === 'trading' ? 'linear' : 'date')
        assert.deepEqual(actual.x, view.layers.map(binding => binding.layer.data.map((mark, position) => mode === 'trading' ? position : mark.x)))
        assert.deepEqual(actual.y, view.layers.map(binding => binding.layer.data.map(mark => mark.y)))
        assert.deepEqual(actual.shapes, view.events.map(event => mode === 'trading' ? dates.indexOf(event.x) : event.x))
        assert.deepEqual(actual.annotations.map(([, x]) => x), view.events.map(event => mode === 'trading' ? dates.indexOf(event.x) : event.x))
        assert.deepEqual(actual.annotations.map(([text]) => text), view.events.map(event => event.label))
        if (mode === 'trading') {
          assert.ok(actual.ticktext.length > 0 && actual.ticktext.length <= 8)
          assert.ok(actual.ticktext.every(text => /^\d{4}-\d{2}-\d{2}$/.test(text)))
          assert.ok(actual.range[0] < 0 && actual.range[1] > dates.length - 1 && actual.range[1] < dates.length + 5)
        }
      }
    }
    async function waitType(type) {
      await page.waitForFunction(expected => [...document.querySelectorAll('.js-plotly-plot')]
        .every(el => el._fullLayout?.xaxis?.type === expected), type)
    }
    async function drag(index, from, to) {
      const plot = plots.nth(index)
      await plot.evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }))
      const box = await plot.locator('.nsewdrag').boundingBox()
      await page.mouse.move(box.x + box.width * from, box.y + box.height * .5)
      await page.mouse.down()
      await page.mouse.move(box.x + box.width * to, box.y + box.height * .5, { steps: 12 })
      await page.mouse.up()
    }
    async function waitRangeChanged(index, before) {
      await page.waitForFunction(({ i, old }) => JSON.stringify(Array.from(document.querySelectorAll('.js-plotly-plot')[i]._fullLayout.xaxis.range)) !== JSON.stringify(old), { i: index, old: before })
    }
    await waitType('linear')
    await assertMode('trading')
    const tradingRange = (await chartState(0)).range
    // A long non-session gap occupies one ordinal step in Trading Days.
    const tradingGaps = await pointXs(0)
    assert.ok(tradingGaps.length >= 4)
    assert.ok(Math.abs((tradingGaps[1] - tradingGaps[0]) - (tradingGaps[2] - tradingGaps[1])) < 1.5)
    // Hover keeps the real supplied date in Trading Days.
    const returns = plots.first()
    await returns.locator('.scatterlayer .trace').first().locator('.point').first().hover({ force: true })
    await page.waitForFunction(() => document.querySelector('.js-plotly-plot .hoverlayer')?.textContent.includes('2025-02-17'))
    assert.match(await returns.locator('.hoverlayer').textContent(), /Strategy\s*2025-02-17/)
    await page.screenshot({ path: resolve(output, 'date-axis-trading.png'), fullPage: true })
    // Zoom in Trading Days, then switch: the calendar viewport must be the full new domain.
    await returns.locator('[data-title="Zoom"]').click()
    await drag(0, .15, .75)
    await waitRangeChanged(0, tradingRange)
    await page.getByText('Calendar Days', { exact: true }).click()
    await waitType('date')
    await assertMode('calendar')
    const calendarRange = (await chartState(0)).range
    assert.notDeepEqual(calendarRange, tradingRange)
    // The 31-day gap is visibly wider than a 1-day gap in Calendar Days.
    const calendarGaps = await pointXs(0)
    assert.ok(calendarGaps[1] - calendarGaps[0] > 5 * (calendarGaps[2] - calendarGaps[1]))
    await returns.locator('.scatterlayer .trace').first().locator('.point').first().hover({ force: true })
    await page.waitForFunction(() => document.querySelector('.js-plotly-plot .hoverlayer')?.textContent.includes('2025-02-17'))
    // Zoom, Pan and Reset keep working in Calendar Days and restore the full calendar domain.
    await drag(0, .45, .7)
    await waitRangeChanged(0, calendarRange)
    await plots.first().locator('[data-title="Reset axes"]').click()
    await page.waitForFunction(old => JSON.stringify(Array.from(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range)) === JSON.stringify(old), calendarRange)
    const pan = plots.first().locator('[data-title="Pan"]')
    await pan.click()
    await drag(0, .55, .7)
    await waitRangeChanged(0, calendarRange)
    await plots.first().locator('[data-title="Reset axes"]').click()
    await page.waitForFunction(old => JSON.stringify(Array.from(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range)) === JSON.stringify(old), calendarRange)
    await page.screenshot({ path: resolve(output, 'date-axis-calendar.png'), fullPage: true })
    // Legend selection survives mode changes.
    await returns.locator('.legend .traces').first().click()
    await page.waitForFunction(() => document.querySelector('.js-plotly-plot')._fullData.some(trace => trace.visible === 'legendonly'))
    await page.getByText('Trading Days', { exact: true }).click()
    await waitType('linear')
    await assertMode('trading')
    assert.deepEqual((await chartState(0)).range, tradingRange)
    assert.ok(await returns.evaluate(el => el._fullData.some(trace => trace.visible === 'legendonly')))
    await page.getByText('Calendar Days', { exact: true }).click()
    await waitType('date')
    assert.ok(await returns.evaluate(el => el._fullData.some(trace => trace.visible === 'legendonly')))
    await page.getByText('Trading Days', { exact: true }).click()
    await waitType('linear')
    await returns.locator('.legend .traces').first().click()
    await page.waitForFunction(() => document.querySelector('.js-plotly-plot')._fullData.every(trace => trace.visible !== 'legendonly'))
    // Repeated switching stays stable and never changes data or issues a request.
    for (let round = 0; round < 3; round++) {
      await page.getByText('Calendar Days', { exact: true }).click(); await waitType('date')
      await page.getByText('Trading Days', { exact: true }).click(); await waitType('linear')
    }
    await assertMode('trading')
    assert.deepEqual((await chartState(0)).range, tradingRange)
    assert.equal(evidence.length, evidenceBefore)
    assert.equal(states.length, statesBefore)
    console.log('PASS: W2 date-axis default/mapping/sync/spacing/hover/zoom-pan-reset/legend with no requests or value change')
  }
  const persistedRunIds = () => {
    const result = spawnSync('poetry', ['run', 'python', '-c',
      'import json,sqlite3,sys; from pathlib import Path; c=sqlite3.connect(Path(sys.argv[1]).as_uri()+"?mode=ro",uri=True); print(json.dumps([r[0] for r in c.execute("SELECT run_id FROM runs")])); c.close()',
      resolve(env.LAB_BACKTESTING_RUN_ROOT, 'runs.sqlite3')], { cwd: root, env, encoding: 'utf8' })
    assert.equal(result.status, 0, result.stderr)
    return JSON.parse(result.stdout)
  }
  const runIds = []
  for (const [profile, pnl, contract] of [['expiry_to_M1_v1', 22000, 'IM2504.CFX'], ['expiry_to_Q1_v1', 19000, 'IM2506.CFX']]) {
    await fill(profile)
    assert.equal((await persistedRunIds()).length, runIds.length, 'preflight and Enter cannot create Run')
    const acceptedResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/api/backtesting/futures-roll/runs'))
    await submit.click()
    const accepted = await acceptedResponse
    assert.equal(accepted.status(), 202)
    const admission = await accepted.json(); assert.equal(admission.status, 'PENDING')
    runIds.push(admission.run_id)
    // Real busy response from the same worker, no second Run.
    if (runIds.length === 1) {
      await page.getByText('RUNNING', { exact: true }).waitFor()
      await page.waitForTimeout(1000)
      const busy = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/api/backtesting/futures-roll/runs'))
      await submit.click(); assert.equal((await busy).status(), 409)
      await page.getByText(/RUN_BUSY：/).waitFor()
    }
    await page.getByTestId('backtest-result').waitFor()
    await page.locator('.js-plotly-plot .nsewdrag').first().waitFor()
    assert.equal(await page.locator('.js-plotly-plot').count(), 2)
    const payload = await (await context.request.get(`http://127.0.0.1:5173/api/backtesting/futures-roll/runs/${admission.run_id}/result`)).json()
    assert.equal(payload.data.summary.total_pnl, pnl)
    assert.equal(payload.data.rolls[0].new_contract_code, contract)
    await page.getByRole('cell', { name: contract, exact: true }).first().waitFor()
    await page.getByText('研究证据与限制 · Evidence / Limitations', { exact: true }).click()
    await page.getByText(payload.data.evidence.input_fingerprint, { exact: true }).waitFor()
    // Plotly receives the exact producer data, units and event annotations.
    const actual = await page.locator('.js-plotly-plot').first().evaluate(el => ({
      ys: el.data.filter(t => t.type === 'scatter' && t.showlegend !== false).map(t => t.y),
      events: el.layout.shapes.length, tickformat: el.layout.yaxis.tickformat,
    }))
    assert.equal(actual.events, payload.data.views.returns.events.length)
    assert.ok(actual.ys.some(ys => JSON.stringify(ys) === JSON.stringify(payload.data.views.returns.layers[0].layer.data.map(m => m.y))))
    assert.equal(actual.tickformat, '.1%')
    if (runIds.length === 1) await dateAxisAcceptance(payload.data)
    await page.screenshot({ path: resolve(output, `${profile}.png`), fullPage: true })
    await page.reload(); await page.getByTestId('backtest-result').waitFor()
    // Reloading restores the Run with the default Trading Days viewport.
    await page.waitForFunction(() => document.querySelector('.js-plotly-plot')._fullLayout.xaxis.type === 'linear')
    assert.deepEqual(await page.locator('.js-plotly-plot').first().evaluate(el => el.data[0].x.slice(0, 2)), [0, 1])
    assert.ok(page.url().includes(admission.run_id))
  }
  assert.ok(states.includes('RUNNING')); assert.ok(states.includes('COMPLETED'))
  await page.goBack(); await page.getByTestId('backtest-result').waitFor(); assert.ok(page.url().includes(runIds[0]))
  await page.goForward(); await page.getByTestId('backtest-result').waitFor(); assert.ok(page.url().includes(runIds[1]))
  // Incomplete/unavailable readiness remains advisory. Real submit path is retained.
  await fill('expiry_to_Q1_v1')
  await page.route('**/api/backtesting/futures-roll/preflight', async route => {
    const response = await route.fetch(); const json = await response.json()
    json.ready = false; json.futures.state = 'incomplete'
    await route.fulfill({ response, json })
  })
  await page.getByRole('button', { name: '重新检查数据' }).click()
  await page.getByText('ready=false', { exact: true }).waitFor(); assert.equal(await submit.isEnabled(), true)
  await page.unroute('**/api/backtesting/futures-roll/preflight')
  await page.route('**/api/backtesting/futures-roll/preflight', route => route.fulfill({ status: 503, json: { error: { kind: 'unavailable', detail: 'safe', param: null } } }))
  await page.getByRole('button', { name: '重新检查数据' }).click()
  await page.getByText('数据检查失败：回测服务暂不可用，请稍后重试。', { exact: true }).waitFor()
  assert.equal(await submit.isEnabled(), true)
  await page.unroute('**/api/backtesting/futures-roll/preflight')
  // Lost POST response: real worker creates one run; client never replays.
  let lostAccepted
  await page.route('**/api/backtesting/futures-roll/runs', async route => {
    const response = await route.fetch(); assert.equal(response.status(), 202)
    lostAccepted = await response.json(); await route.abort('failed')
  })
  await submit.click(); await page.getByText(/网络响应丢失。提交结果可能已被服务器接受/).waitFor()
  await page.waitForTimeout(5500)
  assert.equal((await persistedRunIds()).length, 3); assert.ok(lostAccepted.run_id)
  assert.ok(page.url().includes(runIds[1]))
  await page.unroute('**/api/backtesting/futures-roll/runs')
  // Safe GET recovery uses the same completed immutable identity.
  await page.route('**/api/backtesting/futures-roll/runs/*/result', route => route.fulfill({ status: 503, json: { error: { kind: 'read_busy', detail: 'safe', param: null } } }))
  await page.reload(); await page.getByText('结果读取繁忙，请手动重试。', { exact: true }).waitFor()
  assert.equal(await page.getByTestId('backtest-result').count(), 0)
  await page.unroute('**/api/backtesting/futures-roll/runs/*/result')
  await page.getByRole('button', { name: '重新读取结果' }).click(); await page.getByTestId('backtest-result').waitFor()
  // Unknown/foreign identities cannot leave old result on screen.
  const foreign = await browser.newContext()
  const foreignCredentials = { username: 'wp7_other_user', password: randomBytes(24).toString('base64url') }
  // Provision the second identity through the published Auth Python service;
  // register HTTP is intentionally limited to one request / IP / 300 seconds.
  const provision = spawnSync('poetry', ['run', 'python', '-c',
    'import json,sys; from ui_http.auth import create_service; create_service().register(**json.load(sys.stdin))'],
    { cwd: root, env, input: JSON.stringify(foreignCredentials), encoding: 'utf8' })
  assert.equal(provision.status, 0, provision.stderr)
  const foreignId = cli('pending').match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i)?.[0]
  assert.ok(foreignId); cli('approve', foreignId)
  assert.equal((await foreign.request.post('http://127.0.0.1:5173/auth/login', { headers: { Origin: env.LAB_AUTH_ORIGIN }, data: foreignCredentials })).status(), 200)
  const foreignPage = await foreign.newPage()
  await foreignPage.goto(`http://127.0.0.1:5173/backtesting?run_id=${runIds[0]}`)
  await foreignPage.getByText('回测不存在或无权访问。', { exact: true }).waitFor()
  assert.equal(await foreignPage.getByTestId('backtest-result').count(), 0)
  const denied = await foreign.request.get(`http://127.0.0.1:5173/api/backtesting/futures-roll/runs/${runIds[0]}`)
  const missing = await foreign.request.get('http://127.0.0.1:5173/api/backtesting/futures-roll/runs/' + 'f'.repeat(32))
  assert.equal(denied.status(), 404); assert.deepEqual(await denied.json(), await missing.json())
  await foreign.close()
  await page.goto('http://127.0.0.1:5173/backtesting?run_id=' + 'f'.repeat(32))
  await page.getByText('回测不存在或无权访问。', { exact: true }).waitFor()
  assert.equal(await page.getByTestId('backtest-result').count(), 0)
  await page.goto(`http://127.0.0.1:5173/backtesting?run_id=${runIds[1]}`)
  await page.getByTestId('backtest-result').waitFor()
  // Fault injection changes only delivered HTTP responses; successful results above
  // always come from the actual worker. These checks cover terminal/error rendering.
  const selectedStatus = `**/api/backtesting/futures-roll/runs/${runIds[1]}`
  for (const status of ['FAILED', 'INTERRUPTED']) {
    await page.route(selectedStatus, async route => {
      const response = await route.fetch(); const json = await response.json()
      json.status = status; json.result_available = false
      json.failure = { stage: 'execution', category: 'internal_failure', dependency: null, reason: 'internal_failure' }
      await route.fulfill({ response, json })
    })
    await page.reload(); await page.getByText(status, { exact: true }).waitFor()
    assert.equal(await page.getByTestId('backtest-result').count(), 0)
    await page.unroute(selectedStatus)
  }
  await page.route(selectedStatus, route => route.abort('failed'))
  await page.reload(); await page.getByText('STATUS_ERROR', { exact: true }).waitFor()
  await page.unroute(selectedStatus)
  await page.getByRole('button', { name: '重新读取状态' }).click(); await page.getByTestId('backtest-result').waitFor()
  for (const [status, kind, text] of [[409, 'corrupt', '回测记录或结果损坏，无法展示。'], [413, 'response_too_large', '结果响应超过大小限制。'], [503, 'unavailable', '回测服务暂不可用，请稍后重试。']]) {
    await page.route('**/api/backtesting/futures-roll/runs/*/result', route => route.fulfill({ status, json: { error: { kind, detail: 'safe', param: null } } }))
    await page.reload(); await page.getByText(text, { exact: true }).waitFor()
    assert.equal(await page.getByTestId('backtest-result').count(), 0)
    await page.unroute('**/api/backtesting/futures-roll/runs/*/result')
    await page.getByRole('button', { name: '重新读取结果' }).click(); await page.getByTestId('backtest-result').waitFor()
  }
  await page.route('**/api/backtesting/futures-roll/runs/*/result', route => route.fulfill({ status: 200, json: { invalid: true } }))
  await page.reload(); await page.getByText('服务器响应无效，无法安全展示。', { exact: true }).waitFor()
  await page.unroute('**/api/backtesting/futures-roll/runs/*/result')
  await page.getByRole('button', { name: '重新读取结果' }).click(); await page.getByTestId('backtest-result').waitFor()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.waitForTimeout(500)
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
  assert.ok(await page.locator('.js-plotly-plot').first().evaluate(el => el._fullLayout._size.w >= 300))
  await page.screenshot({ path: resolve(output, 'mobile.png'), fullPage: true })
  await page.setViewportSize({ width: 1440, height: 1000 })
  // Expiration on protected Result read tears down all protected content.
  await page.route('**/api/backtesting/futures-roll/runs/*/result', route => route.fulfill({ status: 401, json: { error: { kind: 'authentication_required', detail: 'safe' } } }))
  await page.reload(); await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  assert.equal(await page.getByTestId('backtest-result').count(), 0)
  assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0])
  assert.deepEqual(errors, [])
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify({ status: 'PASS', admissionStatus: 'PENDING', evidence, states, runIds, lostResponseRun: lostAccepted.run_id, errors }, null, 2))
  console.log(`PASS: WP7 Chromium -> Vite -> FastAPI -> worker -> public-service fixtures; evidence: ${output}`)
} catch (error) {
  console.error(evidence.join('\n'))
  if (page) { await page.screenshot({ path: '/tmp/wp7-backtesting-error.png', fullPage: true }).catch(() => {}); console.error(await page.locator('body').innerText().catch(() => 'Page unavailable')) }
  throw error
} finally {
  await browser?.close()
  for (const child of processes.reverse()) {
    // Windows Poetry/Python launchers leave descendants holding server ports/pipes.
    if (process.platform === 'win32' && child.exitCode === null) {
      spawnSync('taskkill', ['/pid', String(child.pid), '/t', '/f'], { stdio: 'ignore' })
    } else {
      child.kill('SIGTERM')
    }
    if (child.exitCode === null) await new Promise((done) => child.once('exit', done))
  }
  await rm(temporary, { recursive: true, force: true })
}
