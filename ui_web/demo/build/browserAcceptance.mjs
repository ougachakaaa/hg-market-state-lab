import assert from 'node:assert/strict'
import { readFile, mkdir, writeFile } from 'node:fs/promises'
import { chromium } from 'playwright'
import { previewDemo } from './preview.mjs'
import { verifyOverviewLayout } from '../../tests/browser/research_overview_layout.mjs'

export async function verifyBrowser(publicUrl, { reviewOverview = false } = {}) {
  const server = publicUrl ? undefined : await previewDemo(0)
  let browser
  try {
    browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
    const errors = []
    page.on('pageerror', error => errors.push(error.message))
    page.on('console', message => { if (message.type() === 'error' && !message.text().startsWith('Warning: [antd: List]')) errors.push(message.text()) })
    const address = server?.httpServer.address()
    const base = publicUrl ?? `http://127.0.0.1:${address.port}/hg-market-state-lab/`
    await page.route('**/*', async route => {
      const request = route.request()
      const url = new URL(request.url())
      if (url.origin !== new URL(base).origin || !url.pathname.startsWith('/hg-market-state-lab/') ||
        request.method() !== 'GET' || !['document', 'script', 'stylesheet', 'image', 'font'].includes(request.resourceType())) {
        errors.push('Unexpected network request ' + request.resourceType())
        await route.abort()
      } else await route.continue()
    })
    const routes = ['/data/futures-calendar-spread', '/research/calendar-spread-relative-value', '/data', '/data/mo-option-chain', '/data/mo-premium-plane', '/research',
      '/research/futures-basis', '/research/publications', '/backtesting', '/backtesting/futures-roll-long']
    if (reviewOverview) await verifyOverviewLayout(browser, base + '#/research')
    for (const route of routes) {
      await page.goto(base + '#' + route)
      await page.getByText('Static Demo', { exact: true }).waitFor()
      await page.getByRole('heading').first().waitFor()
      assert.equal(await page.getByRole('heading').count() > 0, true, route)
      assert.equal(await page.getByText('静态数据无效，无法展示结果。').count(), 0)
      if (route.includes('mo-option-chain')) await page.getByRole('region', { name: '期权链结果' }).locator('.js-plotly-plot').first().waitFor()
      if (route.includes('mo-premium-plane')) await page.locator('.premium-table tbody tr.ant-table-row').first().waitFor()
      if (route === '/research/publications') await page.getByText('当前静态示例未嵌入 Publication；不代表在线 Publication Store 为空。', { exact: true }).waitFor()
      assert.equal(await page.locator('aside a[href="#/research/publications"]').count(), 0)
    }
    await page.getByTestId('backtest-result').waitFor()
    await page.locator('.js-plotly-plot').first().waitFor()
    await page.getByRole('combobox', { name: '已计算策略结果' }).click()
    await page.getByTitle('到期换入首个后续季月合约（M0 → Q1）', { exact: true }).click()
    await page.getByTestId('backtest-result').waitFor()
    await page.locator('.js-plotly-plot').first().waitFor()
    await page.goto(base + '#/research/futures-basis')
    const introduction = page.getByRole('button', { name: /关于本研究/ })
    assert.equal(await introduction.getAttribute('aria-expanded'), 'false')
    await introduction.click()
    assert.equal(await introduction.getAttribute('aria-expanded'), 'true')
    await page.getByTestId('compact-report').waitFor()
    await page.locator('.js-plotly-plot').first().waitFor()
    await page.reload()
    await page.getByText('Static Demo', { exact: true }).waitFor()
    assert.equal(new URL(page.url()).hash, '#/research/futures-basis')
    await page.evaluate(() => { window.location.hash = '#/research/publications' })
    await page.waitForURL('**/#/research/publications')
    await page.goBack()
    await page.waitForURL('**/#/research/futures-basis')
    // Compare the actual offline chart and tables with the admitted formal capture.
    const captured = JSON.parse(await readFile(new URL('../bundles/calendar_spread_relative_value.json', import.meta.url), 'utf8')).result
    const number = (n, percent = false) => {
      const rounded = (percent ? n * 100 : n).toFixed(percent ? 1 : 2)
      const normalized = Number(rounded) === 0 ? (percent ? '0.0' : '0.00') : rounded
      return `${normalized}${percent ? '%' : ''}`
    }
    const daily = JSON.parse(await readFile(new URL('../bundles/calendar_spread_daily.json', import.meta.url), 'utf8')).result
    await page.goto(base + '#/data/futures-calendar-spread')
    await page.getByText('已查询数据', { exact: true }).waitFor()
    const dailyText = await page.locator('main').textContent()
    assert.ok(dailyText.includes(daily.request.trade_date) && dailyText.includes(daily.request.product_code))
    for (const row of daily.day.observations) {
      for (const contract of [row.near, row.far]) if (contract) { assert.ok(dailyText.includes(contract.contract_code)); assert.ok(dailyText.includes(number(contract.close))) }
      if (row.metrics) for (const metric of ['signed_spread', 'annualized_point_spread', 'annualized_spread_ratio']) assert.ok(dailyText.includes(number(row.metrics[metric].value, metric === 'annualized_spread_ratio')))
    }
    assert.equal(await page.getByRole('button', { name: '查询', exact: true }).count(), 0)
    await page.getByRole('button', { name: '关于本数据' }).click()
    await page.getByText(/真实合约同日 Close/).waitFor()
    await page.goto(base + '#/research/calendar-spread-relative-value')
    const plot = page.locator('.js-plotly-plot').first()
    await plot.waitFor()
    await page.waitForFunction(() => document.querySelector('.js-plotly-plot')?._fullLayout?.xaxis.type === 'linear')
    const domain = [...captured.historical_days.filter(d => d.status === 'open').map(d => d.trade_date), captured.current_day.trade_date]
    async function snapshot() { return plot.evaluate(el => ({ type: el._fullLayout.xaxis.type, x: el.data.map(t => t.x), y: el.data.map(t => t.y), range: Array.from(el._fullLayout.xaxis.range) })) }
    // Contract boundaries produce separate traces; null separators never become zero.
    function assertPoints(state, pair, calendar) {
      const points = state.x.flatMap((xs, i) => xs.map((x, j) => [x, state.y[i][j]])).filter(([x, y]) => x !== null && y !== null)
      const expected = [...pair.samples.map(s => [calendar ? s.trade_date : domain.indexOf(s.trade_date), s.metric.value]), [calendar ? captured.current_day.trade_date : domain.indexOf(captured.current_day.trade_date), captured.current_day.observations[captured.pairs.indexOf(pair)].metrics[captured.metric].value]]
      assert.deepEqual(points, expected)
    }
    assertPoints(await snapshot(), captured.pairs[0], false)
    for (const mode of ['Calendar Days', 'Trading Days']) {
      await page.getByText(mode, { exact: true }).click()
      await page.waitForFunction(type => document.querySelector('.js-plotly-plot')._fullLayout.xaxis.type === type, mode === 'Calendar Days' ? 'date' : 'linear')
      const state = await snapshot(); assertPoints(state, captured.pairs[0], mode === 'Calendar Days')
      await plot.scrollIntoViewIfNeeded()
      await plot.locator('[data-title="Zoom"]').click()
      // Wait for scroll/layout to settle before a real mouse drag.
      await plot.locator('.nsewdrag').evaluate(el => new Promise(done => {
        let last = '', stable = 0
        function frame() { const b = el.getBoundingClientRect(), key = `${b.x},${b.y},${scrollY}`; stable = key === last ? stable + 1 : 0; last = key; if (stable >= 8) done(); else requestAnimationFrame(frame) }
        frame()
      }))
      async function drag(a, b) {
        const box = await plot.locator('.nsewdrag').boundingBox()
        await page.mouse.move(box.x + box.width * a, box.y + box.height * .5); await page.mouse.down()
        await page.mouse.move(box.x + box.width * b, box.y + box.height * .5, { steps: 12 }); await page.mouse.up()
      }
      await drag(.2, .7)
      await page.waitForFunction(old => JSON.stringify(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range) !== JSON.stringify(old), state.range)
      const zoomed = (await snapshot()).range
      await plot.locator('[data-title="Pan"]').click(); await drag(.5, .6)
      await page.waitForFunction(old => JSON.stringify(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range) !== JSON.stringify(old), zoomed)
      await plot.locator('[data-title="Reset axes"]').click()
      await page.waitForFunction(old => JSON.stringify(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range) === JSON.stringify(old), state.range)
    }
    await page.getByRole('combobox', { name: '合约对', exact: true }).click()
    await page.locator('.ant-select-item-option[title="Q1/Q2"]').click()
    await page.waitForFunction(() => document.querySelector('.js-plotly-plot').layout.title.text.includes('Q1/Q2'))
    assertPoints(await snapshot(), captured.pairs[5], false)
    await page.getByRole('button', { name: '四组历史分布与分位点数值（Quantile）', exact: true }).click()
    const body = await page.locator('main').textContent()
    for (const assessment of [captured.pairs[5].matching_stage, captured.pairs[5].all_stages]) assert.ok(body.includes(number(assessment.percentile.result.query_results[0].percentile, true)))
    for (const d of captured.pairs[5].distributions) if (d.quantile) {
      for (const [, value] of d.quantile.result.points_and_values) assert.ok(body.includes(number(value, captured.unit === 'decimal_ratio')))
    }
    // Histogram was explicitly not requested; the static reader must not manufacture it.
    assert.equal(captured.request.histogram_edges, null)
    assert.equal(await page.getByText('显式边界直方图（Histogram）', { exact: true }).count(), 0)
    assert.ok(body.includes('无有效历史样本'), 'Actual empty stages remain visible')
    await page.getByRole('button', { name: /历史样本明细/ }).click()
    await page.getByRole('button', { name: '样本解释与来源限制' }).click()
    assert.equal(await page.getByRole('button', { name: '开始研究', exact: true }).count(), 0)
    await mkdir('.build/demo-review', { recursive: true })
    await page.screenshot({ path: '.build/demo-review/calendar-spread-real.png', fullPage: true })
    await writeFile('.build/demo-review/calendar-spread-acceptance.json', JSON.stringify({ routes: routes.length, product: captured.request.product_code, request: captured.request, allStageSamples: captured.pairs.map(p => p.samples.length), errors, result: 'PASS' }, null, 2) + '\n')
    assert.deepEqual(errors, [])
    console.log('PASS Demo browser ten routes, Calendar Spread exact values and both date axes, local interactions, history and static network isolation')
  } finally {
    if (browser) await browser.close()
    if (server) await new Promise(done => server.httpServer.close(done))
  }
}
