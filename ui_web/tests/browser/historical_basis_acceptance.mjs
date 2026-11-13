// Shared online/file:// presentation acceptance; producer data is read-only.
import assert from 'node:assert/strict'
import { resolve } from 'node:path'

export async function historicalBasisAcceptance(page, expected, output) {
  const plots = page.locator('#section-1 .js-plotly-plot')
  const control = page.locator('#section-1')
  const metrics = ['basis_value', 'basis_ratio', 'annualized_basis_ratio']
  async function projection(trading) {
    for (let i = 0; i < 3; i++) {
      const plot = plots.nth(i)
      await page.waitForFunction(({ index, type }) => document.querySelectorAll('#section-1 .js-plotly-plot')[index]?._fullLayout.xaxis.type === type, { index: i, type: trading ? 'linear' : 'date' })
      const view = expected.views.history[metrics[i]]
      const actual = await plot.evaluate(el => ({
        data: el.data.map(t => ({ x: t.x, y: t.y, text: t.text, connectgaps: t.connectgaps })),
        shapes: el.layout.shapes, annotations: el.layout.annotations,
        axis: { type: el._fullLayout.xaxis.type, range: el._fullLayout.xaxis.range, ticktext: el._fullLayout.xaxis.ticktext },
        y: { dtick: el._fullLayout.yaxis.dtick, tick0: el._fullLayout.yaxis.tick0, griddash: el._fullLayout.yaxis.griddash, gridcolor: el._fullLayout.yaxis.gridcolor },
      }))
      const marks = view.layers.flatMap(b => b.layer.data)
      const traces = actual.data.filter(t => !(t.x.length === 1 && t.x[0] === null))
      assert.deepEqual(traces.flatMap(t => t.y), marks.map(m => m.y))
      assert.deepEqual(traces.flatMap(t => t.x), marks.map(m => trading ? expected.candidate_dates.indexOf(m.x) : m.x))
      assert.ok(actual.data.every(t => t.connectgaps === false))
      for (const [j, event] of view.events.entries()) {
        const x = trading ? expected.candidate_dates.indexOf(event.x) : event.x
        assert.equal(actual.shapes[j].x0, x)
        assert.equal(actual.annotations[j].x, x)
      }
      if (trading) assert.ok(actual.axis.ticktext.length <= 8)
      if (i === 0) {
        assert.equal(actual.y.dtick, 100)
        assert.equal(actual.y.tick0, 0)
        assert.equal(actual.y.griddash, 'dash')
        assert.equal(actual.y.gridcolor, 'rgba(180,180,180,0.25)')
        assert.equal(actual.shapes.length, view.events.length)
      }
      if (i > 0 && marks.some(m => m.y !== null)) {
        assert.ok(actual.data.flatMap(t => t.text).some(t => /\d\.\d%/.test(t)))
        assert.ok(!actual.data.flatMap(t => t.text).some(t => t.includes('-0.0%')))
      }
    }
  }
  async function interact() {
    const plot = plots.first()
    async function settle() {
      await plot.evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }))
      await plot.locator('.nsewdrag').evaluate(el => new Promise(resolve => {
        let previous = ''; let stable = 0
        function frame() {
          const r = el.getBoundingClientRect(); const current = [r.x, r.y, window.scrollY].join(',')
          stable = current === previous ? stable + 1 : 0; previous = current
          if (stable >= 12) resolve(); else requestAnimationFrame(frame)
        }
        frame()
      }))
    }
    await settle()
    const range = () => plot.evaluate(el => Array.from(el._fullLayout.xaxis.range))
    const initial = await range()
    async function drag(from, to) {
      await settle()
      const box = await plot.locator('.nsewdrag').boundingBox()
      await page.mouse.move(box.x + box.width * from, box.y + box.height * .5)
      await page.mouse.down(); await page.mouse.move(box.x + box.width * to, box.y + box.height * .5, { steps: 12 }); await page.mouse.up()
    }
    async function changed(before) {
      await page.waitForFunction(old => JSON.stringify(document.querySelector('#section-1 .js-plotly-plot')._fullLayout.xaxis.range) !== JSON.stringify(old), before)
    }
    await plot.locator('[data-title="Zoom"]').click()
    await page.waitForFunction(() => document.querySelector('#section-1 .js-plotly-plot')._fullLayout.dragmode === 'zoom')
    await drag(.15, .75); await changed(initial)
    await plot.locator('[data-title="Pan"]').click()
    await page.waitForFunction(() => document.querySelector('#section-1 .js-plotly-plot')._fullLayout.dragmode === 'pan')
    const zoomed = await range()
    await drag(.5, .7); await changed(zoomed)
    await plot.locator('[data-title="Reset axes"]').click()
    await page.waitForFunction(old => JSON.stringify(document.querySelector('#section-1 .js-plotly-plot')._fullLayout.xaxis.range) === JSON.stringify(old), initial)
    await plot.locator('[data-title="Zoom"]').click()
  }
  await projection(true)
  if (!metrics.some(metric => expected.views.history[metric].layers.some(b => b.layer.data.some(m => m.y !== null)))) {
    await control.getByText('Calendar Days', { exact: true }).click()
    await projection(false)
    await control.getByText('Trading Days', { exact: true }).click()
    await projection(true)
    console.log('PASS: All-null history retains missing data and date mapping in both modes')
    return
  }
  await interact()
  const first = plots.first()
  await first.scrollIntoViewIfNeeded()
  await first.locator('.legend .traces').first().click()
  await page.waitForFunction(() => document.querySelector('#section-1 .js-plotly-plot')._fullData.some(t => t.visible === 'legendonly'))
  await control.getByText('Calendar Days', { exact: true }).click()
  await projection(false)
  await interact()
  assert.ok(await first.evaluate(el => el._fullData.some(t => t.visible === 'legendonly')))
  await page.screenshot({ path: resolve(output, 'historical-calendar.png') })
  await control.getByText('Trading Days', { exact: true }).click()
  await projection(true)
  assert.ok(await first.evaluate(el => el._fullData.some(t => t.visible === 'legendonly')))
  await first.locator('.legend .traces').first().click()
  await page.waitForFunction(() => document.querySelector('#section-1 .js-plotly-plot')._fullData.every(t => t.visible !== 'legendonly'))
  await first.scrollIntoViewIfNeeded()
  await page.screenshot({ path: resolve(output, 'historical-trading.png') })
  // Real hover for percentage plots: coordinate date and the supplied result detail.
  const ratio = plots.nth(1)
  await ratio.scrollIntoViewIfNeeded()
  if (expected.views.history.basis_ratio.layers.some(b => b.layer.data.some(m => m.y !== null))) {
  const point = ratio.locator('.scatterlayer .point').first()
  await point.hover({ force: true })
  await page.waitForFunction(() => /\d\.\d%/.test(document.querySelectorAll('#section-1 .hoverlayer')[1]?.textContent ?? ''))
  const hover = await ratio.locator('.hoverlayer').textContent()
  assert.match(hover, /\d{4}-\d{2}-\d{2}/)
  assert.match(hover, /结果:.*%/)
  await page.screenshot({ path: resolve(output, 'historical-percentage-hover.png') })
  }
  // Both coordinate modes still expose the same interaction controls.
  for (const plot of [first, ratio]) {
    for (const title of ['Zoom', 'Pan', 'Reset axes']) assert.equal(await plot.locator(`[data-title="${title}"]`).count(), 1)
  }
  console.log('PASS: Historical default/mode mapping, candidate dates, transitions, legend persistence, 100-point grid and percentage hover')
}
