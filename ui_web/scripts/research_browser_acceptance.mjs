// WP3-A presentation acceptance. Auth and normal reads use the smoke's real backend.
// Explicitly intercepted edge states are deterministic UI fixtures, not live research.
import assert from 'node:assert/strict'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

export async function researchAcceptance(page, output) {
  const origin = 'http://127.0.0.1:5173'
  const errors = []
  const onError = error => errors.push(String(error))
  page.on('pageerror', onError)
  for (const viewport of [{ width: 1440, height: 900 }, { width: 1024, height: 768 }]) {
    await page.setViewportSize(viewport)
    const directory = resolve(output, 'wp3a', `${viewport.width}x${viewport.height}`)
    await mkdir(directory, { recursive: true })
    async function capture(name, target) {
      if (target) await target.evaluate(el => el.scrollIntoView({ block: 'start' }))
      await page.evaluate(() => document.fonts.ready)
      assert.equal(await page.getByRole('heading', { level: 2 }).count(), 1, 'one main heading')
      const geometry = await page.evaluate(() => {
        const content = document.querySelector('.ant-layout-content').getBoundingClientRect()
        const sider = document.querySelector('.ant-layout-sider').getBoundingClientRect()
        return { overflow: document.documentElement.scrollWidth - innerWidth, contentLeft: content.left, siderRight: sider.right }
      })
      assert.ok(geometry.overflow <= 1, `${name}: no page overflow: ${JSON.stringify(geometry)}`)
      assert.ok(geometry.contentLeft >= geometry.siderRight - 1, `${name}: sidebar does not obscure content`)
      await page.screenshot({ path: resolve(directory, `${name}.png`), fullPage: true })
      if (target) await page.screenshot({ path: resolve(directory, `${name}-viewport.png`) })
    }
    await page.goto(`${origin}/research`)
    const online = page.getByRole('region', { name: '在线能力发现' })
    await online.getByText('Index Trailing Cumulative Return Research', { exact: true }).waitFor()
    await capture('workspace-initial')
    await online.getByRole('button', { name: '查看详情' }).click()
    const detail = page.getByRole('region', { name: '所选研究详情' })
    await detail.getByText(/supported · live readiness: not_probed/).waitFor()
    assert.equal(await online.getByRole('button', { pressed: true }).count(), 1)
    await capture('workspace-online', detail)
    // Native Collapse is keyboard operable; disclosure must not issue another read.
    const requests = []
    const record = req => { if (req.url().includes('/api/research')) requests.push(req.url()) }
    page.on('request', record)
    const disclosure = detail.getByRole('button', { name: '完整能力描述（原始字段）' })
    await disclosure.focus()
    await page.keyboard.press('Enter')
    await detail.locator('pre').waitFor()
    assert.equal(requests.length, 0)
    await capture('workspace-descriptor', disclosure)
    page.off('request', record)
    const local = page.getByRole('region', { name: '本地研究与离线工作流' })
    await local.getByRole('button', { name: '查看详情' }).nth(0).click()
    await detail.getByText(/observe_price_segments/).waitFor()
    await capture('workspace-local', detail)
    await local.getByRole('button', { name: '查看详情' }).nth(1).click()
    await detail.getByText(/futures_basis_report.py/).waitFor()
    assert.ok(await detail.getByRole('button', { name: '打开 Futures Basis Research' }).isVisible())
    await capture('workspace-offline', detail)
    for (const [name, body, status] of [
      ['catalog-empty', [], 200],
      ['catalog-error', { error: { kind: 'internal_error', detail: 'safe', param: null } }, 500],
    ]) {
      await page.route('**/api/research/capabilities', route => route.fulfill({ status, json: body }))
      await page.goto(`${origin}/research`)
      await page.getByText(status === 200 ? '暂无已发布的在线能力。' : '在线能力目录暂不可用', { exact: true }).waitFor()
      assert.ok(await page.getByText('Price Segmentation', { exact: true }).isVisible())
      await capture(name)
      await page.unroute('**/api/research/capabilities')
    }
    await page.getByRole('button', { name: '打开研究结果浏览' }).click()
    const publicationList = page.locator('.ant-card').filter({ has: page.getByText('Publications', { exact: true }) }).first()
    await publicationList.getByRole('button', { name: '选择', exact: true }).first().waitFor()
    await capture('explorer-list')
    await publicationList.getByRole('button', { name: '选择', exact: true }).first().click()
    await page.getByRole('heading', { name: 'Jobs 与 Analysis' }).waitFor()
    const jobs = page.locator('.ant-card').filter({ has: page.getByText(/^Job \d+ —/) })
    assert.ok(await jobs.count() >= 2, 'multiple published Jobs')
    await capture('explorer-jobs', page.getByText(/^Job 1 —/))
    const distribution = page.locator('.ant-list-item').filter({ hasText: 'distribution' }).first()
    const response = page.waitForResponse(res => /\/analyses\//.test(res.url()))
    await distribution.getByRole('button', { name: '选择 Analysis' }).click()
    const analysisResponse = await response
    const analysisUrl = analysisResponse.url()
    const original = await analysisResponse.json()
    await page.getByText('观察总体与覆盖（原始比例）', { exact: true }).waitFor()
    await capture('explorer-analysis', page.getByText('所选 Analysis', { exact: true }))
    await page.getByRole('button', { name: '展开覆盖与来源证据' }).click()
    await page.getByText('input_fingerprint', { exact: true }).waitFor()
    await capture('explorer-statistics-coverage', page.getByText('观察总体与覆盖（原始比例）', { exact: true }))
    const table = page.locator('.ant-table-content').last()
    const scroll = await table.evaluate(el => { el.scrollLeft = el.scrollWidth; return { width: el.clientWidth, total: el.scrollWidth, left: el.scrollLeft } })
    if (scroll.total > scroll.width) assert.ok(scroll.left > 0, 'overflowing technical table scrolls internally')
    else assert.equal(scroll.left, 0, 'table fits without unnecessary scrolling')
    await page.getByRole('button', { name: 'count', exact: true }).click()
    await page.locator('.js-plotly-plot').waitFor()
    await capture('explorer-chart', page.locator('.js-plotly-plot'))
    // Keep identity and all numerical facts; simulate absent coverage only.
    const missing = structuredClone(original)
    missing.data.coverage = null
    await page.route(analysisUrl, route => route.fulfill({ json: missing }))
    await page.getByRole('button', { name: '关闭 Analysis' }).click()
    await distribution.getByRole('button', { name: '选择 Analysis' }).click()
    await page.getByText('Coverage 不可用', { exact: true }).waitFor()
    await capture('explorer-missing-coverage-fixture', page.getByText('Coverage 不可用', { exact: true }))
    await page.unroute(analysisUrl)
    // A valid categorical View made unsupported by numeric x coordinates.
    const viewPromise = page.waitForResponse(res => /\/views\//.test(res.url()))
    await page.getByRole('button', { name: 'count', exact: true }).click()
    const viewResponse = await viewPromise
    const unsupported = await viewResponse.json()
    unsupported.data.axes[0].coordinate = { kind: 'number', unit: 'index' }
    unsupported.data.layers[0].layer.x = { kind: 'number', unit: 'index' }
    unsupported.data.layers[0].layer.data = unsupported.data.layers[0].layer.data.map((mark, i) => ({ ...mark, x: i }))
    await page.route(viewResponse.url(), route => route.fulfill({ json: unsupported }))
    await page.getByRole('button', { name: '关闭 Analysis' }).click()
    await distribution.getByRole('button', { name: '选择 Analysis' }).click()
    await page.getByRole('button', { name: 'count', exact: true }).click()
    await page.getByText('当前渲染器不支持此 View。', { exact: true }).waitFor()
    await capture('explorer-unsupported-view-fixture', page.getByText('当前渲染器不支持此 View。', { exact: true }))
    await page.unroute(viewResponse.url())
    for (const [name, json, status] of [
      ['explorer-empty-fixture', { data: [], next_cursor: null }, 200],
      ['explorer-error-fixture', { error: { kind: 'unavailable', detail: 'safe', param: null } }, 503],
    ]) {
      await page.route('**/api/research/publications', route => route.fulfill({ status, json }))
      await page.goto(`${origin}/research/publications`)
      await page.getByText(status === 200 ? 'Publication Store 为空。' : 'Publication 存储或来源不可用。', { exact: true }).waitFor()
      await capture(name)
      await page.unroute('**/api/research/publications')
    }
    console.log(`PASS: WP3-A ${viewport.width}×${viewport.height} screenshots, disclosure, identity, table scroll and layout (${directory})`)
  }
  await page.setViewportSize({ width: 1440, height: 900 })
  page.off('pageerror', onError)
  assert.deepEqual(errors, [], 'no browser exceptions')
}
