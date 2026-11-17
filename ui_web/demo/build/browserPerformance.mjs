// Explicit local measurement of the real static artifact; no request interception.
import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'
import { chromium } from 'playwright'
import { previewDemo } from './preview.mjs'
import { assertRouteResult } from './browserAcceptance.mjs'

export async function measurePerformance(outputRoot, evidenceRoot, initialRoute = '/research') {
  const server = await previewDemo(0, { outputRoot })
  let browser
  try {
    browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
    const page = await context.newPage()
    const cdp = await context.newCDPSession(page)
    await cdp.send('Network.enable')
    await cdp.send('Performance.enable')
    const base = `http://127.0.0.1:${server.httpServer.address().port}/hg-market-state-lab/`
    let requests = [], pending = new Map()
    cdp.on('Network.requestWillBeSent', event => {
      assert.equal(new URL(event.request.url).origin, new URL(base).origin)
      assert.equal(event.request.method, 'GET')
      const request = { url: event.request.url, type: event.type }
      requests.push(request); pending.set(event.requestId, request)
    })
    cdp.on('Network.responseReceived', event => {
      Object.assign(pending.get(event.requestId) ?? {}, {
        status: event.response.status, fromDiskCache: event.response.fromDiskCache ?? false,
        contentEncoding: event.response.headers['Content-Encoding'] ?? event.response.headers['content-encoding'] ?? 'identity',
      })
    })
    cdp.on('Network.loadingFinished', event => {
      Object.assign(pending.get(event.requestId) ?? {}, { encodedTransferBytes: event.encodedDataLength })
    })
    async function metrics() { return Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value])) }
    const steps = []
    async function step(name, action, route) {
      requests = []; pending = new Map()
      await page.evaluate(() => { performance.clearResourceTimings(); performance.clearMeasures() }).catch(() => {})
      const before = await metrics(), start = performance.now()
      await action()
      await assertRouteResult(page, route)
      const resultReadyMs = performance.now() - start
      await page.waitForLoadState('networkidle')
      const after = await metrics()
      const timings = await page.evaluate(() => ({
        resources: performance.getEntriesByType('resource').map(r => ({ name: r.name, initiatorType: r.initiatorType, transferSize: r.transferSize, encodedBodySize: r.encodedBodySize, decodedBodySize: r.decodedBodySize, durationMs: r.duration })),
        bundleMeasures: performance.getEntriesByType('measure').filter(m => m.name.startsWith('demo-bundle:')).map(m => ({ name: m.name, durationMs: m.duration })),
      }))
      const scripts = timings.resources.filter(r => /\.js(?:$|\?)/.test(r.name))
      steps.push({ name, resultReadyMs, scriptExecutionMs: (after.ScriptDuration - before.ScriptDuration) * 1000,
        scriptTransferBytes: scripts.reduce((n, r) => n + r.transferSize, 0),
        scriptEncodedBodyBytes: scripts.reduce((n, r) => n + r.encodedBodySize, 0),
        scriptDecodedBodyBytes: scripts.reduce((n, r) => n + r.decodedBodySize, 0),
        requests: [...requests], ...timings })
    }
    const navigate = route => page.evaluate(route => { location.hash = '#' + route }, route)
    assert.ok(['/data', '/research'].includes(initialRoute))
    await step('cold-' + (initialRoute === '/data' ? 'data' : 'research') + '-overview', () => page.goto(base + '#' + initialRoute), initialRoute)
    if (initialRoute === '/research') await step('data-overview', () => navigate('/data'), '/data')
    await step('research-overview', () => navigate('/research'), '/research')
    await step('open-basis', () => navigate('/research/futures-basis'), '/research/futures-basis')
    await step('open-M1', () => navigate('/backtesting/futures-roll-long'), '/backtesting/futures-roll-long')
    await step('select-Q1', async () => {
      await page.getByRole('combobox', { name: '已计算策略结果' }).click()
      await page.getByTitle('到期换入首个后续季月合约（M0 → Q1）', { exact: true }).click()
      const q1 = await import('../bundles/expiry_to_Q1_v1.json', { with: { type: 'json' } })
      await page.getByTestId('backtest-result').getByText((q1.default.result.summary.gross_return * 100).toFixed(1) + '%', { exact: true }).waitFor()
    }, '/backtesting/futures-roll-long')
    await step('return-basis', () => navigate('/research/futures-basis'), '/research/futures-basis')
    await step('return-research-overview', () => navigate('/research'), '/research')
    const evidence = { browser: browser.version(), viewport: '1440x1000', network: 'loopback, no throttling or interception',
      cache: 'fresh browser context then same-document navigation; HTTP cache enabled',
      sizes: 'Resource Timing transferSize includes HTTP overhead; encoded/decoded body sizes exclude headers. Identity encoding is uncompressed. File gzip estimates are not network transfers.',
      timing: 'resultReadyMs includes rendering and automation waits; scriptExecutionMs is CDP ScriptDuration delta. Bundle measures isolate import wait and synchronous validation/adaptation; absent measures on old artifacts are NOT_VERIFIED.', steps }
    await mkdir(evidenceRoot, { recursive: true })
    await writeFile(resolve(evidenceRoot, 'performance.json'), JSON.stringify(evidence, null, 2) + '\n')
    console.log(JSON.stringify({ browser: evidence.browser, steps: steps.map(({ name, resultReadyMs, scriptTransferBytes, scriptDecodedBodyBytes, bundleMeasures }) => ({ name, resultReadyMs, scriptTransferBytes, scriptDecodedBodyBytes, bundleMeasures })) }, null, 2))
    return evidence
  } finally {
    await browser?.close()
    await new Promise(done => server.httpServer.close(done))
  }
}
if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) {
  const [outputRoot, evidenceRoot, initialRoute] = process.argv.slice(2)
  if (!outputRoot || !evidenceRoot) throw new Error('Usage: node demo/build/browserPerformance.mjs <outputRoot> <evidenceRoot>')
  await measurePerformance(resolve(outputRoot), resolve(evidenceRoot), initialRoute)
}
