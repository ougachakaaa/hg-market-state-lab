import { historicalBasisAcceptance } from './historical_basis_acceptance.mjs'
// Real browser -> Vite proxy -> FastAPI -> temporary SQLite. Only market public
// providers are deterministic fixtures; Auth, Cookie and CLI are real.
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdtemp, rm, mkdir, readdir, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'
import { polishAcceptance } from './futures_basis_polish_acceptance.mjs'

const root = fileURLToPath(new URL('../../', import.meta.url))
const temporary = await mkdtemp(resolve(tmpdir(), 'wp8b-online-'))
const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http',
  LAB_AUTH_ORIGIN: 'http://127.0.0.1:5173',
  LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'),
  LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'), LAB_FUTURES_BASIS_RUN_ROOT: resolve(temporary, 'runs') }
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
    'futures_basis_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', '8011', '--no-proxy-headers'])
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
    if (path.startsWith('/auth/') || path.startsWith('/api/research/futures-basis')) evidence.push(`${path} ${res.status()}`)
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
  await page.getByRole('menuitem', { name: '研究工作台', exact: true }).waitFor()
  const cookie = (await context.cookies()).find(value => value.name === 'lab_access_token')
  assert.ok(cookie?.httpOnly)
  assert.equal(cookie.sameSite, 'Strict')
  assert.equal(cookie.secure, false)
  assert.equal(await page.evaluate(() => document.cookie.includes('lab_access_token')), false)
  const output = resolve(process.argv[2] || '/tmp/wp8b-online-browser')
  await mkdir(output, { recursive: true })
  await page.getByRole('region', { name: '本地研究与离线工作流' }).getByRole('button', { name: '查看详情' }).nth(1).click()
  await page.getByRole('button', { name: '打开 Futures Basis Research', exact: true }).click()
  await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
  assert.equal(await page.getByRole('button', { name: '生成研究' }).isEnabled(), false)
  await page.getByRole('combobox', { name: '品种', exact: true }).click()
  await page.getByTitle('IM', { exact: true }).click()
  for (const [label, value] of [['开始日期', '2024-10-18'], ['结束日期', '2024-10-21']]) {
    await page.getByRole('textbox', { name: label, exact: true }).fill(value)
    await page.getByRole('textbox', { name: label, exact: true }).press('Enter')
  }
  assert.equal(evidence.filter(entry => entry.startsWith('/api/research/futures-basis/runs ')).length, 0)
  const acceptedResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/api/research/futures-basis/runs'))
  await page.getByRole('button', { name: '生成研究' }).click()
  const accepted = await acceptedResponse
  assert.equal(accepted.status(), 202)
  const firstId = (await accepted.json()).run_id
  const busyResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/api/research/futures-basis/runs'))
  await page.getByRole('button', { name: '生成研究' }).click()
  assert.equal((await busyResponse).status(), 409)
  await page.getByText(/BUSY：/).waitFor()
  await page.locator('#section-5').waitFor()
  await page.locator('#section-1 .js-plotly-plot .nsewdrag').first().waitFor()
  assert.ok(page.url().includes(`run_id=${firstId}`))
  for (let i = 0; i < 6; i++) assert.equal(await page.locator(`#section-${i}`).count(), 1)
  assert.equal(await page.getByText(/相邻 inputs.canonical.json/).count(), 0)
  const plots = page.locator('#section-1 .js-plotly-plot')
  assert.equal(await plots.count(), 3)
  assert.equal(await plots.first().locator('.legend .traces').count(), 4)
  assert.ok(states.includes('RUNNING'))
  assert.ok(states.includes('COMPLETED'))
  const presentationReport = await (await context.request.get(`http://127.0.0.1:5173/api/research/futures-basis/runs/${firstId}/report`)).json()
  await historicalBasisAcceptance(page, presentationReport.data, output)
  await page.screenshot({ path: resolve(output, 'online-report.png'), fullPage: true })
  await page.screenshot({ path: resolve(output, 'online-overview.png') })
  // An invalid future request must preserve the existing terminal report and URL.
  for (const [label, value] of [['开始日期', '2099-01-01'], ['结束日期', '2099-01-02']]) {
    await page.getByRole('textbox', { name: label, exact: true }).fill(value)
    await page.getByRole('textbox', { name: label, exact: true }).press('Enter')
  }
  assert.equal(evidence.filter(entry => entry.startsWith('/api/research/futures-basis/runs ')).length, 2)
  const rejected = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/api/research/futures-basis/runs'))
  await page.getByRole('button', { name: '生成研究' }).click()
  assert.equal((await rejected).status(), 400)
  await page.getByText(/FORM_ERROR：/).waitFor()
  assert.equal(await page.locator('#section-5').count(), 1)
  assert.ok(page.url().includes(firstId))
  await page.reload()
  await page.locator('#section-5').waitFor()
  assert.ok(page.url().includes(firstId))
  const againAccepted = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/api/research/futures-basis/runs'))
  // Refresh restores the immutable run but deliberately leaves new query controls empty.
  await page.getByRole('combobox', { name: '品种', exact: true }).click()
  await page.getByTitle('IM', { exact: true }).click()
  for (const [label, value] of [['开始日期', '2024-10-18'], ['结束日期', '2024-10-21']]) {
    await page.getByRole('textbox', { name: label, exact: true }).fill(value)
    await page.getByRole('textbox', { name: label, exact: true }).press('Enter')
  }
  await page.getByRole('button', { name: '生成研究' }).click()
  const secondId = (await (await againAccepted).json()).run_id
  assert.notEqual(secondId, firstId)
  await page.waitForFunction(id => new URLSearchParams(location.search).get('run_id') === id, secondId)
  await page.locator('#section-5').waitFor()
  await page.goBack()
  await page.locator('#section-5').waitFor()
  assert.ok(page.url().includes(firstId))
  await page.goForward()
  await page.locator('#section-5').waitFor()
  assert.ok(page.url().includes(secondId))
  // Deliver the POST to the real backend, then lose its response in this browser.
  // The prior report must survive and the client must not create another Run.
  const runDirectories = () => readdir(env.LAB_FUTURES_BASIS_RUN_ROOT)
  assert.equal((await runDirectories()).length, 2)
  let lostAccepted
  await page.route('**/api/research/futures-basis/runs', async route => {
    assert.equal(route.request().method(), 'POST')
    const response = await route.fetch()
    assert.equal(response.status(), 202)
    lostAccepted = await response.json()
    await route.abort('failed')
  })
  // Explicitly select the synthetic candidate after history restoration.
  await page.getByRole('combobox', { name: '品种', exact: true }).click()
  await page.locator('.ant-select-item-option[title="IM"]').click()
  for (const [label, value] of [['开始日期', '2024-10-18'], ['结束日期', '2024-10-21']]) {
    await page.getByRole('textbox', { name: label, exact: true }).fill(value)
    await page.getByRole('textbox', { name: label, exact: true }).press('Enter')
  }
  await page.getByRole('button', { name: '生成研究' }).click()
  await page.getByText(/网络响应丢失。提交结果可能已被服务器接受/).waitFor()
  await page.waitForTimeout(2000)
  assert.ok(lostAccepted?.run_id)
  assert.equal((await runDirectories()).length, 3)
  assert.ok(page.url().includes(secondId))
  assert.equal(await page.locator('#section-5').count(), 1)
  await page.unroute('**/api/research/futures-basis/runs')
  assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0])
  await polishAcceptance(page, context, output, secondId)
  await page.getByRole('button', { name: '退出登录', exact: true }).click()
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  assert.equal((await context.cookies()).length, 0)
  assert.equal((await context.request.get('http://127.0.0.1:5173/auth/me')).status(), 401)
  assert.equal((await context.request.get(`http://127.0.0.1:5173/api/research/futures-basis/runs/${secondId}/report`)).status(), 401)
  assert.equal(await page.locator('#section-0').count(), 0)
  const again = await context.request.post('http://127.0.0.1:5173/auth/logout', {
    headers: { Origin: env.LAB_AUTH_ORIGIN },
  })
  assert.equal(again.status(), 204)
  assert.deepEqual(errors, [])
  await writeFile(resolve(output, 'http-evidence.json'), JSON.stringify({ status: 'PASS', evidence, states, errors, lostAccepted, runsAfterLostResponse: 3 }, null, 2))
  console.log('PASS: real Chromium -> Vite -> FastAPI -> synthetic public services; login -> catalog -> Generate -> poll -> Plotly report -> refresh -> Back/Forward -> logout')
  console.log('PASS: HttpOnly / SameSite Cookie; no JS token/storage; anonymous business gate; repeated logout')
  console.log(evidence.join('\n'))
} catch (error) {
  console.error(evidence.join('\n'))
  if (page) { await page.screenshot({ path: '/tmp/wp8b-online-error.png', fullPage: true }).catch(() => {}); console.error(await page.locator('body').innerText().catch(() => 'Page unavailable')) }
  throw error
} finally {
  await browser?.close()
  for (const child of processes.reverse()) {
    child.kill('SIGTERM')
    if (child.exitCode === null) await new Promise((done) => child.once('exit', done))
  }
  await rm(temporary, { recursive: true, force: true })
}
