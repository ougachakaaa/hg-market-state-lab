// Actual offline file:// acceptance. Never starts a server or permits network I/O.
import assert from 'node:assert/strict'
import { mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { tmpdir } from 'node:os'
import { spawnSync } from 'node:child_process'
import { pathToFileURL, fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

// The no-argument npm command is a self-contained synthetic regression gate.
if (!process.argv[2]) {
  const repository = fileURLToPath(new URL('../../', import.meta.url))
  const web = resolve(repository, 'ui_web')
  const temporary = await mkdtemp(resolve(tmpdir(), 'r01a-offline-browser-'))
  const report = resolve(temporary, 'report')
  const commands = [
    ['poetry', ['run', 'python', 'ui_web/scripts/futures_basis_offline_fixture.py', report], repository],
    [process.execPath, ['scripts/package_futures_basis_report.mjs', report], web],
    [process.execPath, [fileURLToPath(import.meta.url), report], web],
  ]
  for (const [command, args, cwd] of commands) {
    const result = spawnSync(command, args, { cwd, env: process.env, stdio: 'inherit' })
    if (result.error) throw result.error
    if (result.status !== 0) process.exit(result.status ?? 1)
  }
  console.log(`Offline regression artifacts: ${temporary}`)
  process.exit(0)
}
const directory = resolve(process.argv[2])
const output = resolve(process.argv[3] || `${directory}-browser`)
await mkdir(output, { recursive: true })
const expected = JSON.parse(await readFile(resolve(directory, 'report-data.json'), 'utf8'))
const evidence = { status: 'RUNNING', checks: [], requests: [], errors: [] }
let browser; let page
function pass(message) { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  evidence.browser = browser.version()
  const context = await browser.newContext({ offline: true, viewport: { width: 1440, height: 900 }, timezoneId: 'Asia/Shanghai' })
  page = await context.newPage()
  page.setDefaultTimeout(20000)
  page.on('pageerror', e => evidence.errors.push(String(e)))
  page.on('console', m => { if (m.type() === 'error') evidence.errors.push(m.text()) })
  page.on('request', r => { if (!r.url().startsWith('file:') && !r.url().startsWith('data:') && !r.url().startsWith('blob:')) evidence.requests.push(r.url()) })
  await page.goto(pathToFileURL(resolve(directory, 'report.html')).href)
  await page.locator('.js-plotly-plot').first().locator('.nsewdrag').waitFor()
  await page.evaluate(() => document.fonts.ready)
  assert.ok(await page.evaluate(() => Array.from(document.fonts).some(f => f.family.includes('R01A CJK') && f.status === 'loaded')))
  pass('Embedded Chinese font loads with the browser offline and no system CJK fonts')
  for (let i = 0; i < 6; i++) assert.equal(await page.locator(`#section-${i}`).count(), 1)
  const embedded = await page.locator('#report-data').textContent()
  assert.deepEqual(JSON.parse(embedded), expected)
  assert.ok((await page.locator('#section-0').textContent()).includes(expected.fingerprint))
  pass('Six reader sections render; embedded data exactly equals producer payload and fingerprint')
  const plots = page.locator('#section-1 .js-plotly-plot')
  assert.equal(await plots.count(), 3)
  for (let i = 0; i < 3; i++) {
    const metric = ['basis_value', 'basis_ratio', 'annualized_basis_ratio'][i]
    const view = expected.views.history[metric]
    const plot = plots.nth(i)
    await plot.locator('.nsewdrag').waitFor()
    assert.equal(await plot.locator('.legend .traces').count(), 4)
    const shapes = await plot.evaluate(el => el.layout.shapes.length)
    assert.equal(shapes, view.events.length)
    const points = await plot.evaluate(el => el.data.flatMap(t => t.y ?? []).filter(y => y !== null).length)
    assert.equal(points, view.layers.flatMap(b => b.layer.data).filter(m => m.y !== null).length)
  }
  pass('Three independent metrics render all supplied finite points, four Slot legends and every real transition')
  const hasNumeric = expected.views.history.basis_value.layers.some(b => b.layer.data.some(m => m.y !== null))
  if (hasNumeric) {
    const plot = plots.first()
    // Scroll/layout changes can move SVG marks under a stationary pointer. Wait
    // for the real drag surface to settle, then address actual viewport pixels.
    async function settlePlot() {
      await plot.evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }))
      await plot.locator('.nsewdrag').evaluate(el => new Promise((resolve, reject) => {
        let previous = ''; let stable = 0; const started = performance.now()
        function frame() {
          const r = el.getBoundingClientRect()
          const current = [r.x, r.y, r.width, r.height, window.scrollY].join(',')
          stable = current === previous ? stable + 1 : 0; previous = current
          if (stable >= 12) resolve()
          else if (performance.now() - started > 15000) reject(new Error('Plot layout did not settle'))
          else requestAnimationFrame(frame)
        }
        frame()
      }))
    }
    await settlePlot()
    const point = plot.locator('.scatterlayer .point').first()
    const pointBox = await point.boundingBox()
    await page.mouse.move(pointBox.x + pointBox.width / 2, pointBox.y + pointBox.height / 2)
    await page.waitForFunction(() => document.querySelector('#section-1 .hoverlayer')?.textContent.includes('实际合约'))
    const hover = await plot.locator('.hoverlayer').textContent()
    for (const word of ['交易日期', '实际合约', 'DTE', '基差状态', 'Close', 'Source Association']) assert.ok(hover.includes(word), hover)
    await page.screenshot({ path: resolve(output, 'hover.png') })
    pass('Actual mouse hover exposes real contract, dates, prices, DTE, state and source association')
    const initial = await plot.evaluate(el => Array.from(el._fullLayout.xaxis.range))
    async function drag(x0, x1) {
      await settlePlot()
      const box = await plot.locator('.nsewdrag').boundingBox()
      await page.mouse.move(box.x + box.width * x0, box.y + box.height * .5)
      await page.mouse.down(); await page.mouse.move(box.x + box.width * x1, box.y + box.height * .5, { steps: 12 }); await page.mouse.up()
    }
    async function changed(old) {
      await page.waitForFunction(before => JSON.stringify(Array.from(document.querySelector('#section-1 .js-plotly-plot')._fullLayout.xaxis.range)) !== JSON.stringify(before), old)
    }
    await drag(.15, .75); await changed(initial)
    await plot.locator('[data-title="Pan"]').click()
    const zoomed = await plot.evaluate(el => Array.from(el._fullLayout.xaxis.range))
    await drag(.5, .7); await changed(zoomed)
    await plot.locator('[data-title="Reset axes"]').click()
    await page.waitForFunction(before => JSON.stringify(Array.from(document.querySelector('#section-1 .js-plotly-plot')._fullLayout.xaxis.range)) === JSON.stringify(before), initial)
    await plot.locator('.legend .traces').first().click()
    await page.waitForFunction(() => document.querySelector('#section-1 .js-plotly-plot')._fullData.some(t => t.visible === 'legendonly'))
    pass('Real box Zoom, drag Pan, Reset and grouped Slot legend interactions work offline')
  } else {
    assert.equal(await page.getByText('No numeric data', { exact: true }).count(), 3)
    pass('All-null series explicitly show no numeric data without invented values')
  }
  if (expected.distributions.some(d => d.methods.some(m => m.failure_category === 'CalculationFailure'))) {
    assert.ok((await page.locator('#section-2').textContent()).includes('CalculationFailure'))
    pass('Original statistical failure is visible in Chromium')
  }
  if (expected.summary.includes('__wp5Injected')) {
    assert.equal(await page.evaluate(() => window.__wp5Injected), undefined)
    assert.ok((await page.locator('#section-0').textContent()).includes(expected.summary))
    pass('Script-ending producer text remains literal and cannot execute')
  }
  const eventReadout = page.locator('#section-1 section[aria-label="Date events"]').first()
  if (expected.views.history.basis_value.events.length) {
    await eventReadout.locator('.ant-collapse-header').first().click()
    assert.ok((await eventReadout.textContent()).includes('观测到的角色映射变化'))
  }
  const missing = page.locator('#section-1 section[aria-label="Missing values"]')
  if (expected.views.history.annualized_basis_ratio.layers.some(b => b.layer.data.some(m => m.y === null))) {
    assert.ok(await missing.count() > 0)
    await missing.first().locator('.ant-collapse-header').first().click()
    assert.ok((await missing.first().textContent()).includes('原因'))
  }
  await page.locator('#section-3 .ant-table-row-expand-icon').first().click()
  assert.ok((await page.locator('#section-3').textContent()).includes('共同日期'))
  await page.locator('#section-5').scrollIntoViewIfNeeded()
  await page.screenshot({ path: resolve(output, 'report.png'), fullPage: true })
  pass('Transition, unavailable reason, paired population and evidence/limitations are reader-accessible')
  assert.equal(await page.getByRole('heading', { level: 1, name: `${expected.request.observation.product_code} 历史基差研究报告` }).count(), 1)
  for (const close of await page.locator('.notifier-close').all()) await close.click()
  for (const viewport of [{ width: 1440, height: 900 }, { width: 1024, height: 768 }]) {
    await page.setViewportSize(viewport)
    await page.getByRole('navigation', { name: '报告章节' }).getByRole('link').first().click()
    await page.evaluate(() => window.scrollTo(0, 0))
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
    await page.screenshot({ path: resolve(output, `${viewport.width}x${viewport.height}-overview.png`) })
    await page.locator('#section-1 .js-plotly-plot').first().scrollIntoViewIfNeeded()
    await page.screenshot({ path: resolve(output, `${viewport.width}x${viewport.height}-chart.png`) })
    await page.locator('#section-5').getByText('研究参数与逐日结果定位', { exact: true }).click()
    await page.locator('#section-5').scrollIntoViewIfNeeded()
    await page.screenshot({ path: resolve(output, `${viewport.width}x${viewport.height}-evidence.png`) })
    await page.screenshot({ path: resolve(output, `${viewport.width}x${viewport.height}-full.png`), fullPage: true })
    await page.locator('#section-5').getByText('研究参数与逐日结果定位', { exact: true }).click()
  }
  pass('Standalone heading, section navigation, expanded offline evidence and containment at 1440×900 and 1024×768')
  assert.deepEqual(evidence.requests, [])
  assert.deepEqual(evidence.errors, [])
  evidence.status = 'PASS'
} catch (error) {
  evidence.status = 'FAIL'; evidence.errors.push(error.stack || String(error)); process.exitCode = 1
  if (page) await page.screenshot({ path: resolve(output, 'failure.png') }).catch(() => {})
} finally {
  if (browser) await browser.close()
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(evidence, null, 2))
  console.log(JSON.stringify(evidence))
}
