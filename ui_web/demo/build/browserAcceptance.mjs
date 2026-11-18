import assert from 'node:assert/strict'
import { readFile, mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { previewDemo } from './preview.mjs'
import { verifyOverviewLayout } from '../../tests/browser/research_overview_layout.mjs'

export async function assertRouteResult(page, route) {
  const main = page.locator('main')
  switch (route) {
    case '/roadmap':
      await main.getByRole('heading', { name: '策略研究地图', exact: true }).waitFor()
      await main.getByRole('region', { name: '研究详情' }).waitFor()
      await main.locator('.react-flow__node').first().waitFor()
      break
    case '/data':
      await main.getByRole('heading', { name: '数据总览', exact: true }).waitFor()
      for (const name of ['MO Option Chain', 'MO Premium Plane', 'Futures Calendar Spread']) await main.getByRole('button', { name: '打开 ' + name, exact: true }).waitFor()
      break
    case '/backtesting':
      await main.getByRole('heading', { name: '回测总览', exact: true }).waitFor()
      await main.getByRole('button', { name: '查看回测', exact: true }).waitFor()
      break
    case '/research':
      await main.getByRole('heading', { name: '研究总览', exact: true }).waitFor()
      assert.equal(await main.getByRole('button', { name: /^查看.*研究/ }).count(), 2)
      await main.getByRole('note').getByText(/catalog/).waitFor()
      break
    case '/data/futures-calendar-spread':
      await main.getByText('已查询数据', { exact: true }).waitFor()
      assert.equal(await main.locator('tbody tr.ant-table-row').count(), 6)
      break
    case '/research/calendar-spread-relative-value':
      await main.getByText('当前价差相对于可比历史样本处于什么位置？', { exact: true }).waitFor()
      await main.getByText('同到期阶段的历史百分位', { exact: true }).waitFor()
      await main.getByText('全部阶段的历史百分位', { exact: true }).waitFor()
      await main.locator('.js-plotly-plot').first().waitFor()
      break
    case '/data/mo-option-chain':
      await page.getByRole('region', { name: '期权链结果' }).locator('.js-plotly-plot').first().waitFor()
      break
    case '/data/mo-premium-plane':
      await page.locator('.premium-table tbody tr.ant-table-row').first().waitFor()
      break
    case '/research/futures-basis':
      await page.getByTestId('compact-report').waitFor()
      await main.locator('.js-plotly-plot').first().waitFor()
      break
    case '/research/publications':
      await page.getByText('当前静态示例未嵌入 Publication；不代表在线 Publication Store 为空。', { exact: true }).waitFor()
      break
    case '/backtesting/futures-roll-long':
      await page.getByTestId('backtest-result').waitFor()
      await main.locator('.js-plotly-plot').first().waitFor()
      break
    default: throw new Error('Missing valid-result assertion: ' + route)
  }
}

export async function verifyBrowser(publicUrl, { reviewOverview = false, outputRoot, reviewRoot = resolve('.build/demo-review') } = {}) {
  const server = publicUrl ? undefined : await previewDemo(0, { outputRoot })
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
    await page.goto(base)
    await page.waitForURL('**/#/roadmap')
    await assertRouteResult(page, '/roadmap')
    const routes = ['/roadmap', '/data/futures-calendar-spread', '/research/calendar-spread-relative-value', '/data', '/data/mo-option-chain', '/data/mo-premium-plane', '/research',
      '/research/futures-basis', '/research/publications', '/backtesting', '/backtesting/futures-roll-long']
    if (reviewOverview) await verifyOverviewLayout(browser, base + '#/research', { output: reviewRoot })
    for (const route of routes) {
      await page.goto(base + '#' + route)
      await page.getByText('Static Demo', { exact: true }).waitFor()
      await assertRouteResult(page, route)
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
    const basis = JSON.parse(await readFile(new URL('../bundles/basis.json', import.meta.url), 'utf8'))
    const source = page.getByRole('button', { name: '数据来源', exact: true })
    assert.equal(await source.getAttribute('aria-expanded'), 'false')
    await source.click()
    await page.getByText(new RegExp(basis.source.description.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))).waitFor()
    assert.equal(await page.getByTestId('history-charts').locator('.js-plotly-plot').count(), 4)
    const titles = await page.locator('.js-plotly-plot').evaluateAll(plots => plots.map(plot => plot.layout.title.text))
    assert.ok(titles.includes('历史年化基差点（点/年）'))
    for (const title of ['历史基差（点）', '历史基差率（%）', '历史年化基差率（%）']) assert.ok(titles.includes(title), title)
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
    await page.getByText('跨期比较使用近端减远端收盘价，以两合约最后交易日间隔年化；期现比较使用期货减同日指数收盘价，以期货剩余自然日数年化。年化价差是价格关系，不代表实际收益率或交易指令。', { exact: true }).waitFor()
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
    await mkdir(reviewRoot, { recursive: true })
    await page.screenshot({ path: resolve(reviewRoot, 'calendar-spread-real.png'), fullPage: true })
    assert.deepEqual(errors, [])
    await verifyLoadingLifecycle(browser, base)
    await writeFile(resolve(reviewRoot, 'calendar-spread-acceptance.json'), JSON.stringify({ routes: routes.length, product: captured.request.product_code, request: captured.request, allStageSamples: captured.pairs.map(p => p.samples.length), errors, result: 'PASS' }, null, 2) + '\n')
    console.log('PASS Demo browser ten routes, Calendar Spread exact values and both date axes, local interactions, history and static network isolation')
  } finally {
    if (browser) await browser.close()
    if (server) await new Promise(done => server.httpServer.close(done))
  }
}

const bundleAsset = (url, id) => new URL(url).pathname.includes(`/assets/${id}-`)
export async function verifyLoadingLifecycle(browser, base) {
  const contexts = []
  async function fresh(intercept = async route => route.continue()) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
    contexts.push(context)
    const page = await context.newPage()
    page.setDefaultTimeout(15000)
    await page.route('**/*', async route => {
      const request = route.request(), url = new URL(request.url())
      assert.equal(url.origin, new URL(base).origin)
      assert.ok(url.pathname.startsWith('/hg-market-state-lab/'))
      assert.equal(request.method(), 'GET')
      assert.ok(['document', 'script', 'stylesheet', 'image', 'font'].includes(request.resourceType()))
      await intercept(route)
    })
    return page
  }
  const loading = page => page.getByText('正在加载静态展示资源…', { exact: true }).first().waitFor()
  const navigate = (page, path) => page.evaluate(path => { location.hash = '#' + path }, path)
  try {
    let releaseDaily, dailyRequested
    const dailyGate = new Promise(done => { releaseDaily = done })
    const requested = new Promise(done => { dailyRequested = done })
    const counts = new Map()
    const page = await fresh(async route => {
      const url = route.request().url()
      if (url.endsWith('.js')) counts.set(url, (counts.get(url) ?? 0) + 1)
      if (bundleAsset(url, 'calendar_spread_daily')) { dailyRequested(); await dailyGate }
      await route.continue()
    })
    await page.goto(base + '#/research')
    await assertRouteResult(page, '/research')
    await navigate(page, '/data/futures-calendar-spread')
    await requested
    await loading(page)
    assert.equal(await page.getByRole('heading', { name: '研究总览', exact: true }).count(), 0)
    assert.equal(await page.getByText('已查询数据', { exact: true }).count(), 0)
    await navigate(page, '/data')
    await assertRouteResult(page, '/data')
    releaseDaily()
    await navigate(page, '/data/futures-calendar-spread')
    await assertRouteResult(page, '/data/futures-calendar-spread')
    await navigate(page, '/research')
    await assertRouteResult(page, '/research')
    await navigate(page, '/data/futures-calendar-spread')
    await assertRouteResult(page, '/data/futures-calendar-spread')
    for (const [url, count] of counts) if (bundleAsset(url, 'catalog') || bundleAsset(url, 'calendar_spread_daily')) assert.equal(count, 1, 'Validated resources reused on return')

    let releaseQ1, q1Requested
    const q1Gate = new Promise(done => { releaseQ1 = done })
    const requestedQ1 = new Promise(done => { q1Requested = done })
    let m1Loads = 0, q1Loads = 0
    const backtest = await fresh(async route => {
      if (bundleAsset(route.request().url(), 'expiry_to_M1_v1')) m1Loads++
      if (bundleAsset(route.request().url(), 'expiry_to_Q1_v1')) { q1Loads++; q1Requested(); await q1Gate }
      await route.continue()
    })
    await backtest.goto(base + '#/backtesting/futures-roll-long')
    await assertRouteResult(backtest, '/backtesting/futures-roll-long')
    assert.equal(m1Loads, 1); assert.equal(q1Loads, 0)
    async function select(label) {
      await backtest.getByRole('combobox', { name: '已计算策略结果' }).click()
      await backtest.getByTitle(label, { exact: true }).click()
    }
    await select('到期换入首个后续季月合约（M0 → Q1）')
    await requestedQ1
    await loading(backtest)
    assert.equal(await backtest.getByTestId('backtest-result').count(), 0)
    await select('到期换入次月合约（M0 → M1）')
    releaseQ1()
    await assertRouteResult(backtest, '/backtesting/futures-roll-long')
    const m1 = JSON.parse(await readFile(new URL('../bundles/expiry_to_M1_v1.json', import.meta.url), 'utf8'))
    await backtest.getByTestId('backtest-result').getByText((m1.result.summary.gross_return * 100).toFixed(1) + '%', { exact: true }).waitFor()
    await select('到期换入首个后续季月合约（M0 → Q1）')
    await assertRouteResult(backtest, '/backtesting/futures-roll-long')
    assert.equal(m1Loads, 1); assert.equal(q1Loads, 1)

    for (const asset of ['DailySpread', 'calendar_spread_daily']) {
      let attempts = 0
      const failed = await fresh(async route => {
        if (bundleAsset(route.request().url(), asset) && ++attempts === 1) await route.abort('failed')
        else await route.continue()
      })
      await failed.goto(base + '#/data/futures-calendar-spread')
      await failed.getByText('静态资源加载失败，请重试。', { exact: true }).waitFor()
      assert.equal(await failed.getByText('已查询数据', { exact: true }).count(), 0)
      assert.equal(attempts, 1)
      await failed.getByRole('button', { name: '重试静态资源' }).click()
      await assertRouteResult(failed, '/data/futures-calendar-spread')
      assert.equal(attempts, 2)
    }
    const invalid = JSON.parse(await readFile(new URL('../bundles/calendar_spread_daily.json', import.meta.url), 'utf8'))
    invalid.result = {}
    const corrupt = await fresh(async route => {
      if (bundleAsset(route.request().url(), 'calendar_spread_daily')) await route.fulfill({ contentType: 'application/javascript', body: 'export default ' + JSON.stringify(invalid) })
      else await route.continue()
    })
    await corrupt.goto(base + '#/data/futures-calendar-spread')
    await corrupt.getByText('静态结果未通过校验，已停止展示。', { exact: true }).waitFor()
    assert.equal(await corrupt.getByText('已查询数据', { exact: true }).count(), 0)
    await corrupt.getByRole('button', { name: '重试静态资源' }).click()
    await corrupt.getByText('静态结果未通过校验，已停止展示。', { exact: true }).waitFor()
    await navigate(corrupt, '/data')
    await assertRouteResult(corrupt, '/data')
    console.log('PASS actual-artifact loading, stale isolation, M1/Q1 lazy loading, cache, component/Bundle failure retry and invalid Result rejection')
  } finally { await Promise.all(contexts.map(context => context.close())) }
}
