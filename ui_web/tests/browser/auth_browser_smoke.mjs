import { neutralDarkAcceptance } from './neutral_dark_acceptance.mjs'
// Real browser -> Vite proxy -> FastAPI -> temporary SQLite. Only market public
// providers are deterministic fixtures; Auth, Cookie and CLI are real.
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const root = fileURLToPath(new URL('../../../', import.meta.url))
const temporary = await mkdtemp(resolve(tmpdir(), 'g3-auth-'))
const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http',
  LAB_AUTH_ORIGIN: 'http://127.0.0.1:5173',
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
  for (const port of [8011, 5173]) {
    const server = createServer()
    await new Promise((done, reject) => server.once('error', reject).listen(port, '127.0.0.1', done))
    await new Promise((done) => server.close(done))
  }
  const backend = start('poetry', ['run', 'python', '-m', 'uvicorn', '--app-dir', 'ui_http/tests',
    'http_support.auth_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', '8011', '--no-proxy-headers'])
  const frontend = start(process.execPath, ['node_modules/vite/bin/vite.js', '--config', 'tests/config/vite.browser.config.ts', '--strictPort'], resolve(root, 'ui_web'))
  await ready('http://127.0.0.1:8011/auth/me', backend, 401)
  await ready('http://127.0.0.1:5173/', frontend, 200)
  browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  const screenshots = await mkdtemp(resolve(tmpdir(), 's2-wp1-shell-'))
  const context = await browser.newContext()
  page = await context.newPage()
  page.setDefaultTimeout(15000)
  page.on('response', (res) => {
    const path = new URL(res.url()).pathname
    if (path.startsWith('/auth/') || path.startsWith('/mo-option')) evidence.push(`${path} ${res.status()}`)
  })
  const anonymous = await context.request.get('http://127.0.0.1:5173/mo-option-chain')
  assert.equal(anonymous.status(), 401)
  await page.goto('http://127.0.0.1:5173/')
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  for (const [width, height] of [[1440, 900], [1024, 768]]) {
    await page.setViewportSize({ width, height })
    assert.ok(await page.evaluate(() => {
      const background = getComputedStyle(document.elementFromPoint(1, 1)).backgroundColor
      const channels = background.match(/[\d.]+/g)?.map(Number)
      return channels?.length >= 3 && channels.slice(0, 3).every(value => value < 80)
        && (channels.length === 3 || channels[3] > 0)
    }), 'Authentication page has an opaque dark backdrop')
    assert.ok(await page.evaluate(() => document.documentElement.scrollHeight <= innerHeight), 'Login fits the viewport vertically')
    await page.screenshot({ path: resolve(screenshots, `login-${width}.png`) })
  }
  await page.setViewportSize({ width: 1440, height: 900 })
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
  if (!(await page.getByRole('menuitem', { name: '数据总览', exact: true }).isVisible())) await page.getByRole('menuitem', { name: '日常数据', exact: true }).click()
  await page.getByRole('menuitem', { name: '数据总览', exact: true }).click()
  await page.getByRole('button', { name: '打开 MO Option Chain', exact: true }).click()
  await page.getByRole('heading', { name: 'MO 期权链', exact: true }).waitFor()
  const cookie = (await context.cookies()).find((value) => value.name === 'lab_access_token')
  assert.ok(cookie?.httpOnly)
  assert.equal(cookie.sameSite, 'Strict')
  assert.equal(cookie.secure, false)
  assert.equal(await page.evaluate(() => document.cookie.includes('lab_access_token')), false)
  assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0])
  await page.getByLabel('观察日期', { exact: true }).fill('2026-09-17')
  await page.getByLabel('观察日期', { exact: true }).press('Enter')
  await page.getByRole('region', { name: '期权链结果', exact: true }).waitFor()
  await page.locator('.ant-menu-title-content').getByText('MO Premium Plane', { exact: true }).click()
  await page.getByLabel('观察日期', { exact: true }).fill('2026-09-17')
  await page.getByLabel('观察日期', { exact: true }).press('Enter')
  await page.getByRole('region', { name: 'Premium plane results', exact: true }).waitFor()
  await page.waitForLoadState('networkidle')
  await page.reload()
  await page.getByRole('heading', { name: 'MO 年化权利金平面', exact: true }).waitFor()

  const surfaces = [
    ['/research', '研究总览', '研究', '研究总览'],
    ['/research/publications', '研究结果浏览', '研究', 'Research Explorer'],
    ['/research/futures-basis', 'Futures Basis Research', '研究', '历史基差研究'],
    ['/data', '数据总览', '日常数据', '数据总览'],
    ['/data/mo-option-chain', 'MO 期权链', '日常数据', 'MO Option Chain'],
    ['/data/mo-premium-plane', 'MO 年化权利金平面', '日常数据', 'MO Premium Plane'],
    ['/backtesting', '期货展期做多回测', null, '回测'],
  ]
  for (const [width, height] of [[1440, 900], [1024, 768]]) {
    await page.setViewportSize({ width, height })
    for (const [path, heading, group, selectedLabel] of surfaces) {
      await page.goto(`http://127.0.0.1:5173${path}`)
      await page.getByRole('heading', { name: heading, exact: true }).waitFor()
      assert.equal(await page.getByRole('heading', { name: heading, exact: true }).count(), 1, 'One primary page heading')
      const collapsed = width < 1200
      await page.getByRole('button', { name: collapsed ? '展开导航' : '折叠导航', exact: true }).waitFor()
      if (collapsed && group) await page.getByRole('menuitem', { name: group, exact: true }).click()
      if (path === '/research') {
        // During the popup animation its container can briefly have zero bounds.
        // Wait on the actual leaf below instead of re-filtering the container.
        const navigation = collapsed ? page.locator('.ant-menu-submenu-popup') : page.getByRole('menu', { name: '业务导航' })
        await navigation.getByRole('menuitem', { name: 'Research Explorer', exact: true }).waitFor({ state: 'visible' })
        assert.equal(await navigation.getByRole('menuitem', { name: 'Research Explorer', exact: true }).count(), 1)
        assert.equal(await navigation.getByRole('menuitem', { name: 'DESCRIPTIVE RESEARCH', exact: true }).count(), 0)
        await navigation.getByText('DESCRIPTIVE RESEARCH', { exact: true }).click()
        assert.equal(new URL(page.url()).pathname, '/research')
        await page.screenshot({ path: resolve(screenshots, `research-navigation-${collapsed ? 'collapsed' : 'expanded'}-${width}.png`) })
      }
      await page.locator('.ant-menu-item-selected').waitFor({ state: 'visible' })
      assert.equal(await page.locator('.ant-menu-item-selected').count(), 1, `${path}: one selected leaf`)
      assert.ok((await page.getByRole('menuitem', { name: selectedLabel, exact: true }).getAttribute('class')).split(' ').includes('ant-menu-item-selected'), `${path}: the selected leaf matches the route`)
      if (collapsed && group) {
        await page.getByRole('menuitem', { name: group, exact: true }).click()
        await page.locator('.ant-menu-submenu-popup').waitFor({ state: 'hidden' })
      }
      assert.equal(await page.locator('.ant-layout-header h1, .ant-layout-header h2, .ant-layout-header h3').count(), 0, 'Shell header has no duplicate title')
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${path}: no document overflow`)
      await page.screenshot({ path: resolve(screenshots, `${path.slice(1).replaceAll('/', '-')}-${width}.png`), fullPage: true })
      await page.getByRole('button', { name: collapsed ? '展开导航' : '折叠导航', exact: true }).click()
      await page.getByRole('button', { name: collapsed ? '折叠导航' : '展开导航', exact: true }).waitFor()
      assert.equal(new URL(page.url()).pathname, path, 'Collapse does not navigate')
      if (path === '/research') {
        if (!collapsed) {
          await page.getByRole('menuitem', { name: '研究', exact: true }).click()
          await page.locator('.ant-menu-submenu-popup:visible').waitFor()
        }
        await page.screenshot({ path: resolve(screenshots, `research-navigation-${collapsed ? 'expanded' : 'collapsed'}-${width}.png`), animations: 'disabled' })
      }
    }
  }
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('http://127.0.0.1:5173/research')
  await page.getByRole('menuitem', { name: '研究总览', exact: true }).waitFor()
  await page.getByRole('menuitem', { name: '日常数据', exact: true }).click()
  await page.getByRole('menuitem', { name: '数据总览', exact: true }).click()
  await page.getByRole('button', { name: '打开 MO Premium Plane', exact: true }).click()
  await page.goBack()
  await page.getByRole('heading', { name: '数据总览', exact: true }).waitFor()
  await page.goForward()
  await page.getByRole('heading', { name: 'MO 年化权利金平面', exact: true }).waitFor()
  await page.getByRole('link', { name: '日常数据', exact: true }).click()
  await page.getByRole('heading', { name: '数据总览', exact: true }).waitFor()
  assert.equal(new URL(page.url()).pathname, '/data', 'Breadcrumb returns to its overview')
  await neutralDarkAcceptance(page, screenshots)
  console.log(`PASS: WP1 routes, collapse, history and overflow at both desktop sizes; screenshots: ${screenshots}`)
  await page.getByRole('button', { name: '退出登录', exact: true }).click()
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  assert.equal((await context.cookies()).length, 0)
  assert.equal((await context.request.get('http://127.0.0.1:5173/auth/me')).status(), 401)
  assert.equal((await context.request.get('http://127.0.0.1:5173/mo-option-premium-plane')).status(), 401)
  const again = await context.request.post('http://127.0.0.1:5173/auth/logout', {
    headers: { Origin: env.LAB_AUTH_ORIGIN },
  })
  assert.equal(again.status(), 204)
  console.log('PASS: real Chromium registration -> CLI approval -> login -> both MO fixture results -> reload -> logout')
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
