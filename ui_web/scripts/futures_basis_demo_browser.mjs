// WP3: real Chromium against built static assets, without Python or any backend.
import assert from 'node:assert/strict'
import { spawn, spawnSync } from 'node:child_process'
import { mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'node:net'
import { chromium } from 'playwright'
import { historicalBasisAcceptance } from './historical_basis_acceptance.mjs'

const web = fileURLToPath(new URL('../', import.meta.url))
const output = await mkdtemp(resolve(tmpdir(), 'wp3-demo-browser-'))
const base = 'http://127.0.0.1:4179/hg-market-state-lab/'
const fixture = JSON.parse(await readFile(resolve(web, 'src/demo/futures_basis/report.v1.json'), 'utf8'))
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let preview; let browser; let page
function pass(message) { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  const build = spawnSync('npm', ['run', 'demo:build'], { cwd: web, encoding: 'utf8', shell: process.platform === 'win32' })
  assert.equal(build.status, 0, build.stderr || build.error?.message)
  const html = await readFile(resolve(web, 'dist-demo/index.html'), 'utf8')
  assert.match(html, /\/hg-market-state-lab\/assets\//)
  pass('Independent npm-only build emits dist-demo/index.html and subpath asset URLs')
  const port = createServer()
  await new Promise((done, reject) => port.once('error', reject).listen(4179, '127.0.0.1', done))
  await new Promise(done => port.close(done))
  preview = spawn(process.execPath, ['node_modules/vite/bin/vite.js', 'preview', '--config', 'vite.demo.config.ts', '--port', '4179', '--strictPort'], { cwd: web, stdio: ['ignore', 'pipe', 'pipe'] })
  let serverOutput = ''
  preview.stdout.on('data', chunk => { serverOutput += chunk })
  preview.stderr.on('data', chunk => { serverOutput += chunk })
  let ready = false
  for (let i = 0; i < 120; i++) {
    assert.equal(preview.exitCode, null, serverOutput)
    try { if ((await fetch(base)).status === 200) { ready = true; break } } catch { /* starting */ }
    await new Promise(done => setTimeout(done, 250))
  }
  assert.ok(ready, serverOutput)
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  evidence.browser = browser.version()
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, timezoneId: 'Asia/Shanghai' })
  await context.addInitScript(() => {
    window.__cookieAccess = []
    Object.defineProperty(document, 'cookie', {
      get() { window.__cookieAccess.push('read'); return '' },
      set() { window.__cookieAccess.push('write') },
    })
  })
  await context.route('**/*', async route => {
    const url = new URL(route.request().url())
    evidence.requests.push({ url: url.href, type: route.request().resourceType() })
    if (url.origin !== new URL(base).origin || !url.pathname.startsWith('/hg-market-state-lab/') || /\/(api|auth)(\/|$)/.test(url.pathname)) {
      evidence.errors.push(`Forbidden request: ${url.href}`)
      return route.abort()
    }
    return route.continue()
  })
  page = await context.newPage()
  page.setDefaultTimeout(20000)
  page.on('pageerror', e => evidence.errors.push(String(e)))
  page.on('console', m => { if (m.type() === 'error') evidence.errors.push(m.text()) })
  page.on('response', r => { if (r.status() >= 400) evidence.errors.push(`HTTP ${r.status()}: ${r.url()}`) })
  page.on('requestfailed', r => evidence.errors.push(`Request failed: ${r.url()}`))
  await page.goto(base)
  await page.locator('#section-1 .nsewdrag').first().waitFor()
  await page.getByRole('heading', { name: '股指期货历史基差研究', exact: true }).waitFor()
  for (const field of ['label', 'notice', 'data_source']) assert.ok((await page.locator('#synthetic-disclosure').textContent()).includes(fixture.disclosure[field]))
  assert.ok((await page.locator('#section-0').textContent()).includes(fixture.report.fingerprint))
  for (let i = 0; i < 6; i++) {
    await page.getByRole('navigation', { name: '报告章节' }).getByRole('link').nth(i).click()
    await page.locator(`#section-${i}`).getByRole('heading').first().waitFor({ state: 'visible' })
    assert.ok(await page.locator(`#section-${i}`).evaluate(el => {
      const r = el.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0
    }))
    assert.ok(await page.getByRole('link', { name: '查看合成演示数据声明' }).isVisible())
    const headingTop = await page.locator(`#section-${i}`).getByRole('heading').first().evaluate(el => el.getBoundingClientRect().top)
    assert.ok(headingTop >= 48, 'section heading must clear the sticky synthetic strip')
  }
  assert.match(await page.locator('#section-5').textContent(), /Synthetic Fixture/)
  assert.doesNotMatch(await page.locator('#section-5').textContent(), /此 HTTP 接口|相邻 inputs/)
  pass('Six shared report sections, navigation, producer fingerprint and verbatim synthetic disclosure render')
  await historicalBasisAcceptance(page, fixture.report, output)
  pass('Real Plotly Zoom / Pan / Reset, legend, hover and Trading / Calendar Days interactions')
  const metric = page.getByRole('combobox', { name: 'Distribution metric', exact: true })
  const slot = page.getByRole('combobox', { name: 'Distribution slot', exact: true })
  await metric.click()
  await page.getByText('basis_ratio', { exact: true }).last().click()
  await slot.click()
  await page.getByText('Q1', { exact: true }).last().click()
  const distribution = fixture.report.distributions.find(d => d.request.metric === 'basis_ratio' && d.request.slot === 'Q1')
  const histogram = fixture.report.views.histograms[`${distribution.request.analysis_id}/count`]
  await page.waitForFunction(title => document.querySelector('#section-2 .js-plotly-plot')?.layout.title.text === title, histogram.layout.title)
  assert.match(await page.locator('#section-3').textContent(), /Metric：basis_ratio/)
  await page.locator('#section-3 .ant-table-row-expand-icon').first().click()
  await page.getByText('共同日期：', { exact: false }).first().waitFor()
  pass('Metric / Slot choose existing fixture distributions and paired statistics expand')
  for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport)
    await page.getByRole('link', { name: '查看合成演示数据声明' }).click()
    await page.locator('#synthetic-disclosure').scrollIntoViewIfNeeded()
    assert.ok(await page.locator('#synthetic-disclosure').isVisible())
    await page.evaluate(() => window.scrollTo(0, 0))
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `Overflow at ${viewport.width}`)
    await page.screenshot({ path: resolve(output, `${viewport.width}-overview.png`) })
    await page.locator('#section-1 .js-plotly-plot').first().scrollIntoViewIfNeeded()
    await page.screenshot({ path: resolve(output, `${viewport.width}-chart.png`) })
    if (viewport.width === 390) {
      const frame = page.getByLabel('basis_value 图表，窄屏可横向滚动', { exact: true })
      assert.ok(await frame.evaluate(el => el.scrollWidth > el.clientWidth))
      await frame.evaluate(el => { el.scrollLeft = 120 })
      assert.ok(await frame.evaluate(el => el.scrollLeft > 0))
      await page.getByRole('combobox', { name: 'Distribution slot', exact: true }).click()
      await page.getByText('Q2', { exact: true }).last().click()
      const chosen = fixture.report.distributions.find(d => d.request.metric === 'basis_ratio' && d.request.slot === 'Q2')
      await page.waitForFunction(title => document.querySelector('#section-2 .js-plotly-plot')?.layout.title.text === title, fixture.report.views.histograms[`${chosen.request.analysis_id}/count`].layout.title)
    }
    await page.locator('#section-5').scrollIntoViewIfNeeded()
    assert.ok(await page.getByRole('link', { name: '查看合成演示数据声明' }).isVisible())
    await page.screenshot({ path: resolve(output, `${viewport.width}-evidence.png`) })
  }
  pass('Desktop 1440×900 and mobile 390×844 contain the reader; synthetic indicator remains visible while scrolling')
  assert.deepEqual(await page.evaluate(() => window.__cookieAccess), [])
  await page.reload()
  await page.locator('#section-1 .nsewdrag').first().waitFor()
  assert.deepEqual(await page.evaluate(() => window.__cookieAccess), [])
  assert.deepEqual(await context.cookies(), [])
  assert.deepEqual(evidence.errors, [])
  assert.ok(evidence.requests.every(r => r.type === 'document' || r.type === 'script' || r.type === 'stylesheet' || r.type === 'font' || r.type === 'image'))
  pass('Subpath refresh works; no Auth / API / external requests, cookie access, resource failures or console errors')
  // Fault injection changes the input to the real WP2 parser in the built chunk.
  // No failure switch or fake fixture is added to the application.
  const broken = await browser.newContext()
  const faultErrors = []
  const faultPage = await broken.newPage()
  faultPage.on('pageerror', e => faultErrors.push(String(e)))
  await broken.route('**/assets/fixture-*.js', async route => {
    const response = await route.fetch()
    const original = await response.text()
    const changed = original.replace(/JSON\.parse\([\w$]+\)/, 'JSON.parse("null")')
    assert.notEqual(changed, original, 'must inject invalid data into actual fixture parser')
    await route.fulfill({ response, body: changed })
  })
  await faultPage.goto(base)
  await faultPage.getByText('演示数据无法加载或校验失败', { exact: true }).waitFor()
  assert.equal(await faultPage.locator('[id^="section-"]').count(), 0)
  assert.deepEqual(faultErrors, [])
  await faultPage.screenshot({ path: resolve(output, 'invalid-fixture.png') })
  await broken.close()
  pass('Invalid fixture reaches real validation and displays an error with no fabricated report')
  evidence.status = 'PASS'
} catch (error) {
  evidence.status = 'FAIL'; evidence.errors.push(error.stack || String(error)); process.exitCode = 1
  if (page) await page.screenshot({ path: resolve(output, 'failure.png') }).catch(() => {})
} finally {
  if (browser) await browser.close()
  if (preview) {
    const stopped = new Promise(done => preview.once('exit', done))
    if (preview.exitCode === null) { preview.kill('SIGTERM'); await stopped }
  }
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(evidence, null, 2))
  console.log(`Demo browser acceptance: ${evidence.status}; artifacts: ${output}`)
  if (evidence.status !== 'PASS') console.error(evidence.errors)
}
