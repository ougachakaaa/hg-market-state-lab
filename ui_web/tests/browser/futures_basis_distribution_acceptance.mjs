import assert from 'node:assert/strict'

const presets = {
  basis_value: { default: 10, widths: [5, 10, 20, 50], scale: 1 },
  basis_ratio: { default: .1, widths: [.1, .2, .5], scale: 100 },
  annualized_basis_ratio: { default: 5, widths: [2.5, 5, 10, 20], scale: 100 },
}
const slots = ['M0', 'M1', 'Q1', 'Q2']

export async function verifyBasisDistribution(page, report) {
  const plot = page.getByTestId('distribution-comparison').locator('.js-plotly-plot')
  const summary = page.getByRole('region', { name: '统计摘要' })
  for (const [metric, preset] of Object.entries(presets)) {
    await page.getByRole('combobox', { name: 'Distribution metric' }).click()
    await page.locator('.ant-select-item-option-content').getByText(metric, { exact: true }).click()
    const unit = metric === 'basis_value' ? '点' : '个百分点'
    assert.ok((await page.getByRole('combobox', { name: 'Bin width' }).evaluate(el => el.closest('.ant-select').textContent)).includes(`${preset.default} ${unit}`))
    const beforeSummary = await summary.textContent()
    const distributions = report.distributions.filter(d => d.request.metric === metric)
    // Existing static empty fixtures intentionally have no sample associations.
    if (distributions.length !== 4) {
      assert.equal(await plot.count(), 0)
      assert.ok((await page.getByRole('status').textContent()).includes('展示数据不一致'))
      continue
    }
    const hasSamples = distributions.some(d => d.binding.length)
    if (!hasSamples) {
      assert.equal(await plot.count(), 0)
      assert.ok((await page.getByRole('status').textContent()).includes('无有效样本'))
      continue
    }
    for (const width of preset.widths) {
      await page.getByRole('combobox', { name: 'Bin width' }).click()
      await page.locator('.ant-select-item-option-content').getByText(`${width} ${unit}`, { exact: true }).click()
      await page.waitForFunction(revision => document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot')?._fullLayout.xaxis.uirevision === revision, `${metric}/${width}`)
      const traces = await plot.evaluate(el => el.data.map(t => ({ name: t.name, x: t.x, y: t.y, customdata: t.customdata, color: t.line.color, hovertemplate: t.hovertemplate })))
      assert.deepEqual(traces.map(t => t.name), slots)
      assert.deepEqual(traces.map(t => t.color), ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
      let sharedX
      for (const [i, trace] of traces.entries()) {
        const distribution = distributions.find(d => d.request.slot === slots[i])
        const values = report.views.history[metric].layers.find(b => b.id === slots[i]).layer.data.map(p => p.y).filter(v => v !== null)
        assert.equal(values.length, distribution.binding.length)
        const formal = distribution.methods.find(m => m.spec.method === 'interval_count')
        if (!values.length || formal?.failure_category) {
          assert.deepEqual(trace.y, [null])
          continue
        }
        if (sharedX) assert.deepEqual(trace.x, sharedX)
        sharedX = trace.x
        let total = 0
        for (let j = 0; j < trace.x.length; j += 2) {
          const left = trace.x[j]; const right = trace.x[j + 1]
          const final = j + 2 === trace.x.length
          const count = values.filter(v => v >= left && (final ? v <= right : v < right)).length
          const metadata = trace.customdata[j]
          assert.equal(metadata[1], count)
          assert.equal(metadata[2], count / values.length)
          assert.equal(metadata[3], values.length)
          assert.equal(trace.y[j], count / values.length)
          assert.deepEqual(trace.customdata[j + 1], metadata)
          assert.ok(metadata[0].endsWith(final ? ']' : ')'))
          assert.ok(Math.abs((right - left) - width / preset.scale) <= Number.EPSILON * Math.max(1, Math.abs(left), Math.abs(right)))
          total += count
        }
        assert.equal(total, distribution.binding.length)
        assert.ok(trace.hovertemplate.includes('Count：%{customdata[1]:d}'))
        assert.ok(trace.hovertemplate.includes('Frequency：%{customdata[2]:.1%}'))
        assert.ok(trace.hovertemplate.includes('Eligible N：%{customdata[3]:d}'))
      }
      assert.equal(await summary.textContent(), beforeSummary)
      // Legend visibility changes neither the traces nor their common edges.
      const before = await plot.evaluate(el => el.data.map(t => t.x))
      await plot.locator('.legend .traces').first().click()
      await page.waitForFunction(() => document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot').data[0].visible === 'legendonly')
      assert.deepEqual(await plot.evaluate(el => el.data.map(t => t.x)), before)
      assert.equal(await plot.evaluate(el => el.data[1].visible === 'legendonly'), false)
      await plot.locator('.legend .traces').first().click()
      await page.waitForFunction(() => document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot').data[0].visible !== 'legendonly')
    }
    console.log(`PASS distribution ${metric}: N=${distributions.map(d => d.binding.length).join('/')} conserved for all preset widths`)
  }
  await page.getByRole('combobox', { name: 'Distribution metric' }).click()
  await page.locator('.ant-select-item-option-content').getByText('basis_value', { exact: true }).click()
  await page.locator('.ant-select-dropdown:visible').waitFor({ state: 'hidden' })
}

export async function verifyDistributionInteractions(page) {
  const plot = page.getByTestId('distribution-comparison').locator('.js-plotly-plot')
  if (!await plot.count()) return // Explicit all-empty/invalid fixtures have no plot.
  await plot.scrollIntoViewIfNeeded()
  await plot.locator('.nsewdrag').waitFor()
  const initial = await plot.evaluate(el => Array.from(el._fullLayout.xaxis.range))
  async function drag(from, to) {
    const box = await plot.locator('.nsewdrag').boundingBox()
    await page.mouse.move(box.x + box.width * from, box.y + box.height * .35)
    await page.mouse.down()
    await page.mouse.move(box.x + box.width * to, box.y + box.height * .75, { steps: 12 })
    await page.mouse.up()
  }
  await drag(.2, .75)
  await page.waitForFunction(before => JSON.stringify(document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot')._fullLayout.xaxis.range) !== JSON.stringify(before), initial)
  await plot.locator('[data-title="Pan"]').click()
  const zoomed = await plot.evaluate(el => Array.from(el._fullLayout.xaxis.range))
  await drag(.45, .65)
  await page.waitForFunction(before => JSON.stringify(document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot')._fullLayout.xaxis.range) !== JSON.stringify(before), zoomed)
  await plot.locator('[data-title="Reset axes"]').click()
  await page.waitForFunction(before => JSON.stringify(document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot')._fullLayout.xaxis.range) === JSON.stringify(before), initial)
  // Parent-only resizing must work without a window resize event.
  await plot.locator('..').evaluate(el => { el.style.width = '75%' })
  await page.waitForFunction(() => {
    const el = document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot')
    return Math.abs(el._fullLayout.width - el.parentElement.clientWidth) < 2
  })
  await plot.locator('..').evaluate(el => { el.style.width = '100%' })
  await page.waitForFunction(() => {
    const el = document.querySelector('[data-testid="distribution-comparison"] .js-plotly-plot')
    return Math.abs(el._fullLayout.width - el.parentElement.clientWidth) < 2
  })
  // Address a real positive-frequency vertex, then inspect the rendered hover.
  const point = await plot.evaluate(el => {
    const trace = el.data.find(t => t.y.some(y => y > 0))
    const i = trace.y.findIndex(y => y > 0)
    const box = el.getBoundingClientRect()
    return { x: box.x + el._fullLayout.xaxis._offset + el._fullLayout.xaxis.l2p(trace.x[i]), y: box.y + el._fullLayout.yaxis._offset + el._fullLayout.yaxis.l2p(trace.y[i]) }
  })
  await page.mouse.move(point.x, point.y)
  await page.waitForFunction(() => document.querySelector('[data-testid="distribution-comparison"] .hoverlayer')?.textContent.includes('Eligible N'))
  const hover = await plot.locator('.hoverlayer').textContent()
  for (const word of ['区间', 'Count', 'Frequency', 'Eligible N']) assert.ok(hover.includes(word), hover)
  console.log('PASS distribution real hover, Zoom/Pan/Reset and parent-only responsive resize')
}
