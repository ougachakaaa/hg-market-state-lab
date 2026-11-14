import { onlineHarness, unusedPort, observe } from './online_harness.mjs'
import { historicalBasisAcceptance } from './historical_basis_acceptance.mjs'
// Real browser -> Vite proxy -> FastAPI -> temporary SQLite. Only market public
// providers are deterministic fixtures; Auth, Cookie and CLI are real.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdtemp, rm, mkdir, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'
import { polishAcceptance } from './futures_basis_polish_acceptance.mjs'

const root = fileURLToPath(new URL('../../../', import.meta.url))
const temporary = await mkdtemp(resolve(tmpdir(), 'wp8b-online-'))
const backendPort = await unusedPort()
let frontendPort = await unusedPort()
while (frontendPort === backendPort) frontendPort = await unusedPort()
const origin = `http://127.0.0.1:${frontendPort}`
const output = resolve(process.argv[2] || resolve(temporary, 'evidence'))
const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http',
  LAB_AUTH_ORIGIN: origin, LAB_BROWSER_API_ORIGIN: `http://127.0.0.1:${backendPort}`,
  LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'),
  LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'), LAB_FUTURES_BASIS_RUN_ROOT: resolve(temporary, 'runs') }
const { start, ready, save, stop } = onlineHarness(env, root, output)
let drain = async () => {}
let browser
let page
const evidence = []
const states = []
const errors = []
function cli(...args) {
  const result = spawnSync('poetry', ['run', 'lab', 'auth', ...args], { cwd: root, env, encoding: 'utf8' })
  assert.equal(result.status, 0, result.stderr)
  return result.stdout
}
try {
  const backend = start('poetry', ['run', 'python', '-m', 'uvicorn', '--app-dir', 'ui_web/tests/fixtures',
    'futures_basis_browser_app:create_app', '--factory', '--host', '127.0.0.1', '--port', String(backendPort), '--no-proxy-headers'])
  const frontend = start(process.execPath, ['node_modules/vite/bin/vite.js', '--config', 'tests/config/vite.browser.config.ts', '--strictPort', '--port', String(frontendPort)], resolve(root, 'ui_web'))
  await ready(`${env.LAB_BROWSER_API_ORIGIN}/auth/me`, backend, 401)
  await ready(`${origin}/`, frontend, 200)
  browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  const context = await browser.newContext()
  page = await context.newPage()
  page.setDefaultTimeout(15000)
  drain = observe(page, evidence, states, errors)
  const anonymous = await context.request.get(`${origin}/mo-option-chain`)
  assert.equal(anonymous.status(), 401)
  await page.goto(`${origin}/`)
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'MO Option Chain', exact: true }).count(), 0)
  assert.equal(evidence.some((entry) => entry.includes('/mo-option')), false)
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
  await mkdir(output, { recursive: true })
  await page.getByRole('region', { name: '本地研究与离线工作流' }).getByRole('button', { name: '查看详情' }).nth(1).click()
  await page.getByRole('button', { name: '进入历史基差研究', exact: true }).click()
  await page.getByRole('heading', { name: 'Futures Basis Research', exact: true }).waitFor()
  assert.equal(await page.getByRole('button', { name: '生成研究' }).isEnabled(), false)
  await page.getByRole('combobox', { name: '品种', exact: true }).click()
  await page.getByTitle('IM', { exact: true }).click()
  for (const [label, value] of [['开始日期', '2024-10-18'], ['结束日期', '2024-10-21']]) {
    await page.getByRole('textbox', { name: label, exact: true }).fill(value)
    await page.getByRole('textbox', { name: label, exact: true }).press('Enter')
  }
  assert.equal(evidence.filter(entry => entry.startsWith('POST /api/research/futures-basis/runs ')).length, 0)
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
  const presentationReport = await (await context.request.get(`${origin}/api/research/futures-basis/runs/${firstId}/report`)).json()
  await historicalBasisAcceptance(page, presentationReport.data, output)
  await page.screenshot({ path: resolve(output, 'online-report.png'), fullPage: true })
  await page.screenshot({ path: resolve(output, 'online-overview.png') })
  // Verify the Web-only today gate using a blocked public assessment without
  // acquiring Source data or creating a Run.
  await page.route('**/api/research/futures-basis/preflight', async route => {
    const r = await route.fetch()
    assert.equal(r.status(), 200, `Preflight fetch: ${r.status()}`)
    const result = await r.json()
    result.submission = 'blocked'; result.today_gate = 'not_ready'
    for (const item of result.dependencies) if (item.dependency === 'futures') {
      item.state = 'needs_fetch'; item.reason_code = 'cache_incomplete'
      item.message = '本地数据覆盖不完整，正式执行可能需要获取数据。'
    }
    await route.fulfill({ response: r, json: result })
  })
  await page.getByRole('button', { name: '重新检查输入' }).click()
  await page.getByText('本地当日数据未就绪，请先完成数据准备，再重新检查。', { exact: true }).waitFor()
  assert.equal(await page.getByRole('button', { name: '生成研究' }).isEnabled(), false)
  assert.equal(evidence.filter(entry => entry.startsWith('POST /api/research/futures-basis/runs ')).length, 2)
  await page.unroute('**/api/research/futures-basis/preflight')
  // An invalid future request must preserve the existing terminal report and URL.
  for (const [label, value] of [['开始日期', '2099-01-01'], ['结束日期', '2099-01-02']]) {
    await page.getByRole('textbox', { name: label, exact: true }).fill(value)
    await page.getByRole('textbox', { name: label, exact: true }).press('Enter')
  }
  assert.equal(evidence.filter(entry => entry.startsWith('POST /api/research/futures-basis/runs ')).length, 2)
  await page.getByText('输入检查失败，请重新检查').waitFor()
  assert.equal(await page.getByRole('button', { name: '生成研究' }).isEnabled(), false)
  assert.equal(evidence.filter(entry => entry.startsWith('POST /api/research/futures-basis/runs ')).length, 2)
  assert.equal(await page.locator('#section-5').count(), 1)
  assert.ok(page.url().includes(firstId))
  await page.reload()
  await page.locator('#section-5').waitFor()
  assert.ok(page.url().includes(firstId))
  const againAccepted = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/api/research/futures-basis/runs'))
  // Refresh restores the immutable run; only the end date defaults to Shanghai today.
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
  const runCount = () => {
    const result = spawnSync('poetry', ['run', 'python', '-c',
      'import sqlite3,sys; from pathlib import Path; c=sqlite3.connect(Path(sys.argv[1]).as_uri()+"?mode=ro",uri=True); print(c.execute("SELECT count(*) FROM runs").fetchone()[0]); c.close()',
      resolve(env.LAB_FUTURES_BASIS_RUN_ROOT, 'runs.sqlite3')], { cwd: root, env, encoding: 'utf8' })
    assert.equal(result.status, 0, result.stderr)
    return Number(result.stdout.trim())
  }
  assert.equal(runCount(), 2)
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
  // Bounded observation window: detect forbidden automatic POST replay.
  await page.waitForTimeout(2000)
  assert.ok(lostAccepted?.run_id)
  assert.equal(runCount(), 3)
  assert.ok(page.url().includes(secondId))
  assert.equal(await page.locator('#section-5').count(), 1)
  await page.unroute('**/api/research/futures-basis/runs')
  assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0])
  await polishAcceptance(page, context, output, secondId, origin)
  await page.getByRole('button', { name: '退出登录', exact: true }).click()
  await page.getByRole('button', { name: '登录', exact: true }).waitFor()
  assert.equal((await context.cookies()).length, 0)
  assert.equal((await context.request.get(`${origin}/auth/me`)).status(), 401)
  assert.equal((await context.request.get(`${origin}/api/research/futures-basis/runs/${secondId}/report`)).status(), 401)
  assert.equal(await page.locator('#section-0').count(), 0)
  const again = await context.request.post(`${origin}/auth/logout`, {
    headers: { Origin: env.LAB_AUTH_ORIGIN },
  })
  assert.equal(again.status(), 204)
  await drain()
  assert.deepEqual(errors, [])
  await writeFile(resolve(output, 'http-evidence.json'), JSON.stringify({ status: 'PASS', evidence, states, errors, lostAccepted, runsAfterLostResponse: 3 }, null, 2))
  console.log('PASS: real Chromium -> Vite -> FastAPI -> synthetic public services; login -> catalog -> Generate -> poll -> Plotly report -> refresh -> Back/Forward -> logout')
  console.log('PASS: HttpOnly / SameSite Cookie; no JS token/storage; anonymous business gate; repeated logout')
  console.log(evidence.join('\n'))
} catch (error) {
  await mkdir(output, { recursive: true })
  if (page) await page.screenshot({ path: resolve(output, 'failure.png'), fullPage: true }).catch(() => {})
  throw error
} finally {
  try {
    await drain()
    await save(evidence, errors)
    console.log(`Diagnostics: ${output}`)
  } finally {
    try { await browser?.close() } finally {
      await stop()
      // Keep evidence, remove only this run's authentication and Run Store.
      await rm(env.LAB_AUTH_DB_PATH, { force: true })
      await rm(env.LAB_FUTURES_BASIS_RUN_ROOT, { recursive: true, force: true })
    }
  }
}
