import { fileURLToPath } from 'node:url'
// Focused review of the current formal Demo build, with its unchanged Bundle.
import assert from 'node:assert/strict'
import { readFile, mkdir } from 'node:fs/promises'
import { chromium } from 'playwright'
import { previewDemo } from '../../demo/build/preview.mjs'
import { verifyBasisSummary } from './futures_basis_summary_acceptance.mjs'
import { verifyDateEvents } from './date_events_disclosure.mjs'

const report = JSON.parse(await readFile(new URL('../../demo/bundles/basis.json', import.meta.url), 'utf8')).result
const output = new URL('../../.build/futures-basis-summary-review/', import.meta.url)
await mkdir(output, { recursive: true })
const server = await previewDemo(0)
let browser
try {
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
  const page = await context.newPage()
  const errors = []
  page.on('pageerror', e => errors.push(String(e)))
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()) })
  const base = `http://127.0.0.1:${server.httpServer.address().port}/hg-market-state-lab/`
  await context.route('**/*', async route => {
    const request = route.request()
    const url = new URL(request.url())
    if (url.origin !== new URL(base).origin || request.method() !== 'GET' || !['document', 'script', 'stylesheet', 'image', 'font'].includes(request.resourceType())) {
      errors.push(`Unexpected request: ${request.resourceType()} ${url.pathname}`)
      await route.abort()
    } else await route.continue()
  })
  await page.goto(base + '#/research/futures-basis')
  await page.getByTestId('compact-report').waitFor()
  await page.locator('.js-plotly-plot').first().waitFor()
  await verifyBasisSummary(page, report)
  assert.equal(new URL(page.url()).hash, '#/research/futures-basis')
  assert.equal(await page.locator('.js-plotly-plot').count(), 5) // Four histories and one distribution comparison.
  const plots = page.getByTestId('history-charts').locator('.js-plotly-plot')
  const before = await plots.evaluateAll(plots => plots.map(el => el.data.map(t => t.y)))
  assert.deepEqual(before.map(traces => traces.flat().filter(v => v != null).sort((a, b) => a - b)),
    ['basis_value', 'basis_ratio', 'annualized_basis_ratio', 'annualized_basis_value'].map(metric => report.views.history[metric].layers.flatMap(b => b.layer.data).map(m => m.y).filter(v => v != null).sort((a, b) => a - b)))
  for (const mode of ['Calendar Days', 'Trading Days']) {
    await page.getByText(mode, { exact: true }).click()
    await page.waitForFunction(type => [...document.querySelectorAll('[data-testid="history-charts"] .js-plotly-plot')].every(el => el._fullLayout.xaxis.type === type), mode === 'Calendar Days' ? 'date' : 'linear')
    assert.deepEqual(await plots.evaluateAll(plots => plots.map(el => el.data.map(t => t.y))), before)
    assert.ok(await plots.evaluateAll(plots => plots.every(el => el.data.every(t => t.connectgaps === false))))
  }
  const legend = plots.first().locator('.legend .traces').first()
  await legend.click()
  await page.waitForFunction(() => document.querySelector('[data-testid="history-charts"] .js-plotly-plot').data.some(t => t.visible === 'legendonly'))
  await legend.click()
  await verifyDateEvents(page, Object.values(report.views.history).filter(v => v.events.length > 0).length)
  await page.screenshot({ path: fileURLToPath(new URL('demo.png', output)), fullPage: true })
  assert.deepEqual(errors, [])
  console.log(`PASS formal Demo summary, Metric/Bin Width controls, expiry note, narrow scrolling, history values/null breaks, date axis, Legend, Date Events and route (Chromium ${browser.version()})`)
} finally {
  await browser?.close()
  await new Promise(done => server.httpServer.close(done))
}
