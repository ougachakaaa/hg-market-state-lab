import assert from 'node:assert/strict'
import { chromium } from 'playwright'
import { previewDemo } from '../../demo/build/preview.mjs'
import { verifyDateEvents } from './date_events_disclosure.mjs'
const server = await previewDemo(0)
const browser = await chromium.launch({ headless: true })
try {
 const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
 let requests = 0
 page.on('request', r => { if (/fetch|xhr/.test(r.resourceType())) requests++ })
 const base = `http://127.0.0.1:${server.httpServer.address().port}/hg-market-state-lab/`
 for (const [route, count] of [['research/futures-basis', 3], ['backtesting/futures-roll-long', 2]]) {
  await page.goto(base + '#/' + route)
  await page.locator('.nsewdrag').first().waitFor()
  if (count === 3) await page.waitForFunction(() => document.querySelectorAll('section[aria-label="Date events"]').length === 3)
  const plots = count === 3 ? page.locator('[data-testid="history-charts"] .js-plotly-plot') : page.locator('.js-plotly-plot')
  const markers = () => plots.evaluateAll(els => els.map(el => ({ shapes: el.layout.shapes, annotations: el.layout.annotations, data: el.data })))
  const before = await markers()
  await verifyDateEvents(page, count)
  assert.deepEqual(await markers(), before)
  await page.getByText('Calendar Days', { exact: true }).click()
  await page.getByText('Trading Days', { exact: true }).click()
  if (count === 2) {
   await page.getByRole('combobox', { name: '已计算策略结果' }).click()
   await page.locator('.ant-select-item-option').filter({ hasText: 'Q1' }).click()
   await verifyDateEvents(page, 2)
  }
  console.log('PASS real Demo Plotly Date Events: ' + route)
 }
 assert.equal(requests, 0)
} finally {
 await browser.close()
 await new Promise(done => server.httpServer.close(done))
}
