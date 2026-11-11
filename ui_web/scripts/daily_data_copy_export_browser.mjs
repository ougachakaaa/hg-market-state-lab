// Real browser -> Vite proxy -> FastAPI -> temporary SQLite. Only market public
// providers are deterministic fixtures; Auth, Cookie and CLI are real.
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdtemp, rm, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const root = fileURLToPath(new URL('../../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'daily-data-evidence-'))
const frontendPort = Number(process.env.DAILY_DATA_FRONTEND_PORT ?? 5173)
const backendPort = Number(process.env.DAILY_DATA_BACKEND_PORT ?? 8011)
const origin = `http://127.0.0.1:${frontendPort}`
const backendOrigin = `http://127.0.0.1:${backendPort}`
const report = { checks: [], downloads: [], errors: [], status: 'RUNNING' }
const temporary = await mkdtemp(resolve(tmpdir(), 'daily-data-auth-'))
const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http',
  LAB_AUTH_ORIGIN: origin,
  LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'),
  LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'),
  LAB_FUTURES_BASIS_RUN_ROOT: resolve(temporary, 'futures-basis-runs') }
const processes = []
let browser
let page
const evidence = []
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
  for (const port of [backendPort, frontendPort]) {
    const server = createServer()
    await new Promise((done, reject) => server.once('error', reject).listen(port, '127.0.0.1', done))
    await new Promise((done) => server.close(done))
  }
  const backend = start('poetry', ['run', 'python', '-m', 'uvicorn', '--app-dir', 'ui_http/tests',
    'http_support.daily_data_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', String(backendPort), '--no-proxy-headers'])
  const configPath = resolve(temporary, 'vite.config.mjs')
  await writeFile(configPath, `import react from '${resolve(root, 'ui_web/node_modules/@vitejs/plugin-react/dist/index.js')}'; export default { plugins: [react()], server: { host: '127.0.0.1', proxy: Object.fromEntries(['/auth', '/mo-option-chain', '/mo-option-premium-plane'].map(path => [path, '${backendOrigin}'])) } }`)
  const frontend = start(process.execPath, ['node_modules/vite/bin/vite.js', '--strictPort', '--port', String(frontendPort), '--config', configPath], resolve(root, 'ui_web'))
  await ready(`${backendOrigin}/auth/me`, backend, 401)
  await ready(`${origin}/`, frontend, 200)
  browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  report.browser = browser.version()
  report.environment = { node: process.version, platform: process.platform, timezone: 'Asia/Shanghai' }
  const context = await browser.newContext({ permissions: ['clipboard-read', 'clipboard-write'], viewport: { width: 1440, height: 1100 }, timezoneId: 'Asia/Shanghai' })
  await context.addInitScript(() => {
    const create = URL.createObjectURL.bind(URL), revoke = URL.revokeObjectURL.bind(URL)
    window.__urls = { created: 0, revoked: 0, types: [] }
    URL.createObjectURL = (...args) => { const url = create(...args); window.__urls.created++; window.__urls.types.push(args[0].type); return url }
    URL.revokeObjectURL = url => { window.__urls.revoked++; revoke(url) }
  })
  page = await context.newPage()
  page.setDefaultTimeout(15000)
  page.on('pageerror', error => report.errors.push(String(error)))
  page.on('response', (res) => {
    const path = new URL(res.url()).pathname
    if (path.startsWith('/auth/') || path.startsWith('/mo-option')) evidence.push(`${path} ${res.status()}`)
  })
  const anonymous = await context.request.get(`${origin}/mo-option-chain`)
  assert.equal(anonymous.status(), 401)
  assert.equal((await context.request.get(`${origin}/mo-option-premium-plane`)).status(), 401)
  await page.goto(`${origin}/`)
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'MO Option Chain', exact: true }).count(), 0)
  assert.equal(evidence.some((entry) => entry.startsWith('/mo-option')), false)
  await page.getByRole('button', { name: '注册', exact: true }).click()
  await page.getByLabel('用户名', { exact: true }).fill('wp3_browser_user')
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
  assert.match(pending, /wp3_browser_user/)
  const userId = pending.match(/[0-9a-f]{8}-[0-9a-f-]{27,}/i)?.[0]
  assert.ok(userId, 'CLI pending must expose an approval identity')
  cli('approve', userId)
  await page.getByRole('button', { name: '返回登录', exact: true }).click()
  await page.getByLabel('用户名', { exact: true }).fill('wp3_browser_user')
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await page.getByRole('menuitem', { name: '研究总览', exact: true }).waitFor()
  const passed = text => { report.checks.push(text); console.log(`PASS: ${text}`) }
  let requestCount = 0
  page.on('request', req => { if (/\/mo-option-(chain|premium-plane)\?/.test(req.url())) requestCount++ })
  const products = [
    { title: 'MO Option Chain', path: '/mo-option-chain', date: '观察日期', region: '期权链结果', group: 'MO Option Chain copy actions', prefix: 'mo-option-chain', columns: 13 },
    { title: 'MO Premium Plane', path: '/mo-option-premium-plane', date: '观察日期', region: 'Premium plane results', group: 'MO Premium Plane copy actions', prefix: 'mo-premium-plane', columns: 31 },
  ]
  const secrets = [password, env.LAB_AUTH_JWT_SECRET, env.LAB_AUTH_DB_PATH, ...(await context.cookies()).map(cookie => cookie.value)]
  const scalar = value => value === null ? 'null' : String(value)
  const baseChain = ['target_trade_date', 'option_product', 'price_type', 'underlying_instrument_id', 'underlying_price', 'expiry_date', 'futures_present', 'futures_instrument_id', 'futures_price', 'option_type', 'instrument_id', 'strike', 'price']
  const basePremium = ['observation_kind', 'observation_value', 'option_product', 'price_type', 'underlying_instrument_id', 'underlying_price', 'expiry_date', 'dte', 'futures_present', 'futures_instrument_id', 'futures_price', 'instrument_id', 'option_type', 'strike', 'premium']
  // Test-owned coordinate manifest. Never import the production serializers/projections.
  const coordinates = [
    'underlying_spot.total.unannualized.points', 'underlying_spot.total.unannualized.yield',
    'underlying_spot.total.annualized.points', 'underlying_spot.total.annualized.yield',
    'underlying_spot.time_value.unannualized.points', 'underlying_spot.time_value.unannualized.yield',
    'underlying_spot.time_value.annualized.points', 'underlying_spot.time_value.annualized.yield',
    'expiry_futures.total.unannualized.points', 'expiry_futures.total.unannualized.yield',
    'expiry_futures.total.annualized.points', 'expiry_futures.total.annualized.yield',
    'expiry_futures.time_value.unannualized.points', 'expiry_futures.time_value.unannualized.yield',
    'expiry_futures.time_value.annualized.points', 'expiry_futures.time_value.annualized.yield',
  ]
  function expectedRows(data, premium) {
    const common = { option_product: data.option_product, price_type: data.price_type, underlying_instrument_id: data.underlying.instrument_id, underlying_price: data.underlying.price }
    const context = expiry => ({ expiry_date: expiry.expiry_date, dte: expiry.dte, futures_present: expiry.futures !== null, futures_instrument_id: expiry.futures?.instrument_id ?? null, futures_price: expiry.futures?.price ?? null })
    if (!premium) return data.expiries.flatMap(expiry => ['calls', 'puts'].flatMap(side => expiry[side].map(point => ({ ...common, ...context(expiry), target_trade_date: data.target_trade_date, option_type: side === 'calls' ? 'call' : 'put', ...point }))))
    return data.points.map(point => ({ ...common, ...context(data.expiries.find(e => e.expiry_date === point.expiry_date)), ...point, observation_kind: data.observation.kind, observation_value: data.observation.value,
      ...Object.fromEntries(coordinates.map(key => [`metric_${key.replaceAll('.', '_')}`, key.split('.').reduce((value, part) => value[part], point.metrics)])),
    }))
  }
  // RFC4180 parser including quoted newlines/escaped quotes, independent of exporter.
  function parseCsv(text) {
    const rows = []; let row = [], cell = '', quoted = false
    for (let i = 0; i < text.length; i++) {
      const char = text[i]
      if (char === '"') { if (quoted && text[i + 1] === '"') { cell += '"'; i++ } else quoted = !quoted }
      else if (!quoted && char === ',') { row.push(cell); cell = '' }
      else if (!quoted && char === '\r' && text[i + 1] === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; i++ }
      else cell += char
    }
    assert.equal(quoted, false); assert.equal(cell, ''); assert.equal(row.length, 0)
    return rows
  }
  function safeContent(text) {
    for (const secret of secrets) assert.ok(!text.includes(secret))
    assert.ok(!/lab_access_token|authorization|set-cookie|TUSHARE_TOKEN|LAB_AUTH_/i.test(text))
  }
  async function copy(product, data) {
    const requestsBefore = requestCount
    const group = page.getByRole('group', { name: product.group, exact: true })
    await group.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
    await group.getByRole('status').filter({ hasText: /^Copied$/ }).waitFor()
    const json = await page.evaluate(() => navigator.clipboard.readText())
    assert.equal(json, JSON.stringify(data, null, 2)); safeContent(json)
    await group.getByRole('button', { name: 'Copy Context JSON', exact: true }).click()
    await group.getByRole('status').filter({ hasText: /^Copied$/ }).waitFor()
    const contextText = await page.evaluate(() => navigator.clipboard.readText())
    const contextJson = JSON.parse(contextText)
    assert.deepEqual(Object.keys(contextJson), ['format_version', 'metadata', 'data'])
    assert.equal(contextJson.format_version, 'daily-data-context-v1')
    assert.equal(contextJson.metadata.product, product.title)
    const fields = product.columns === 31 ? { observation: data.observation } : { target_trade_date: data.target_trade_date }
    assert.deepEqual(contextJson.metadata.response_identity, { ...fields, option_product: data.option_product, price_type: data.price_type, underlying_instrument_id: data.underlying.instrument_id })
    assert.deepEqual(contextJson.data, JSON.parse(json))
    assert.ok(contextJson.metadata.reading_notes.every(note => typeof note === 'string'))
    for (const phrase of product.columns === 31 ? ['sparse Points', 'absent Point', 'null metric', 'numeric zero', 'futures: null'] : ['null price', 'numeric zero', 'futures: null', 'Call/Put grouping']) assert.ok(contextJson.metadata.reading_notes.join(' ').includes(phrase))
    assert.equal(contextText, JSON.stringify(contextJson, null, 2))
    safeContent(contextText)
    await writeFile(resolve(output, `${product.prefix}-context.json`), contextText)
    const event = page.waitForEvent('download')
    await group.getByRole('button', { name: 'Export Context JSON', exact: true }).click()
    const file = await event
    const filename = `${product.prefix}_${data.target_trade_date ?? data.observation.value}_${data.price_type}_context.json`
    assert.equal(file.suggestedFilename(), filename)
    const destination = resolve(output, `${report.downloads.length}-${filename}`)
    await file.saveAs(destination); assert.equal(await file.failure(), null)
    const bytes = await readFile(destination)
    const text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes)
    assert.equal(text, contextText)
    assert.deepEqual(bytes, Buffer.from(contextText, 'utf8'))
    assert.deepEqual(JSON.parse(text).data, data)
    safeContent(text)
    await page.waitForFunction(() => !document.querySelector('a[download]') && window.__urls.created === window.__urls.revoked)
    assert.equal(await page.evaluate(() => window.__urls.types.at(-1)), 'application/json;charset=utf-8')
    report.downloads.push({ filename, bytes: bytes.length, format: 'Context JSON V1', matchesClipboard: true })
    assert.equal(requestCount, requestsBefore)
    report.clipboardChecks = (report.clipboardChecks ?? 0) + 2
    return json
  }
  async function download(product, data) {
    const requestsBefore = requestCount
    const event = page.waitForEvent('download')
    await page.getByRole('group', { name: product.group }).getByRole('button', { name: 'Export CSV', exact: true }).click()
    const file = await event
    const filename = `${product.prefix}_${data.target_trade_date ?? data.observation.value}_${data.price_type}.csv`
    assert.equal(file.suggestedFilename(), filename)
    const destination = resolve(output, `${report.downloads.length}-${filename}`)
    await file.saveAs(destination); assert.equal(await file.failure(), null)
    const bytes = await readFile(destination)
    await writeFile(resolve(output, `${product.prefix}.csv`), bytes)
    assert.deepEqual([...bytes.subarray(0, 3)], [239, 187, 191])
    const text = bytes.subarray(3).toString('utf8'); safeContent(text)
    assert.ok(text.endsWith('\r\n')); assert.ok(!/(?<!\r)\n|\r(?!\n)/.test(text))
    const [header, ...rows] = parseCsv(text)
    const headers = product.columns === 13 ? baseChain : [...basePremium, ...coordinates.map(key => `metric_${key.replaceAll('.', '_')}`)]
    assert.deepEqual(header, headers); assert.equal(header.length, product.columns)
    const expected = expectedRows(data, product.columns === 31)
    assert.equal(rows.length, expected.length)
    rows.forEach((row, index) => { assert.equal(row.length, product.columns); assert.deepEqual(row, header.map(key => scalar(expected[index][key]))) })
    await page.waitForFunction(() => !document.querySelector('a[download]') && window.__urls.created === window.__urls.revoked)
    assert.equal(requestCount, requestsBefore)
    report.downloads.push({ filename, bytes: bytes.length, columns: header.length, rows: rows.length, bom: 'EF BB BF' })
    return text
  }
  async function enterDate(product, date) {
    const input = page.getByLabel(product.date, { exact: true })
    if (!date) {
      await input.hover()
      await page.getByRole('button', { name: '清除', exact: true }).click()
    } else {
      await input.fill(date)
      await input.press('Enter')
    }
  }
  async function screenshots(product, state) {
    for (const [width, height] of [[1440, 900], [1024, 768]]) {
      await page.setViewportSize({ width, height })
      await page.keyboard.press('Escape')
      await page.waitForTimeout(350) // Ant Design popup/sidebar transitions.
      await page.evaluate(() => window.scrollTo(0, 0))
      await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth)
      const actions = page.getByRole('group', { name: product.group, exact: true })
      if (await actions.count()) {
        assert.deepEqual(await actions.getByRole('button').allTextContents(), ['Copy Raw JSON', 'Copy Context JSON', 'Export CSV', 'Export Context JSON'])
        for (const button of await actions.getByRole('button').all()) {
          const box = await button.boundingBox()
          assert.ok(box && box.x >= 0 && box.x + box.width <= width)
        }
      }
      const path = resolve(output, `${product.prefix}-${state}-${width}.png`)
      await page.screenshot({ path })
      report.screenshots = [...(report.screenshots ?? []), path]
    }
  }
  async function query(product, date) {
    const result = page.waitForResponse(res => new URL(res.url()).pathname === product.path && res.status() === 200)
    await enterDate(product, date)
    const response = await result
    const data = await response.json()
    await page.getByRole('region', { name: product.region, exact: true }).waitFor()
    return data
  }
  async function noActions() { assert.equal(await page.getByRole('button', { name: 'Export Context JSON', exact: true }).count(), 0); assert.equal(await page.getByRole('button', { name: 'Export CSV', exact: true }).count(), 0); assert.equal(await page.getByRole('button', { name: 'Copy Raw JSON', exact: true }).count(), 0); assert.equal(await page.getByRole('button', { name: 'Copy Context JSON', exact: true }).count(), 0) }
  for (const product of process.env.DAILY_DATA_LAYOUT_ONLY ? [] : products) {
    await page.setViewportSize({ width: 1440, height: 900 })
    const expand = page.getByRole('button', { name: '展开', exact: true })
    if (await expand.isVisible()) await expand.click()
    if (product.columns === 13) {
      if (!(await page.getByRole('menuitem', { name: '数据总览', exact: true }).isVisible())) await page.getByRole('menuitem', { name: '日常数据', exact: true }).click()
      await page.getByRole('menuitem', { name: '数据总览', exact: true }).click()
      await page.getByRole('button', { name: '打开 MO Option Chain', exact: true }).click()
    } else await page.locator('.ant-menu-title-content').getByText(product.title, { exact: true }).click()
    await noActions()
    await screenshots(product, 'idle')
    const idleRequests = requestCount
    if (product.columns === 31) {
      await page.getByRole('combobox', { name: '价格口径', exact: true }).click()
      await page.getByText('开盘（Open）', { exact: true }).click()
      assert.equal(requestCount, idleRequests)
      await page.getByRole('combobox', { name: '价格口径', exact: true }).click()
      await page.getByText('收盘（Close）', { exact: true }).click()
    }
    const input = page.getByLabel(product.date, { exact: true })
    for (const invalid of ['2026-09-', '2026-02-30', 'invalid']) {
      await input.fill(invalid)
      await input.press('Enter')
      await input.press('Tab')
      assert.equal(requestCount, idleRequests)
    }
    for (const [width, height] of [[1440, 900], [1024, 768]]) {
      await page.setViewportSize({ width, height })
      const beforeCalendar = requestCount
      // Open a known month without committing the typed date.
      await input.click()
      await input.fill('2026-09-16')
      await page.locator('.ant-picker-dropdown:not(.ant-picker-dropdown-hidden) td[title="2026-09-17"]').waitFor()
      const calendar = page.locator('.ant-picker-dropdown:not(.ant-picker-dropdown-hidden)')
      await calendar.waitFor()
      await page.waitForTimeout(350)
      await page.screenshot({ path: resolve(output, `${product.prefix}-calendar-${width}.png`) })
      await calendar.locator('td[title="2026-09-17"]').click()
      await page.getByRole('region', { name: product.region, exact: true }).waitFor()
      assert.equal(requestCount, beforeCalendar + 1)
      if (product.columns === 31) {
        const response = page.waitForResponse(res => new URL(res.url()).pathname === product.path && res.status() === 200)
        await page.getByRole('combobox', { name: '价格口径', exact: true }).click()
        await page.getByText('开盘（Open）', { exact: true }).click()
        assert.equal((await (await response).json()).price_type, 'open')
        await page.getByRole('region', { name: product.region, exact: true }).waitFor()
        const close = page.waitForResponse(res => new URL(res.url()).pathname === product.path && res.status() === 200)
        await page.getByRole('combobox', { name: '价格口径', exact: true }).click()
        await page.getByText('收盘（Close）', { exact: true }).click()
        await close
        await page.getByRole('region', { name: product.region, exact: true }).waitFor()
      }
      await enterDate(product, '')
      await page.getByRole('status').filter({ hasText: '请选择观察日期' }).waitFor()
      await noActions()
    }
    const data = await query(product, '2026-09-17')
    await screenshots(product, 'success')
    assert.equal(data.expiries.length, 2)
    assert.equal(data.expiries[1].futures, null)
    const facts = product.columns === 31 ? data.points : data.expiries.flatMap(e => [...e.calls, ...e.puts])
    assert.equal(facts.length, product.columns === 31 ? 4 : 6)
    assert.ok(facts.some(point => (product.columns === 31 ? point.premium : point.price) === null))
    assert.ok(facts.some(point => (product.columns === 31 ? point.premium : point.price) === 0))
    assert.ok(facts.some(point => point.strike === 9000))
    const before = requestCount
    const json = await copy(product, data), csv = await download(product, data)
    assert.equal(requestCount, before)
    const unchanged = async () => { assert.equal(await copy(product, data), json); assert.equal(await download(product, data), csv); assert.equal(requestCount, before) }
    await page.getByRole('checkbox', { name: '2026-10-23', exact: true }).uncheck(); await unchanged()
    if (product.columns === 13) {
      await page.getByRole('button', { name: '扩大行权价视窗', exact: true }).click(); await unchanged()
      const advanced = page.getByText('高级设置 · 图表颜色', { exact: true })
      if (await advanced.count()) await advanced.click()
      const color = page.getByRole('button', { name: 'Call 颜色', exact: true })
      const previous = await color.innerText()
      await color.click()
      const hex = page.locator('.ant-color-picker-hex-input input')
      await hex.fill('123456'); await hex.press('Enter'); await page.keyboard.press('Escape')
      assert.notEqual(await color.innerText(), previous); await unchanged()
      await screenshots(product, 'colors-expanded')
    } else {
      for (const name of ['Put', 'Same-expiry futures', 'Time value', 'Unannualized', 'Yield']) {
        const radio = page.getByRole('radio', { name, exact: true })
        await radio.locator('xpath=ancestor::label').click(); assert.equal(await radio.isChecked(), true); await unchanged()
      }
      await page.getByText('View raw response', { exact: true }).click()
      await page.locator('.raw-response-code').waitFor()
      assert.equal(await page.locator('.raw-response-code').innerText(), json)
      await page.getByRole('button', { name: 'Copy JSON', exact: true }).click()
      assert.equal(await page.evaluate(() => navigator.clipboard.readText()), json)
      assert.equal(requestCount, before)
      // Query input actually changes the resolved response price type.
      const result = page.waitForResponse(res => new URL(res.url()).pathname === product.path && res.status() === 200)
      await page.getByRole('combobox', { name: '价格口径', exact: true }).click()
      await page.locator('.ant-select-item-option-content').getByText('最高（High）', { exact: true }).click()
      const high = await (await result).json(); assert.equal(high.price_type, 'high')
      await page.getByRole('region', { name: product.region, exact: true }).waitFor()
      await copy(product, high); await download(product, high)
    }
    passed(`${product.title}: real clipboard, identical Context JSON download, independent CSV fields, presentation independence and URL cleanup`)

    // Failure instrumentation is restricted to explicit failure scenarios.
    await page.evaluate(() => {
      window.__originalWrite = navigator.clipboard.writeText.bind(navigator.clipboard)
      navigator.clipboard.writeText = async () => { throw new Error('private fixture failure') }
    })
    const group = page.getByRole('group', { name: product.group })
    await group.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
    await group.getByText('Copy failed', { exact: true }).waitFor()
    await page.evaluate(() => { navigator.clipboard.writeText = window.__originalWrite; window.__originalCreate = URL.createObjectURL; URL.createObjectURL = () => { throw new Error('private fixture failure') } })
    const unexpectedDownloads = []
    const failedDownload = download => unexpectedDownloads.push(download.suggestedFilename())
    page.on('download', failedDownload)
    for (const name of ['Export CSV', 'Export Context JSON']) {
      await group.getByRole('button', { name, exact: true }).click()
      await group.getByText('Export failed', { exact: true }).waitFor()
      assert.equal(await group.getByText('Download started', { exact: true }).count(), 0)
    }
    await page.evaluate(() => { URL.createObjectURL = window.__originalCreate; navigator.clipboard.writeText = () => new Promise(resolve => { window.__finishCopy = resolve }) })
    await group.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
    for (const name of ['Copy Raw JSON', 'Copy Context JSON', 'Export CSV', 'Export Context JSON']) assert.equal(await group.getByRole('button', { name, exact: true }).isDisabled(), true)
    await query(product, '2026-09-18')
    await page.evaluate(() => { window.__finishCopy(); navigator.clipboard.writeText = window.__originalWrite })
    assert.equal(await page.getByRole('group', { name: product.group }).getByRole('status').count(), 0)
    assert.deepEqual(unexpectedDownloads, [])
    assert.equal(await page.getByText('private fixture failure', { exact: true }).count(), 0)
    page.off('download', failedDownload)
    await page.waitForFunction(() => !document.querySelector('a[download]'))

    // Delay a real HTTP response. Ignore abort only in this explicit race test so
    // an older response genuinely reaches React after the newer success.
    await page.evaluate(() => {
      window.__originalFetch = window.fetch
      window.fetch = (input, init) => window.__originalFetch(input, typeof input === 'string' && input.startsWith('/mo-option-') ? { ...init, signal: undefined } : init)
    })
    let release, arrived
    const waiting = new Promise(resolve => { arrived = resolve })
    const gate = new Promise(resolve => { release = resolve })
    const delayed = async route => {
      const response = await route.fetch(); arrived(); await gate
      await route.fulfill({ response })
    }
    const oldPattern = `**${product.path}?*${product.columns === 13 ? 'target_trade_date' : 'as_of'}=2026-09-21*`
    await page.route(oldPattern, delayed)
    await enterDate(product, '2026-09-21')
    let timeout
    try {
      await Promise.race([waiting, new Promise((_, reject) => { timeout = setTimeout(() => reject(new Error('Delayed fixture did not arrive')), 15000) })])
    } finally { clearTimeout(timeout) }
    await noActions()
    assert.match(await page.getByRole('status').innerText(), /正在加载.*2026-09-21/)
    await screenshots(product, 'loading')
    const newer = await query(product, '2026-09-22')
    const late = page.waitForResponse(res => res.url().includes('2026-09-21') && new URL(res.url()).pathname === product.path)
    release(); await late
    // Round-trip in the page lets the response promise/state updates settle.
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
    await copy(product, newer)
    await page.unroute(oldPattern, delayed)
    await page.evaluate(() => { window.fetch = window.__originalFetch })

    const pattern = `**${product.path}?*`
    const failures = [[503, { error: { kind: product.columns === 31 ? 'premium_plane_unavailable' : 'option_chain_unavailable', detail: 'Fixture unavailable', param: null } }], [200, { invalid: true }]]
    if (product.columns === 31) failures.push([200, { ...newer, points: [] }])
    for (const [index, [status, body]] of failures.entries()) {
      await page.route(pattern, route => route.fulfill({ status, json: body }))
      await enterDate(product, ['2026-09-23', '2026-09-24', '2026-09-25'][index])
      await page.getByRole('alert').waitFor(); await noActions()
      assert.match(await page.getByRole('alert').innerText(), /清空日期并重新选择/)
      if (index === 0) await screenshots(product, 'error')
      await page.unroute(pattern)
    }
    await enterDate(product, ''); await noActions()
    const recovered = await query(product, '2026-09-17')
    await copy(product, recovered); await download(product, recovered)
    passed(`${product.title}: idle/loading/error/invalid, late response, stale clipboard, failure feedback and recovery`)
  }
  // Layout stress uses validated deterministic HTTP-shaped facts, never market I/O.
  for (const product of products) {
    await page.goto(`${origin}/data/${product.columns === 13 ? 'mo-option-chain' : 'mo-premium-plane'}`)
    const seed = await (await context.request.get(`${origin}${product.path}?${product.columns === 13 ? 'target_trade_date' : 'as_of'}=2026-09-17&option_product=MO&price_type=close`)).json()
    const dense = structuredClone(seed)
    const dates = ['2026-09-25', '2026-10-23', '2026-11-27', '2026-12-25', '2027-01-22', '2027-02-26', '2027-03-26', '2027-04-23']
    dense.expiries = dates.map((date, index) => ({ ...structuredClone(seed.expiries[index % seed.expiries.length]), expiry_date: date,
      ...(product.columns === 31 ? { dte: 8 + index * 28 } : {}) }))
    if (product.columns === 31) dense.points = dates.flatMap((date, index) => ['call', 'put'].flatMap(side => Array.from({ length: 80 }, (_, row) => ({
      ...structuredClone(seed.points.find(point => point.option_type === side) ?? seed.points[0]),
      expiry_date: date, option_type: side, strike: 6500 + row * 25,
      instrument_id: `MO-${index}-${side}-${row}`,
    }))))
    const pattern = `**${product.path}?*`
    await page.route(pattern, route => route.fulfill({ json: dense }))
    await query(product, '2026-09-17')
    const before = requestCount
    await screenshots(product, 'dense')
    for (const [width, height] of [[1440, 900], [1024, 768]]) {
      await page.setViewportSize({ width, height })
      await page.waitForTimeout(350) // Let the responsive breakpoint settle before selecting the toggle.
      for (let transition = 0; transition < 2; transition++) {
        await page.getByRole('button', { name: /^(展开导航|折叠导航)$/ }).click()
        await page.waitForTimeout(350)
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))
        if (product.columns === 13) {
          await page.waitForFunction(() => {
            const frame = document.querySelector('.chart-frame'), plot = frame?.querySelector('.js-plotly-plot')
            return plot?._fullLayout && Math.abs(plot._fullLayout.width - frame.clientWidth) < 2
          })
        }
      }
      if (product.columns === 31) {
        const body = page.locator('.premium-table .ant-table-body')
        if (process.env.DAILY_DATA_LAYOUT_PHASE !== 'before') {
          assert.ok(await body.evaluate(node => node.scrollHeight > node.clientHeight && node.scrollWidth > node.clientWidth))
          await body.evaluate(node => { node.scrollTop = 500; node.scrollLeft = 700 })
          assert.ok(await body.evaluate(node => {
            const strike = node.querySelector('tr[data-row-key] > th')
            return strike && getComputedStyle(strike).position === 'sticky' && Math.abs(strike.getBoundingClientRect().left - node.getBoundingClientRect().left) < 2
          }))
        }
      }
      await page.screenshot({ path: resolve(output, `${product.prefix}-dense-scrolled-${width}.png`), fullPage: true })
    }
    if (product.columns === 13) {
      const plotFacts = await page.locator('.js-plotly-plot').evaluate(plot => ({ data: plot.data, shapes: plot.layout.shapes, annotations: plot.layout.annotations, xaxis: plot.layout.xaxis, yaxis: plot.layout.yaxis }))
      await writeFile(resolve(output, 'chain-plot-facts.json'), JSON.stringify(plotFacts, null, 2))
      await page.getByText('合约明细', { exact: true }).first().click()
    } else {
      await page.getByText('View raw response', { exact: true }).click()
      assert.equal(await page.locator('.raw-response-code').innerText(), JSON.stringify(dense, null, 2))
    }
    await page.screenshot({ path: resolve(output, `${product.prefix}-evidence-expanded.png`), fullPage: true })
    const raw = await copy(product, dense)
    await writeFile(resolve(output, `${product.prefix}-raw.json`), raw)
    await download(product, dense)
    if (process.env.DAILY_DATA_BASELINE_EVIDENCE) {
      const files = [`${product.prefix}-raw.json`, `${product.prefix}-context.json`, `${product.prefix}.csv`, ...(product.columns === 13 ? ['chain-plot-facts.json'] : [])]
      for (const file of files) assert.deepEqual(await readFile(resolve(output, file)), await readFile(resolve(process.env.DAILY_DATA_BASELINE_EVIDENCE, file)), `Baseline bytes: ${file}`)
      passed(`${product.title}: baseline Raw/Context/CSV bytes${product.columns === 13 ? ' and Plotly facts' : ''} unchanged`)
    }
    // Empty presentation remains successful with controls and complete copy sources.
    const empty = structuredClone(dense)
    if (product.columns === 13) empty.expiries.forEach(expiry => [...expiry.calls, ...expiry.puts].forEach(point => { point.price = null }))
    else empty.points = empty.points.filter(point => point.option_type === 'put')
    await page.unroute(pattern)
    await page.route(pattern, route => route.fulfill({ json: empty }))
    await query(product, '2026-09-18')
    await screenshots(product, 'presentation-empty')
    assert.ok(await page.getByText(product.columns === 13 ? '选中的到期日没有可绘制的价格。' : '当前选择下无 analytical observation；可调整期权类型或显示到期日。', { exact: true }).isVisible())
    assert.equal(requestCount, before + 1)
    await page.unroute(pattern)
    passed(`${product.title}: dense layout, sidebar resizing, expanded evidence and legal presentation empty state`)
  }
  await page.getByRole('button', { name: '退出登录', exact: true }).click()
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  for (const product of products) assert.equal((await context.request.get(`${origin}${product.path}`)).status(), 401)
  assert.deepEqual(report.errors, [])
  report.productRequests = requestCount
  passed('Logout protects both products; no page errors or credential leakage')
  report.status = 'PASS'
} catch (error) {
  report.status = 'FAIL'; report.failure = String(error)
  if (page) await page.screenshot({ path: resolve(output, 'failure.png'), fullPage: true }).catch(() => {})
  throw error
} finally {
  await browser?.close()
  for (const child of processes.reverse()) {
    child.kill('SIGTERM')
    if (child.exitCode === null) await new Promise(done => child.once('exit', done))
  }
  await rm(temporary, { recursive: true, force: true })
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(report, null, 2) + '\n')
  console.log(`Browser evidence: ${output}`)
}
