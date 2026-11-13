// Opt-in real-market HTTP + visible Windows Chrome acceptance. No fake services.
// Run from ui_web: node tests/browser/wp8_real_acceptance.mjs /absolute/external/root
// The aggregate gate is PASS only when Python, offline reproduction, HTTP and Windows
// Chrome all pass in this artifact round; every other outcome exits nonzero.
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { randomBytes } from 'node:crypto'
import { mkdir, readFile, writeFile, readdir, rm, stat } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import Ajv2020 from 'ajv/dist/2020.js'
import { chromium } from 'playwright'
import {
  FAIL,
  NOT_RUN,
  PASS,
  classifyHttpAcceptance,
  classifyOverall,
  classifyPythonAcceptance,
  classifyReproduction,
  classifyWindowsAcceptance,
  combineStatuses,
  exitCode,
} from './wp8_acceptance_status.mjs'

const windows = process.argv[2] === '--windows'
const artifactRoot = resolve(process.argv[windows ? 3 : 2] || '/tmp/w2-wp8-real-im')
const origin = 'http://127.0.0.1:5173'
const base = `${origin}/api/backtesting/futures-roll`
const profiles = ['expiry_to_M1_v1', 'expiry_to_Q1_v1']
const body = profile => ({ product_code: 'IM', start_date: '2024-01-01', end_date: '2026-10-30', strategy_profile: profile })
const save = (name, value) => writeFile(resolve(artifactRoot, name), JSON.stringify(value, null, 2) + '\n')
const pause = ms => new Promise(done => setTimeout(done, ms))

async function readArtifact(name) {
  try {
    return JSON.parse(await readFile(resolve(artifactRoot, name), 'utf8'))
  } catch {
    return null
  }
}

async function removeArtifacts(names) {
  await Promise.all(names.map(name => rm(resolve(artifactRoot, name), { force: true })))
}

async function hasArtifact(name) {
  try {
    return (await stat(resolve(artifactRoot, name))).size > 0
  } catch {
    return false
  }
}

async function windowsBrowser() {
  let input = ''
  for await (const chunk of process.stdin) input += chunk
  const credentials = JSON.parse(input)
  const report = { kind: 'actual_windows_chrome_real_market', status: 'RUNNING', profiles: {}, errors: [] }
  // Invalidate an earlier PASS before attempting any browser execution.
  await save('windows-acceptance.json', report)
  let browser
  let page
  try {
    browser = await chromium.launch({ headless: false,
      executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' })
    report.version = browser.version()
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
    page = await context.newPage()
    page.setDefaultTimeout(60000)
    page.on('pageerror', error => report.errors.push(error.name))
    let posts = 0
    page.on('request', request => { if (request.method() === 'POST' && request.url() === `${base}/runs`) posts++ })
    const start = performance.now()
    await page.goto(origin)
    await page.getByLabel('用户名', { exact: true }).fill(credentials.username)
    await page.getByLabel('密码', { exact: true }).fill(credentials.password)
    await page.getByRole('button', { name: '登录', exact: true }).click()
    await page.getByRole('menuitem', { name: '回测', exact: true }).click()
    report.login_navigation_seconds = (performance.now() - start) / 1000
    const cookie = (await context.cookies()).find(value => value.name === 'lab_access_token')
    assert.ok(cookie?.httpOnly && cookie.sameSite === 'Strict')
    const ids = []
    for (const profile of profiles) {
      await page.getByRole('combobox', { name: '产品', exact: true }).click()
      await page.locator('.ant-select-item-option[title="IM"]').click()
      for (const [label, value] of [['开始日期', '2024-01-01'], ['结束日期', '2026-10-30']]) {
        const field = page.getByRole('textbox', { name: label, exact: true })
        await field.fill(value); await field.press('Enter')
      }
      await page.getByRole('combobox', { name: '策略', exact: true }).click()
      await page.locator(`.ant-select-item-option[title="${profile}"]`).click()
      await page.getByText('ready=true', { exact: true }).waitFor()
      assert.equal(posts, ids.length, 'preflight and edits never submit')
      const acceptedResponse = page.waitForResponse(r => r.request().method() === 'POST' && r.url() === `${base}/runs`)
      const started = performance.now()
      await page.getByRole('button', { name: /开始回测/ }).click()
      const response = await acceptedResponse
      assert.equal(response.status(), 202)
      const accepted = await response.json()
      assert.equal(accepted.status, 'PENDING')
      ids.push(accepted.run_id)
      await page.getByTestId('backtest-result').waitFor({ timeout: 300000 })
      await page.locator('.js-plotly-plot .nsewdrag').first().waitFor()
      const renderSeconds = (performance.now() - started) / 1000
      const res = await context.request.get(`${base}/runs/${accepted.run_id}/result`)
      assert.equal(res.status(), 200)
      const payload = await res.json()
      assert.equal(payload.data.request.strategy_profile, profile)
      const expected = JSON.parse(await readFile(resolve(artifactRoot, `${profile}-result.json`), 'utf8'))
      assert.deepEqual(payload.data, expected)
      assert.equal(await page.locator('.js-plotly-plot').count(), 2)
      for (const [i, name] of ['returns', 'drawdown'].entries()) {
        const plot = page.locator('.js-plotly-plot').nth(i)
        const observed = await plot.evaluate(el => ({ ys: el.data.filter(t => t.type === 'scatter' && t.showlegend !== false).map(t => t.y), events: el.layout.shapes.length }))
        for (const layer of payload.data.views[name].layers) {
          assert.ok(observed.ys.some(ys => JSON.stringify(ys) === JSON.stringify(layer.layer.data.map(m => m.y))))
        }
        assert.equal(observed.events, payload.data.views[name].events.length)
        await plot.scrollIntoViewIfNeeded()
        const drag = plot.locator('.nsewdrag')
        const initial = await plot.evaluate(el => JSON.stringify(el._fullLayout.xaxis.range))
        const box = await drag.boundingBox()
        await page.mouse.move(box.x + box.width * .2, box.y + box.height * .3)
        await page.mouse.down()
        await page.mouse.move(box.x + box.width * .7, box.y + box.height * .8, { steps: 12 })
        await page.mouse.up()
        await page.waitForFunction(({ index, initialRange }) => JSON.stringify(document.querySelectorAll('.js-plotly-plot')[index]._fullLayout.xaxis.range) !== initialRange, { index: i, initialRange: initial })
        const zoomed = await plot.evaluate(el => JSON.stringify(el._fullLayout.xaxis.range))
        await plot.locator('[data-title="Pan"]').click({ force: true })
        await page.mouse.move(box.x + box.width * .5, box.y + box.height * .5)
        await page.mouse.down()
        await page.mouse.move(box.x + box.width * .65, box.y + box.height * .5, { steps: 12 })
        await page.mouse.up()
        await page.waitForFunction(({ index, previous }) => JSON.stringify(document.querySelectorAll('.js-plotly-plot')[index]._fullLayout.xaxis.range) !== previous, { index: i, previous: zoomed })
        await plot.locator('[data-title="Reset axes"]').click({ force: true })
        await page.waitForFunction(({ index, initialRange }) => JSON.stringify(document.querySelectorAll('.js-plotly-plot')[index]._fullLayout.xaxis.range) === initialRange, { index: i, initialRange: initial })
      }
      await page.getByRole('cell', { name: payload.data.trades[0].contract_code, exact: true }).first().waitFor()
      for (const [title, rows] of [['交易记录 · Trades', payload.data.trades], ['展期记录 · Rolls', payload.data.rolls]]) {
        const card = page.locator('.ant-card').filter({ hasText: title })
        const pages = card.locator('.ant-pagination-item')
        if (await pages.count()) await pages.last().click()
        const last = rows.at(-1)
        await card.getByRole('cell', { name: last.contract_code ?? last.new_contract_code, exact: true }).last().waitFor()
      }
      await page.getByText('研究证据与限制 · Evidence / Limitations', { exact: true }).click()
      await page.getByText(payload.data.evidence.input_fingerprint, { exact: true }).waitFor()
      await page.screenshot({ path: resolve(artifactRoot, `windows-${profile}.png`), fullPage: true })
      const postCount = posts
      await page.reload(); await page.getByTestId('backtest-result').waitFor()
      assert.equal(posts, postCount)
      assert.ok(page.url().includes(accepted.run_id))
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 2))
      report.profiles[profile] = { status: 'PASS', run_id: accepted.run_id,
        fingerprint: payload.data.evidence.input_fingerprint, seconds: (performance.now() - started) / 1000,
        result_render_seconds: renderSeconds, tables_last_page: true,
        charts: 'exact_producer_values_and_zoom_pan_reset', refresh_without_submit: true }
      await save('windows-acceptance.json', report)
    }
    await page.goBack(); await page.getByTestId('backtest-result').waitFor()
    assert.ok(page.url().includes(ids[0]))
    await page.goForward(); await page.getByTestId('backtest-result').waitFor()
    assert.ok(page.url().includes(ids[1]))
    await page.goto(`${origin}/backtesting?run_id=${ids[0]}`)
    await page.getByTestId('backtest-result').waitFor()
    assert.equal(posts, 2)
    await page.getByRole('button', { name: '退出登录', exact: true }).click()
    await page.getByRole('button', { name: '登录', exact: true }).waitFor()
    assert.equal(await page.getByTestId('backtest-result').count(), 0)
    assert.equal((await context.request.get(`${base}/runs/${ids[0]}/result`)).status(), 401)
    assert.equal(report.errors.length, 0)
    report.status = PASS
  } catch (error) {
    // Do not persist raw browser exception text: it can contain local paths.
    report.status = browser ? FAIL : NOT_RUN
    report.reason = browser ? 'browser_acceptance_failed' : 'windows_chrome_unavailable'
    report.failure = { name: error.name, phase: Object.keys(report.profiles).length }
    if (browser && page) {
      await page.screenshot({ path: resolve(artifactRoot, 'windows-failure.png'), fullPage: true }).catch(() => {})
    }
  } finally {
    await save('windows-acceptance.json', report)
    if (browser) await browser.close()
  }
  process.exitCode = exitCode(report.status)
}

async function orchestrate() {
  const root = fileURLToPath(new URL('../../../', import.meta.url))
  assert.ok(artifactRoot !== resolve(root) && !artifactRoot.startsWith(`${resolve(root)}/`), 'artifacts_must_be_outside_repository')
  await mkdir(artifactRoot, { recursive: true })
  const temporary = resolve(artifactRoot, 'private-runtime')
  await mkdir(temporary, { recursive: true, mode: 0o700 })
  const env = { ...process.env, LAB_AUTH_MODE: 'loopback-http', LAB_AUTH_ORIGIN: origin,
    LAB_AUTH_JWT_SECRET: randomBytes(32).toString('base64url'),
    LAB_AUTH_DB_PATH: resolve(temporary, 'auth.sqlite3'),
    LAB_BACKTESTING_RUN_ROOT: resolve(temporary, 'runs'),
    LAB_FUTURES_BASIS_RUN_ROOT: resolve(temporary, 'research-runs') }
  const children = []
  const runId = randomBytes(16).toString('hex')
  const stages = { python: null, reproduction: null, http: null, windows: null }
  const report = {
    kind: 'actual_acceptance_gate',
    status: NOT_RUN,
    run_id: runId,
    generated_at: new Date().toISOString(),
    stages,
    profiles: {},
    privacy: {},
  }
  let currentStage = 'python'
  function start(command, args, cwd = root) {
    const child = spawn(command, args, { cwd, env, stdio: ['ignore', 'pipe', 'pipe'] })
    children.push(child)
    // Log deliberately excludes request bodies, headers, credentials and exception text.
    child.stdout.resume(); child.stderr.resume()
    return child
  }
  async function ready(url, child, status) {
    for (let i = 0; i < 120; i++) {
      if (child.exitCode !== null) throw new Error('server_start_failed')
      try { if ((await fetch(url)).status === status) return } catch { /* startup */ }
      await pause(250)
    }
    throw new Error('server_start_timeout')
  }
  function cli(...args) {
    const result = spawnSync('poetry', ['run', 'lab', 'auth', ...args], { cwd: root, env, encoding: 'utf8' })
    assert.equal(result.status, 0, 'auth_cli_failed')
    return result.stdout
  }
  async function provision(username) {
    const credentials = { username, password: randomBytes(24).toString('base64url') }
    const p = spawnSync('poetry', ['run', 'python', '-c',
      'import json,sys; from ui_http.auth import create_service; create_service().register(**json.load(sys.stdin))'],
    { cwd: root, env, input: JSON.stringify(credentials), encoding: 'utf8' })
    assert.equal(p.status, 0, 'auth_register_failed')
    const user = cli('pending').trim().split('\n').map(line => line.split('\t')).find(parts => parts[1] === username)
    assert.ok(user, 'pending_user_missing')
    cli('approve', user[0])
    return credentials
  }
  async function login(credentials) {
    const response = await fetch(`${origin}/auth/login`, { method: 'POST', headers: {
      Origin: origin, 'Content-Type': 'application/json' }, body: JSON.stringify(credentials) })
    assert.equal(response.status, 200)
    return response.headers.get('set-cookie').split(';')[0]
  }
  async function runWindowsStage(credentials) {
    await removeArtifacts(['windows-acceptance.json', 'windows-failure.png',
      ...profiles.map(profile => `windows-${profile}.png`)])
    function winPath(path) {
      const result = spawnSync('wslpath', ['-w', path], { encoding: 'utf8' })
      return result.status === 0 ? result.stdout.trim() : ''
    }
    const scriptPath = winPath(fileURLToPath(import.meta.url))
    const rootPath = winPath(artifactRoot)
    if (!scriptPath || !rootPath) {
      await save('windows-acceptance.json', { status: NOT_RUN, reason: 'wsl_interop_unavailable' })
      return NOT_RUN
    }
    // Windows Node consumes the shared pure-JS Playwright package; Chrome is Windows.
    const command = `& node.exe '${scriptPath.replaceAll("'", "''")}' --windows '${rootPath.replaceAll("'", "''")}'`
    const child = spawn('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', command], { stdio: ['pipe', 'pipe', 'pipe'] })
    children.push(child)
    child.stdin.on('error', () => { /* missing Windows command; classified below */ })
    child.stdin.end(JSON.stringify(credentials))
    child.stdout.resume(); child.stderr.resume()
    const code = await new Promise(done => {
      child.once('error', () => done(null)); child.once('exit', done)
    })
    report.windows_process_exit = code
    let windowsReport = await readArtifact('windows-acceptance.json')
    if (!windowsReport) {
      await save('windows-acceptance.json', { status: NOT_RUN, reason: 'windows_automation_unavailable' })
      windowsReport = { status: NOT_RUN }
    }
    const screenshots = await Promise.all(profiles.map(profile => hasArtifact(`windows-${profile}.png`)))
    return classifyWindowsAcceptance(windowsReport, { processExit: code, screenshots, profiles })
  }

  try {
    // Stale HTTP/Windows artifacts are removed before any stage can claim a result.
    await removeArtifacts(['http-acceptance.json', 'windows-acceptance.json', 'windows-failure.png',
      ...profiles.flatMap(profile => [`http-${profile}-preflight.json`, `http-${profile}-result.json`, `windows-${profile}.png`])])
    await save('http-acceptance.json', { ...report, status: NOT_RUN, reason: 'acceptance_not_finished' })

    const pythonReport = await readArtifact('python-acceptance.json')
    stages.python = classifyPythonAcceptance(pythonReport, profiles)
    const reproductionReport = await readArtifact('offline-reproduction.json')
    stages.reproduction = classifyReproduction(reproductionReport, pythonReport, profiles)
    report.python_acceptance_status = stages.python
    report.reproduction_status = stages.reproduction
    if (stages.python !== PASS || stages.reproduction !== PASS) {
      stages.http = NOT_RUN
      stages.windows = NOT_RUN
      report.reason = 'real_market_prerequisites_not_passed'
      await save('windows-acceptance.json', { status: NOT_RUN, reason: 'real_market_prerequisite_failed' })
      return
    }
    report.python_run_id = pythonReport.run_id
    report.python_fingerprint = pythonReport.profiles[profiles[0]].fingerprint

    currentStage = 'http'
    const { createServer } = await import('node:net')
    for (const port of [8011, 5173]) {
      const server = createServer()
      await new Promise((done, reject) => server.once('error', reject).listen(port, '127.0.0.1', done))
      await new Promise(done => server.close(done))
    }
    const backend = start('poetry', ['run', 'python', 'market_backtesting/tests/wp8_real_acceptance.py', '--root', artifactRoot, '--mode', 'serve'])
    const frontend = start(process.execPath, ['node_modules/vite/bin/vite.js', '--config', 'tests/config/vite.browser.config.ts', '--strictPort'], resolve(root, 'ui_web'))
    await ready('http://127.0.0.1:8011/auth/me', backend, 401)
    await ready(origin, frontend, 200)
    const credentials = await provision('wp8_real_user')
    const other = await provision('wp8_other_user')
    const cookie = await login(credentials)
    const foreignCookie = await login(other)
    const headers = { Origin: origin, 'Content-Type': 'application/json', Cookie: cookie }
    // The live authenticated backend publishes the exact schema used for validation.
    const openapi = await (await fetch('http://127.0.0.1:8011/openapi.json', { headers })).json()
    const schemaPath = '/backtesting/futures-roll/runs/{run_id}/result'
    const responseSchema = openapi.paths[schemaPath].get.responses['200'].content['application/json'].schema
    const validationSchema = JSON.parse(JSON.stringify({ ...responseSchema, $defs: openapi.components.schemas }).replaceAll('#/components/schemas/', '#/$defs/'))
    const validate = new Ajv2020({ strict: false, validateFormats: false }).compile(validationSchema)
    for (const profile of profiles) {
      const started = performance.now()
      const preflight = await fetch(`${base}/preflight`, { method: 'POST', headers, body: JSON.stringify(body(profile)) })
      assert.equal(preflight.status, 200)
      const readiness = await preflight.json()
      await save(`http-${profile}-preflight.json`, readiness)
      const accepted = await fetch(`${base}/runs`, { method: 'POST', headers, body: JSON.stringify(body(profile)) })
      assert.equal(accepted.status, 202)
      const admission = await accepted.json()
      assert.equal(admission.status, 'PENDING')
      const states = ['PENDING']
      let status
      do {
        const res = await fetch(`${base}/runs/${admission.run_id}`, { headers })
        assert.equal(res.status, 200)
        status = await res.json()
        if (states.at(-1) !== status.status) states.push(status.status)
        if (['PENDING', 'RUNNING'].includes(status.status)) {
          const early = await fetch(`${base}/runs/${admission.run_id}/result`, { headers })
          if (early.status !== 409) {
            // Completion can race the preceding Status read; never fail a legal 200.
            assert.equal(early.status, 200)
            const current = await (await fetch(`${base}/runs/${admission.run_id}`, { headers })).json()
            assert.equal(current.status, 'COMPLETED')
          }
          await pause(300)
        }
      } while (['PENDING', 'RUNNING'].includes(status.status))
      const item = { run_id: admission.run_id, terminal: status.status, states, seconds: (performance.now() - started) / 1000 }
      report.profiles[profile] = item
      if (status.status !== 'COMPLETED') {
        item.failure = status.failure
        item.status = ['upstream_operation', 'incomplete_input'].includes(status.failure?.category) ? 'NOT RUN' : 'FAIL'
        break
      }
      const response = await fetch(`${base}/runs/${admission.run_id}/result`, { headers })
      assert.equal(response.status, 200)
      assert.equal(response.headers.get('cache-control'), 'no-store')
      const raw = await response.text()
      assert.ok(Buffer.byteLength(raw) <= 33554432)
      const payload = JSON.parse(raw)
      assert.ok(validate(payload), 'live_openapi_result_invalid')
      assert.equal(payload.run_id, admission.run_id)
      assert.deepEqual(payload.request, status.request)
      assert.deepEqual(payload.request, payload.data.request)
      const expected = JSON.parse(await readFile(resolve(artifactRoot, `${profile}-result.json`), 'utf8'))
      assert.deepEqual(payload.data, expected)
      await save(`http-${profile}-result.json`, payload)
      item.status = PASS; item.result_bytes = Buffer.byteLength(raw)
      item.summary = payload.data.summary; item.window = payload.data.window
      item.fingerprint = payload.data.evidence.input_fingerprint
      const repeated = await (await fetch(`${base}/runs/${admission.run_id}/result`, { headers })).json()
      assert.deepEqual(repeated, payload)
      for (const suffix of ['', '/result']) {
        const a = await fetch(`${base}/runs/${admission.run_id}${suffix}`, { headers: { Cookie: foreignCookie } })
        const b = await fetch(`${base}/runs/${'0'.repeat(32)}${suffix}`, { headers: { Cookie: foreignCookie } })
        assert.equal(a.status, 404); assert.equal(b.status, 404)
        assert.deepEqual(await a.json(), await b.json())
      }
      report.privacy.foreign_unknown_identical = true
      report.privacy.completed_reread = true
      await save('http-acceptance.json', report)
    }
    const httpProfiles = combineStatuses(profiles.map(profile => report.profiles[profile]?.status))
    // The aggregate report carries the overall gate status, so classify HTTP with
    // an explicit HTTP-scoped view of the same profiles and run association.
    stages.http = classifyHttpAcceptance(
      { ...report, kind: 'actual_http_auth_real_market', status: httpProfiles },
      pythonReport,
      profiles,
    )
    await save('http-acceptance.json', report)
    if (stages.http === PASS) {
      currentStage = 'windows'
      stages.windows = await runWindowsStage(credentials)
    } else {
      stages.windows = NOT_RUN
      await save('windows-acceptance.json', { status: NOT_RUN, reason: 'real_market_prerequisite_failed' })
    }
    try {
      report.retained_run_count = (await readdir(env.LAB_BACKTESTING_RUN_ROOT)).length
    } catch {
      report.retained_run_count = 0
    }
  } catch (error) {
    stages[currentStage] = FAIL
    report.failure = { name: error.name, stage: currentStage }
  } finally {
    report.stages = stages
    report.status = classifyOverall(stages)
    report.exit_code = exitCode(report.status)
    await save('http-acceptance.json', report)
    for (const child of children.reverse()) if (child.exitCode === null) child.kill('SIGTERM')
    await pause(1000)
    // Credentials are disposable. Results/evidence survive; private runtime is removed.
    await rm(temporary, { recursive: true, force: true })
    process.exitCode = report.exit_code
  }
}

if (windows) await windowsBrowser()
else await orchestrate()
