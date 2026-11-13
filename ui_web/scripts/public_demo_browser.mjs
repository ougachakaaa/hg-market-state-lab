import assert from 'node:assert/strict'
import { createServer } from 'node:http'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { resolve, extname, relative, sep } from 'node:path'
import { chromium } from 'playwright'
import { createServer as createViteServer } from 'vite'
import { workspaceRoutes } from '../src/app/routeInventory.ts'
import { output as build, loadPublicPackage, verifyArtifact } from './public_release.mjs'

const artifact = resolve(build, 'site')
const output = resolve(build, process.argv[2] ? 'browser-online' : 'browser-local')
const publicUrl = process.argv[2]
const { envelope } = loadPublicPackage()
const payload = key => JSON.parse(envelope.examples[key].json)
const read = async (root, path) => JSON.parse(await readFile(resolve(root, path), 'utf8'))
// Use the formal feature exporters as the byte oracle; no second CSV projection.
const validator = await createViteServer({ configFile: false, logLevel: 'silent', server: { middlewareMode: true }, appType: 'custom' })
let csvModels
try {
  csvModels = [await validator.ssrLoadModule('/src/features/mo_option_chain/model/csvExport.ts'), await validator.ssrLoadModule('/src/features/mo_option_premium/model/csvExport.ts')]
} finally { await validator.close() }
const admission = await read(build, 'release.json')
verifyArtifact(artifact, admission)
assert.equal(admission.status, 'PASS')

await mkdir(output, { mode: 0o700 })
const evidence = { status: 'RUNNING', routes: [], checks: [], requests: [], errors: [], warnings: [] }
let browser
const server = createServer(async (req, res) => {
  const name = decodeURIComponent(new URL(req.url, 'http://local').pathname).replace(/^\/hg-market-state-lab\//, '') || 'index.html'
  const path = resolve(artifact, name)
  if (relative(artifact, path).startsWith('..' + sep)) { res.writeHead(404).end(); return }
  try { res.writeHead(200, { 'Content-Type': { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.json': 'application/json' }[extname(path)] || 'application/octet-stream' }).end(await readFile(path)) }
  catch { res.writeHead(404).end() }
})
const pass = label => { evidence.checks.push(label); console.log(`PASS: ${label}`) }
try {
  await new Promise(done => server.listen(0, '127.0.0.1', done))
  const base = publicUrl || `http://127.0.0.1:${server.address().port}/hg-market-state-lab/`
  evidence.url = base; evidence.sourceSha = admission.sourceSha; evidence.artifactDigest = admission.artifactDigest
  browser = await chromium.launch({ headless: true })
  evidence.browser = browser.version()
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, permissions: ['clipboard-read', 'clipboard-write'] })
  await context.route('**/*', async route => {
    const request = route.request(), url = new URL(request.url())
    evidence.requests.push({ path: url.pathname, type: request.resourceType(), method: request.method() })
    if (url.origin !== new URL(base).origin || !url.pathname.startsWith('/hg-market-state-lab/') || /\/(api|auth)(\/|$)/.test(url.pathname) || request.method() !== 'GET' || !['document', 'script', 'stylesheet', 'font', 'image'].includes(request.resourceType())) {
      evidence.errors.push(`Forbidden request ${url.pathname}`); await route.abort()
    } else await route.continue()
  })
  const page = await context.newPage()
  page.setDefaultTimeout(20000)
  page.on('pageerror', error => evidence.errors.push(String(error)))
  page.on('console', message => { if (message.text().startsWith('Warning: [antd: List] The `List` component is deprecated')) evidence.warnings.push(message.text()); else if (message.type() === 'error') evidence.errors.push(message.text()); else if (message.type() === 'warning') evidence.warnings.push(message.text()) })
  page.on('response', response => { if (response.status() >= 400) evidence.errors.push(`HTTP ${response.status()}: ${new URL(response.url()).pathname}`) })
  const main = page.locator('main')
  const headings = { '/research': '研究总览', '/research/futures-basis': 'Futures Basis Research', '/research/publications': '研究结果浏览', '/data': '数据总览', '/data/mo-option-chain': 'MO 期权链', '/data/mo-premium-plane': 'MO 年化权利金平面', '/backtesting': '期货展期做多回测' }
  const go = async path => {
    await page.evaluate(path => { window.location.hash = `#${path}` }, path)
    await main.getByRole('heading', { name: headings[path], exact: true }).waitFor()
    await page.waitForFunction(() => !document.body.textContent.includes('Static Error'))
  }
  // Hold the actual WebCrypto admission, asserting loading without a timed sleep.
  await page.addInitScript(() => {
    const digest = crypto.subtle.digest.bind(crypto.subtle)
    let release
    const gate = new Promise(done => { release = done })
    window.releaseStaticAdmission = release
    crypto.subtle.digest = async (...args) => { await gate; return digest(...args) }
  })
  if (publicUrl) {
    const { createHash } = await import('node:crypto')
    let failure
    for (let attempt = 0; attempt < 12; attempt++) {
      try {
        for (const file of admission.files) {
          const response = await context.request.get(new URL(file.file, base).href)
          assert.equal(response.status(), 200)
          const bytes = await response.body()
          assert.equal(createHash('sha256').update(bytes).digest('hex'), file.sha256, `Deployed asset ${file.file}`)
        }
        failure = null; break
      } catch (error) { failure = error; if (attempt < 11) await new Promise(done => setTimeout(done, 5000)) }
    }
    if (failure) throw failure
    pass('All deployed file bytes match exact candidate inventory')
  }
  await page.goto(base)
  await page.getByText('静态 Example 正在校验', { exact: true }).waitFor()
  await page.evaluate(() => window.releaseStaticAdmission())
  await main.getByRole('heading', { name: '研究总览', exact: true }).waitFor()
  assert.equal(new URL(page.url()).hash, '#/research')
  await page.getByText('Market State Lab — Personal Research & Engineering Portfolio', {exact:true}).waitFor()
  await page.getByText(/本项目仅用于个人软件工程与金融研究方法展示/).waitFor()
  for (const route of workspaceRoutes) {
    assert.ok(headings[route.path], `Missing browser gate: ${route.path}`)
    await go(route.path)
    assert.equal(await page.getByText('Static Error', { exact: true }).count(), 0)
    assert.ok(await page.locator('.ant-breadcrumb').getByText(route.title, { exact: true }).count() > 0)
    for (const width of [1440, 1024, 390]) {
      await page.setViewportSize({ width, height: 1000 })
      const metrics = await page.evaluate(() => ({ viewport: innerWidth, body: document.documentElement.scrollWidth }))
      assert.ok(metrics.body <= metrics.viewport + 2, `Document overflow ${route.path} at ${width}: ${JSON.stringify(metrics)}`)
      await page.screenshot({ path: resolve(output, `${route.path.replaceAll('/', '_')}-${width}.png`) })
    }
    await page.setViewportSize({ width: 1440, height: 1000 })
    evidence.routes.push({ path: route.path, sharedPresentation: true, widths: [1440, 1024, 390], status: 'PASS' })
  }
  pass('All canonical routes, shared breadcrumbs and 1440/1024/narrow containment')
  await page.evaluate(() => { window.location.hash = '#/unknown' })
  await page.waitForFunction(() => location.hash === '#/research')
  await go('/research')
  await main.getByRole('button', { name: '查看详情', exact: true }).first().click()
  await main.getByRole('region', { name: '所选研究详情' }).waitFor()
  assert.match(await main.textContent(), /trailing_cumulative_return_v1/)
  assert.match(await main.textContent(), /not_probed/)
  pass('Static admission loading state completes without a backend')
  pass('Genuine Capability identity, status and local Detail')

  const download = async name => {
    const pending = page.waitForEvent('download')
    await page.getByRole('button', { name, exact: true }).click()
    const file = await pending
    return { name: file.suggestedFilename(), bytes: await readFile(await file.path()) }
  }
  for (const [path, expectedRows] of [['/data/mo-option-chain', 312], ['/data/mo-premium-plane', 312]]) {
    await go(path)
    const expected = payload(path.includes('chain') ? 'chain' : 'premium')
    await main.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
    await page.waitForFunction(expected => navigator.clipboard.readText().then(value => { try { return JSON.stringify(JSON.parse(value)) === JSON.stringify(expected) } catch { return false } }), expected)
    const raw = await page.evaluate(() => navigator.clipboard.readText())
    assert.deepEqual(JSON.parse(raw), expected)
    const expiries = main.getByRole('checkbox')
    if (await expiries.count() > 1) await expiries.first().click()
    if (path.includes('chain')) await main.getByRole('button', { name: '扩大行权价视窗' }).click()
    else {
      for (const name of ['Put', 'Same-expiry futures', 'Time value', 'Unannualized', 'Yield']) { const radio = main.getByRole('radio', { name, exact: true }); await radio.locator('xpath=ancestor::label').click(); assert.equal(await radio.isChecked(), true) }
      await main.getByText('View embedded payload', { exact: true }).click()
      await main.getByText('Validated embedded Example payload', { exact: true }).waitFor()
      assert.match(await main.textContent(), /Historical Real Market Data/)
    }
    await main.getByRole('button', { name: 'Copy Raw JSON', exact: true }).click()
    assert.deepEqual(JSON.parse(await page.evaluate(() => navigator.clipboard.readText())), expected)
    await main.getByRole('button', { name: 'Copy Context JSON', exact: true }).click()
    await page.waitForFunction(() => navigator.clipboard.readText().then(value => value.includes('daily-data-context-v1')))
    const copied = JSON.parse(await page.evaluate(() => navigator.clipboard.readText()))
    assert.deepEqual(copied.data, expected)
    const csv = await download('Export CSV')
    const formalCsv = path.includes('chain') ? csvModels[0].optionChainCsv(expected) : csvModels[1].premiumPlaneCsv(expected)
    assert.equal(csv.bytes.toString('utf8'), formalCsv.csv)
    assert.equal(csv.name, formalCsv.filename)
    assert.equal(csv.bytes.toString('utf8').replace(/^\uFEFF/, '').trimEnd().split('\r\n').length, expectedRows + 1)
    const json = await download('Export Context JSON')
    assert.deepEqual(JSON.parse(json.bytes.toString('utf8')), copied)
    assert.match(json.name, /2026-11-11_close/)
    if (path.includes('chain')) {
      const plot = page.locator('.js-plotly-plot').first()
      await plot.waitFor(); await plot.scrollIntoViewIfNeeded()
      const bounds = await plot.boundingBox()
      const index = await plot.locator('.scatterlayer .trace .point').evaluateAll((points, box) => points.findIndex(point => { const r = point.getBoundingClientRect(); return r.x > box.x + 100 && r.right < box.x + box.width - 50 && r.y > box.y + 60 && r.bottom < box.y + box.height - 60 }), bounds)
      assert.ok(index >= 0, 'A genuine point is inside the selected strike viewport')
      await plot.locator('.scatterlayer .trace .point').nth(index).hover({ force: true })
      await plot.locator('.hoverlayer .hovertext').first().waitFor()
    }
    pass(`${path}: full genuine payload Copy/Context/CSV/JSON after local expiry selection`)
  }
  await go('/research/futures-basis')
  for (let i = 0; i < 6; i++) assert.equal(await page.locator(`#section-${i}`).count(), 1)
  await main.getByRole('button', { name: '06 · 证据与限制' }).click()
  assert.equal(new URL(page.url()).hash, '#/research/futures-basis')
  assert.match(await page.locator('#section-5').textContent(), /Historical Real Market Data/)
  assert.doesNotMatch(await page.locator('#section-5').textContent(), /Synthetic Fixture/)
  const basisPlots = page.locator('#section-1 .js-plotly-plot')
  assert.deepEqual(await basisPlots.evaluateAll(els => els.map(el => el._fullLayout.xaxis.type)), ['linear', 'linear', 'linear'])
  await main.getByText('Calendar Days', { exact: true }).click()
  await page.waitForFunction(() => [...document.querySelectorAll('#section-1 .js-plotly-plot')].every(el => el._fullLayout.xaxis.type === 'date'))
  await main.getByText('Trading Days', { exact: true }).click()
  await page.waitForFunction(() => [...document.querySelectorAll('#section-1 .js-plotly-plot')].every(el => el._fullLayout.xaxis.type === 'linear'))
  await main.getByLabel('Distribution slot').click(); await page.getByTitle('Q1', { exact: true }).click()
  pass('Basis all six sections, 206 sessions, local section jump, Slot and time axis')

  await go('/research/publications')
  assert.equal(await main.getByRole('button', { name: '上一页', exact: true }).isDisabled(), true)
  assert.equal(await main.getByRole('button', { name: '下一页', exact: true }).isDisabled(), true)
  await main.getByRole('button', { name: /^选\s*择$/ }).click()
  assert.equal(await main.getByRole('button', { name: '选择 Analysis', exact: true }).count(), 4)
  let viewCount = 0
  for (let i = 0; i < 4; i++) {
    await main.getByRole('button', { name: '选择 Analysis', exact: true }).nth(i).click()
    const card = main.locator('.ant-card').filter({ has: page.getByText('所选 Analysis', { exact: true }) }).first()
    const viewButtons = card.getByRole('button').filter({ hasText: /^(quantile|count|frequency)$/ })
    for (let j = 0; j < await viewButtons.count(); j++) { await viewButtons.nth(j).click(); await page.locator('.js-plotly-plot').first().waitFor(); viewCount++ }
  }
  assert.equal(viewCount, 6)
  pass('Explorer actual Publication, four Analyses and all six ChartViews')

  await go('/backtesting')
  for (const strategy of ['expiry_to_M1_v1', 'expiry_to_Q1_v1']) {
    if (strategy.includes('Q1')) { await main.getByLabel('已计算策略结果').click(); await page.getByTitle(strategy, { exact: true }).click() }
    const expected = payload(strategy).result
    await page.waitForFunction(strategy => document.querySelector('[data-testid="backtest-result"]')?.textContent.includes(strategy), strategy)
    assert.match(await main.getByTestId('backtest-result').textContent(), /206 个交易日/)
    const plots = page.locator('.js-plotly-plot')
    await plots.first().locator('.nsewdrag').waitFor()
    assert.equal(await plots.count(), 2)
    await page.waitForFunction(() => [...document.querySelectorAll('.js-plotly-plot')].every(el => el._fullLayout.xaxis.type === 'linear'))
    await main.getByText('Calendar Days', { exact: true }).click()
    await page.waitForFunction(() => [...document.querySelectorAll('.js-plotly-plot')].every(el => el._fullLayout.xaxis.type === 'date'))
    const actualDates = await plots.first().evaluate(el => el.data.find(t => t.type === 'scatter' && t.showlegend !== false).x)
    assert.deepEqual(actualDates, expected.views.returns.layers[0].layer.data.map(m => m.x))
    const ys = await plots.first().evaluate(el => el.data.filter(t => t.type === 'scatter' && t.showlegend !== false).map(t => t.y))
    assert.ok(ys.some(y => JSON.stringify(y) === JSON.stringify(expected.views.returns.layers[0].layer.data.map(m => m.y))))
    await main.getByText('研究证据与限制 · Evidence / Limitations', { exact: true }).click()
    assert.doesNotMatch(await main.textContent(), /Embedded Synthetic Example/)
  }
  await main.getByText('Trading Days', { exact: true }).click()
  await page.waitForFunction(() => [...document.querySelectorAll('.js-plotly-plot')].every(el => el._fullLayout.xaxis.type === 'linear'))
  const plot = page.locator('.js-plotly-plot').first()
  await plot.scrollIntoViewIfNeeded()
  const initialRange = await plot.evaluate(el => el._fullLayout.xaxis.range.map(String))
  const box = await plot.boundingBox()
  await page.mouse.move(box.x + box.width * .3, box.y + box.height * .5); await page.mouse.down()
  await page.mouse.move(box.x + box.width * .7, box.y + box.height * .5, { steps: 8 }); await page.mouse.up()
  await page.waitForFunction(before => document.querySelector('.js-plotly-plot')?._fullLayout.xaxis.range.some((v, i) => String(v) !== before[i]), initialRange)
  await page.locator('.modebar-btn[data-title="Reset axes"]').first().click()
  await page.waitForFunction(before => document.querySelector('.js-plotly-plot')?._fullLayout.xaxis.range.every((v, i) => String(v) === before[i]), initialRange)
  await page.locator('.modebar-btn[data-title="Pan"]').first().click()
  await page.waitForFunction(() => document.querySelector('.js-plotly-plot')?._fullLayout.dragmode === 'pan')
  pass('M1/Q1 formal returns coordinates, complete readers, real Plotly Zoom/Pan/Reset')
  await go('/research/publications')
  await page.locator('.ant-breadcrumb a').first().click()
  await main.getByRole('heading', { name: '研究总览', exact: true }).waitFor()
  await page.getByRole('menuitem', { name: '回测', exact: true }).click()
  await main.getByRole('heading', { name: '期货展期做多回测', exact: true }).waitFor()
  pass('Shared sidebar and breadcrumb links navigate locally')
  await go('/data'); await go('/research/publications'); await page.goBack(); assert.equal(new URL(page.url()).hash, '#/data')
  await page.goForward(); assert.equal(new URL(page.url()).hash, '#/research/publications')
  await page.reload(); await page.getByText('静态 Example 正在校验', { exact: true }).waitFor(); await page.evaluate(() => window.releaseStaticAdmission()); await main.getByRole('heading', { name: '研究结果浏览', exact: true }).waitFor()
  pass('Hash navigation, browser Back/Forward and deep-link reload')
  const invalid = await context.newPage()
  invalid.on('pageerror', error => evidence.errors.push(String(error)))
  await invalid.route('**/*.js', async route => {
    const response = await route.fetch()
    const source = await response.text()
    const changed = source.replaceAll(envelope.examples.chain.identity.resultDigest, '0'.repeat(64))
    if (source === changed) { await route.fulfill({response}); return }
    evidence.requests.push({ path: new URL(route.request().url()).pathname, type: 'script', method: 'GET', probe: 'invalid-digest' })
    await route.fulfill({ response, body: changed })
  })
  await invalid.goto(base)
  await invalid.getByText('Static Error：公共 Example 准入失败', { exact: true }).waitFor()
  assert.equal(await invalid.getByRole('heading', { name: '研究总览', exact: true }).count(), 0)
  await invalid.screenshot({ path: resolve(output, 'static-error.png') })
  await invalid.close()
  pass('Corrupt embedded digest displays Static Error before business mounting; no fallback')
  assert.deepEqual(await context.cookies(), [])
  assert.deepEqual(evidence.errors, [])
  evidence.status = 'PASS'
} catch (error) { evidence.status = 'FAIL'; evidence.failure = String(error); throw error }
finally {
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(evidence, null, 2))
  await browser?.close(); await new Promise(done => server.close(done))
}
