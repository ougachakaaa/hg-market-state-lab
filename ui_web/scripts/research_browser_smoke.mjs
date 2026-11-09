// Real browser -> Vite proxy -> FastAPI -> temporary SQLite. Only market public
// providers are deterministic fixtures; Auth, Cookie and CLI are real.
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdir, mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const root = fileURLToPath(new URL('../../', import.meta.url))
const temporary = await mkdtemp(resolve(tmpdir(), 'g3-auth-'))
const screenshots = resolve(tmpdir(), 'hg-market-state-lab-web-workspace')
await mkdir(screenshots, { recursive: true })
const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http',
  LAB_AUTH_ORIGIN: 'http://127.0.0.1:5173',
  LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'),
  LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'),
  LAB_RESEARCH_PUBLICATION_ROOT: resolve(temporary, 'publications') }
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
  for (const port of [8011, 5173]) {
    const server = createServer()
    await new Promise((done, reject) => server.once('error', reject).listen(port, '127.0.0.1', done))
    await new Promise((done) => server.close(done))
  }
  const fixture = spawnSync('poetry', ['run', 'python', 'ui_web/scripts/research_browser_fixture.py', temporary], { cwd: root, env, encoding: 'utf8' })
  assert.equal(fixture.status, 0, fixture.stderr)
  const publicationId = fixture.stdout.trim().split(/\s+/).at(-1)
  const backend = start('poetry', ['run', 'python', '-m', 'uvicorn', '--app-dir', 'ui_http/tests',
    'http_support.auth_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', '8011', '--no-proxy-headers'])
  const frontend = start(process.execPath, ['node_modules/vite/bin/vite.js', '--strictPort'], resolve(root, 'ui_web'))
  await ready('http://127.0.0.1:8011/auth/me', backend, 401)
  await ready('http://127.0.0.1:5173/', frontend, 200)
  browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  page = await context.newPage()
  page.setDefaultTimeout(15000)
  page.on('response', (res) => {
    const path = new URL(res.url()).pathname
    if (path.startsWith('/auth/') || path.startsWith('/mo-option') || path.startsWith('/api/research')) evidence.push(`${path} ${res.status()}`)
  })
  const anonymous = await context.request.get('http://127.0.0.1:5173/mo-option-chain')
  assert.equal(anonymous.status(), 401)
  await page.goto('http://127.0.0.1:5173/')
  await page.getByRole('button', { name: 'Login', exact: true }).waitFor()
  await page.screenshot({ path: resolve(screenshots, 'login.png'), fullPage: true })
  assert.equal(await page.getByRole('button', { name: 'MO Option Chain', exact: true }).count(), 0)
  assert.equal(evidence.some((entry) => entry.startsWith('/mo-option')), false)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  await page.getByLabel('Username', { exact: true }).fill('g3_browser_user')
  const password = randomBytes(24).toString('base64url')
  await page.getByLabel('Password', { exact: true }).fill(password)
  const registration = page.waitForResponse((res) => res.url().endsWith('/auth/register'))
  await page.getByRole('button', { name: 'Submit Registration', exact: true }).click()
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
  await page.getByRole('button', { name: '返回 Login', exact: true }).click()
  await page.getByLabel('Username', { exact: true }).fill('g3_browser_user')
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Login', exact: true }).click()
  await page.getByRole('button', { name: 'Research Workspace', exact: true }).waitFor()
  assert.equal(new URL(page.url()).pathname, '/research')
  await page.getByText('Index Trailing Cumulative Return Research', { exact: true }).waitFor()
  assert.ok(evidence.includes('/api/research/capabilities 200'))
  assert.equal(await page.getByText('Local / Python only').count(), 1)
  assert.equal(await page.getByText('Local / Python only · Report generation available').count(), 1)
  await page.getByRole('region', { name: 'Available online' }).getByRole('button', { name: 'View details' }).click()
  await page.getByText(/live readiness: not_probed/).waitFor()
  assert.ok(evidence.includes('/api/research/capabilities/trailing_cumulative_return_v1 200'))
  await page.screenshot({ path: resolve(screenshots, 'research.png'), fullPage: true })
  const cookie = (await context.cookies()).find((value) => value.name === 'lab_access_token')
  assert.ok(cookie?.httpOnly)
  assert.equal(cookie.sameSite, 'Strict')
  assert.equal(cookie.secure, false)
  assert.equal(await page.evaluate(() => document.cookie.includes('lab_access_token')), false)
  assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0])
  await page.getByRole('button', { name: 'Open Research Explorer', exact: true }).click()
  assert.equal(new URL(page.url()).pathname, '/research/publications')
  await page.getByText(publicationId, { exact: true }).waitFor()
  await page.screenshot({ path: resolve(screenshots, 'research-explorer.png'), fullPage: true })
  await page.getByRole('button', { name: /选\s*择/ }).first().click()
  await page.getByText('声明的 Research scope').waitFor()
  const distribution = page.locator('.ant-list-item').filter({ hasText: 'distribution' }).first()
  const intervalResponse = page.waitForResponse(res => /\/analyses\//.test(res.url()))
  await distribution.getByRole('button', { name: '选择 Analysis' }).click()
  const intervalUrl = (await intervalResponse).url()
  await page.getByText('Observation population and coverage (原始比例)').waitFor()
  const countResponse = page.waitForResponse(res => /\/views\//.test(res.url()))
  await page.getByRole('button', { name: 'count', exact: true }).click()
  assert.equal((await countResponse).status(), 200)
  await page.locator('.js-plotly-plot').waitFor()
  const countValues = await page.locator('.js-plotly-plot').evaluate(el => Array.from(el.data[0].y))
  const frequencyResponse = page.waitForResponse(res => /\/views\//.test(res.url()))
  await page.getByRole('button', { name: 'frequency', exact: true }).click()
  assert.equal((await frequencyResponse).status(), 200)
  await page.waitForFunction(previous => { const plot = document.querySelector('.js-plotly-plot'); return plot?.data && JSON.stringify(Array.from(plot.data[0].y)) !== JSON.stringify(previous) }, countValues)
  const otherJobQuantile = page.locator('.ant-list-item').filter({ hasText: 'quantiles' }).nth(1)
  const quantileAnalysis = page.waitForResponse(res => /\/analyses\//.test(res.url()))
  await otherJobQuantile.getByRole('button', { name: '选择 Analysis' }).click()
  assert.notEqual((await quantileAnalysis).url(), intervalUrl)
  await page.getByText('Probability', { exact: true }).waitFor()
  const quantileView = page.waitForResponse(res => /\/views\//.test(res.url()))
  await page.getByRole('button', { name: 'quantile', exact: true }).click()
  assert.equal((await quantileView).status(), 200)
  await page.locator('.js-plotly-plot').waitFor()
  const researchPlotBounds = await page.locator('.js-plotly-plot').first().boundingBox()
  assert.ok(researchPlotBounds && researchPlotBounds.x >= 0 && researchPlotBounds.x + researchPlotBounds.width <= 1441, 'Research chart fits the viewport')
  await page.screenshot({ path: resolve(screenshots, 'research-chart.png'), fullPage: true })
  await page.getByRole('button', { name: 'Daily Data overview', exact: true }).click()
  assert.equal(new URL(page.url()).pathname, '/data')
  await page.screenshot({ path: resolve(screenshots, 'daily-data.png'), fullPage: true })
  await page.getByRole('button', { name: 'MO Option Chain →', exact: true }).click()
  await page.getByLabel('目标交易日', { exact: true }).fill('2026-09-17')
  await page.getByRole('region', { name: '期权链结果', exact: true }).waitFor()
  await page.locator('.option-chain-page .js-plotly-plot').waitFor()
  const chainBounds = await page.locator('.option-chain-page .js-plotly-plot').boundingBox()
  assert.ok(chainBounds && chainBounds.x >= 0 && chainBounds.x + chainBounds.width <= 1441, 'Option chart fits the viewport')
  await page.screenshot({ path: resolve(screenshots, 'mo-option-chain.png'), fullPage: true })
  await page.locator('.ant-menu-title-content').getByText('MO Premium Plane', { exact: true }).click()
  await page.getByLabel('Observation 日期', { exact: true }).fill('2026-09-17')
  await page.getByRole('region', { name: 'Premium plane results', exact: true }).waitFor()
  await page.screenshot({ path: resolve(screenshots, 'mo-premium-plane.png'), fullPage: true })
  const sider = page.locator('.ant-layout-sider')
  const expandedWidth = (await sider.boundingBox()).width
  await page.locator('.ant-layout-sider-trigger').click()
  await page.waitForFunction(width => document.querySelector('.ant-layout-sider')?.getBoundingClientRect().width < width, expandedWidth)
  await page.locator('.ant-layout-sider-trigger').click()
  await page.waitForFunction(width => document.querySelector('.ant-layout-sider')?.getBoundingClientRect().width === width, expandedWidth)
  await page.waitForLoadState('networkidle')
  await page.reload()
  await page.getByRole('heading', { name: 'MO 年化权利金平面', exact: true }).waitFor()
  assert.equal(new URL(page.url()).pathname, '/data/mo-premium-plane')
  await page.goBack()
  await page.getByRole('heading', { name: 'MO 期权链', exact: true }).waitFor()
  await page.goForward()
  await page.getByRole('heading', { name: 'MO 年化权利金平面', exact: true }).waitFor()
  await page.goto('http://127.0.0.1:5173/research/publications')
  await page.getByRole('heading', { name: 'Research Explorer', exact: true }).waitFor()
  await page.getByText(publicationId, { exact: true }).waitFor()
  await page.getByRole('button', { name: 'Logout', exact: true }).click()
  await page.getByRole('button', { name: 'Login', exact: true }).waitFor()
  assert.equal((await context.cookies()).length, 0)
  assert.equal((await context.request.get('http://127.0.0.1:5173/auth/me')).status(), 401)
  assert.equal((await context.request.get('http://127.0.0.1:5173/mo-option-premium-plane')).status(), 401)
  const again = await context.request.post('http://127.0.0.1:5173/auth/logout', {
    headers: { Origin: env.LAB_AUTH_ORIGIN },
  })
  assert.equal(again.status(), 204)
  console.log('PASS: real Chromium login -> Research Workspace -> Daily Data -> both MO pages -> Research Explorer -> logout; direct URL, reload and history')
  console.log(`Screenshots: ${screenshots}`)
  console.log('PASS: HttpOnly / SameSite Cookie; no JS token/storage; anonymous business gate; repeated logout')
  console.log(evidence.join('\n'))
} catch (error) {
  console.error(evidence.join('\n'))
  if (page) console.error(await page.locator('body').innerText().catch(() => 'Page unavailable'))
  throw error
} finally {
  await browser?.close()
  for (const child of processes.reverse()) {
    child.kill('SIGTERM')
    if (child.exitCode === null) await new Promise((done) => child.once('exit', done))
  }
  await rm(temporary, { recursive: true, force: true })
}
