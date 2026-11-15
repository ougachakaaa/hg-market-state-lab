import assert from 'node:assert/strict'
import { chromium } from 'playwright'
import { previewDemo } from './preview.mjs'

export async function verifyBrowser(publicUrl) {
  const server = publicUrl ? undefined : await previewDemo(0)
  let browser
  try {
    browser = await chromium.launch({ headless: true })
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
    const routes = ['/data', '/data/mo-option-chain', '/data/mo-premium-plane', '/research',
      '/research/futures-basis', '/research/publications', '/backtesting', '/backtesting/futures-roll-long']
    for (const route of routes) {
      await page.goto(base + '#' + route)
      await page.getByText('Static Demo', { exact: true }).waitFor()
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
    await page.getByTitle('expiry_to_Q1_v1', { exact: true }).click()
    await page.getByTestId('backtest-result').waitFor()
    await page.locator('.js-plotly-plot').first().waitFor()
    await page.goto(base + '#/research/futures-basis')
    const introduction = page.getByRole('button', { name: /关于本研究/ })
    assert.equal(await introduction.getAttribute('aria-expanded'), 'false')
    await introduction.click()
    assert.equal(await introduction.getAttribute('aria-expanded'), 'true')
    await page.locator('[id="section-0"]').waitFor()
    await page.locator('.js-plotly-plot').first().waitFor()
    await page.reload()
    await page.getByText('Static Demo', { exact: true }).waitFor()
    assert.equal(new URL(page.url()).hash, '#/research/futures-basis')
    await page.evaluate(() => { window.location.hash = '#/research/publications' })
    await page.waitForURL('**/#/research/publications')
    await page.goBack()
    await page.waitForURL('**/#/research/futures-basis')
    assert.deepEqual(errors, [])
    console.log('PASS Demo browser eight routes, local interactions, history and static network isolation')
  } finally {
    if (browser) await browser.close()
    if (server) await new Promise(done => server.httpServer.close(done))
  }
}
