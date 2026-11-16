import { verifyBasisDistribution, verifyDistributionInteractions } from './futures_basis_distribution_acceptance.mjs'
import assert from 'node:assert/strict'

// Compare reader cells directly with retained producer results, never new statistics.
export async function verifyBasisSummary(page, report) {
  const note = page.getByText('合约到期日的剩余期限 D=0，年化基差按研究定义主动留空，并非行情数据错误；原始基差仍然保留。', { exact: true })
  await note.scrollIntoViewIfNeeded()
  assert.equal(await note.isVisible(), true)
  assert.equal(await note.count(), 1)
  assert.equal(await note.locator('xpath=ancestor::*[contains(@class,"ant-collapse")]').count(), 0)
  const summary = page.getByRole('region', { name: '统计摘要' })
  const format = (value, unit) => {
    if (value == null) return '不可用'
    if (unit !== 'decimal_ratio') return String(value)
    const rounded = (value * 100).toFixed(1)
    return `${Number(rounded) === 0 ? '0.0' : rounded}%`
  }
  function expected(metric) {
    return ['M0', 'M1', 'Q1', 'Q2'].map(slot => {
      const d = report.distributions.find(d => d.request.slot === slot && d.request.metric === metric)
      const cell = (method, point) => {
        const m = d?.methods.find(m => m.spec.method === method)
        if (m?.failure_category) return `不可用（${m.failure_category}）`
        if (!d?.binding.length || !m?.result || m.result.method !== method || m.result.sample_count <= 0) return '不可用'
        return format(method === 'mean' ? m.result.value : m.result.points_and_values?.find(([p]) => p === point)?.[1], m.result.unit)
      }
      return [slot, d ? String(d.binding.length) : '不可用', ...[0, .25, .5, .75, 1].map(p => cell('quantile', p)), cell('mean')]
    })
  }
  async function check(metric) {
    const cells = await summary.locator('tbody tr.ant-table-row').evaluateAll(rows => rows.map(row => [...row.querySelectorAll('td')].map(td => td.textContent)))
    assert.deepEqual(cells, expected(metric))
  }
  await check('basis_value')
  for (const metric of ['basis_ratio', 'annualized_basis_ratio', 'basis_value']) {
    await page.getByRole('combobox', { name: 'Distribution metric' }).click()
    await page.locator('.ant-select-item-option-content').getByText(metric, { exact: true }).click()
    await check(metric)
  }
  await verifyBasisDistribution(page, report)
  await verifyDistributionInteractions(page)
  await check('basis_value')
  // Let the portal's exit animation finish before resizing; its old absolute
  // position can temporarily exceed the narrower viewport.
  await page.locator('.ant-select-dropdown:visible').waitFor({ state: 'hidden' })
  for (const width of [1440, 1024, 390]) {
    await page.setViewportSize({ width, height: 900 })
    await summary.scrollIntoViewIfNeeded()
    if (await page.getByTestId('distribution-comparison').count()) await page.waitForFunction(() => {
      const el = document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot')
      return Math.abs(el._fullLayout.width - el.parentElement.clientWidth) < 2
    })
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false)
    const frame = summary.locator('.ant-table-content')
    assert.ok(await frame.evaluate(el => ['auto', 'scroll'].includes(getComputedStyle(el).overflowX)))
    await check('basis_value')
  }
  await page.setViewportSize({ width: 1440, height: 1000 })
}
