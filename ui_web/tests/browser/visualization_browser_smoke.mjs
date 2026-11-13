// Standalone artificial Views -> real React/Plotly -> Chromium. No backend.
import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const root = fileURLToPath(new URL('../../', import.meta.url))
const output = resolve(process.env.WP1_BROWSER_EVIDENCE_DIR || resolve(root, '.build/tests/visualization-browser'))
await mkdir(output, { recursive: true })
const evidence = { status: 'RUNNING', checks: [], errors: [] }
const server = await createServer({ root, server: { host: '127.0.0.1', port: 0, open: false, proxy: {} } })
let browser; let page
function passed(message) { evidence.checks.push(message); console.log(`PASS: ${message}`) }
try {
  await server.listen()
  const address = server.httpServer.address()
  browser = await chromium.launch({ headless: true, ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH } : {}) })
  evidence.browser = browser.version()
  page = await browser.newPage({ viewport: { width: 1400, height: 1100 }, timezoneId: 'Asia/Shanghai' })
  page.setDefaultTimeout(15000)
  page.on('pageerror', error => evidence.errors.push(String(error)))
  page.on('request', request => {
    const url = new URL(request.url())
    if (/^\/(research|auth|mo-option)/.test(url.pathname) || (request.resourceType() === 'fetch' || request.resourceType() === 'xhr')) evidence.errors.push(`Unexpected data request: ${request.url()}`)
  })
  await page.goto(`http://127.0.0.1:${address.port}/tests/visualization/visualization-harness.html`)
  const plot = page.locator('.js-plotly-plot')
  const traces = () => plot.locator('.scatterlayer .trace.scatter')
  async function settled() { await page.waitForFunction(() => !!document.querySelector('.js-plotly-plot')?._fullLayout?._plots?.xy); await plot.locator('.nsewdrag').waitFor() }
  async function choose(name) { await page.getByRole('button', { name, exact: true }).click(); await settled() }
  async function ranges() { return plot.evaluate(el => Object.fromEntries(Object.keys(el._fullLayout).filter(k => /^[xy]axis\d*$/.test(k)).map(k => [k, Array.from(el._fullLayout[k].range)]))) }
  async function drag(x0, y0, x1, y1, modifier) {
    const box = await plot.locator('.nsewdrag').boundingBox()
    if (modifier) await page.keyboard.down(modifier)
    await page.mouse.move(box.x + box.width * x0, box.y + box.height * y0)
    await page.mouse.down(); await page.mouse.move(box.x + box.width * x1, box.y + box.height * y1, { steps: 12 }); await page.mouse.up()
    if (modifier) await page.keyboard.up(modifier)
  }
  async function waitChanged(before) { await page.waitForFunction(old => JSON.stringify(Array.from(document.querySelector('.js-plotly-plot')._fullLayout.xaxis.range)) !== JSON.stringify(old), before.xaxis) }
  async function reset(initial) {
    await plot.locator('[data-title="Reset axes"]').click()
    await page.waitForFunction(expected => {
      const layout = document.querySelector('.js-plotly-plot')._fullLayout
      return Object.entries(expected).every(([key, range]) => JSON.stringify(Array.from(layout[key].range)) === JSON.stringify(range))
    }, initial)
  }
  await settled()
  assert.equal(await traces().count(), 4)
  assert.equal(await plot.locator('.scatterlayer .point').count(), 5)
  const paths = await traces().evaluateAll(nodes => nodes.map(n => Array.from(n.querySelectorAll('.js-line')).map(p => p.getAttribute('d'))))
  assert.ok(paths.slice(0, 3).flat().every(d => !/[LHVCSQTA]/i.test(d)), JSON.stringify(paths))
  assert.ok(paths[3].some(d => /L/.test(d)), JSON.stringify(paths))
  assert.equal(await plot.locator('.legend .traces').count(), 2)
  passed('Fixed fixture renders 3 finite A points without edges, B edge, 5 total points and 2 logical legends')
  await traces().first().locator('.point').hover({ force: true })
  await page.waitForFunction(() => document.querySelector('.hoverlayer')?.textContent.includes('<b>literal text</b>'))
  const hover = await plot.locator('.hoverlayer').textContent()
  for (const text of ['Series A', '2026-01-02', '1 count', 'Note: <b>literal text</b>']) assert.ok(hover.includes(text), hover)
  assert.equal(await plot.locator('.hoverlayer b, .hoverlayer img, .hoverlayer script').count(), 0)
  await page.screenshot({ path: resolve(output, 'fixed-point-hover.png'), fullPage: true })
  passed('Real point hover shows binding/date/value/unit and literal custom detail')
  await page.getByText('Series A — 2026-01-06 — No value').click()
  await page.getByText('Reason: Not supplied').waitFor()
  passed('Null date and reason are inspectable without a y marker')
  const initial = await ranges()
  await drag(.15, .5, .75, .5); await waitChanged(initial)
  assert.deepEqual((await ranges()).yaxis, initial.yaxis)
  await reset(initial)
  await drag(.15, .2, .75, .8); await waitChanged(initial)
  await reset(initial)
  const box = await plot.locator('.nsewdrag').boundingBox()
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2)
  await page.mouse.wheel(0, -180); await waitChanged(initial)
  await plot.locator('[data-title="Pan"]').click()
  const zoomed = await ranges(); await drag(.5, .5, .7, .5); await waitChanged(zoomed)
  await reset(initial)
  await plot.locator('.legend .traces').first().click()
  await page.waitForFunction(() => document.querySelector('.js-plotly-plot')._fullData.slice(0, 3).every(t => t.visible === 'legendonly'))
  await reset(initial)
  assert.ok(await plot.evaluate(el => el._fullData.slice(0, 3).every(t => t.visible === 'legendonly')))
  passed('Box/wheel zoom, selectable drag pan, full-axis reset and grouped legend work; reset preserves legend selection')
  await choose('Events V2')
  assert.equal(await plot.locator('.shapelayer path').count(), 3)
  assert.equal(await plot.locator('.annotation').count(), 3)
  const positions = await plot.evaluate(el => {
    const axis = el._fullLayout.xaxis
    return Array.from(el.querySelectorAll('.shapelayer path')).map((path, i) => {
      const x = Number(path.getAttribute('d').match(/^M([\d.e+-]+),/)[1])
      return { actual: x, expected: axis._offset + axis.d2p(el.layout.shapes[i].x0) }
    })
  })
  assert.ok(positions.every(p => Math.abs(p.actual - p.expected) < 1), JSON.stringify(positions))
  for (const label of ['e1 — 2026-01-05 — Boundary', 'e2 — 2026-01-05 — Same date', 'e3 — 2026-01-12 — Event only date']) await page.getByText(label).waitFor()
  await page.getByText('e2 — 2026-01-05 — Same date').click()
  await page.getByText('Note: <b>literal event</b>').waitFor()
  assert.equal(await page.getByRole('region', { name: 'Date events' }).locator('b').count(), 0)
  const eventText = await page.getByRole('region', { name: 'Date events' }).textContent()
  assert.ok(eventText.indexOf('literal event') < eventText.indexOf('Second detail'))
  await page.screenshot({ path: resolve(output, 'events-and-details.png'), fullPage: true })
  passed('Date event lines match axis pixel positions; same-day and event-only dates retain independent ordered literal details')
  await choose('Multi-axis V2')
  const multiInitial = await ranges()
  assert.ok(multiInitial.yaxis2)
  assert.equal(await plot.locator('.y2title').textContent(), 'distance')
  await drag(.2, .2, .8, .8); await waitChanged(multiInitial)
  assert.notDeepEqual((await ranges()).yaxis2, multiInitial.yaxis2)
  await reset(multiInitial)
  passed('Multi-y-axis layout renders separate units and zoom/reset updates both numeric axes')
  await choose('Null gap V2')
  assert.equal(await traces().first().locator('.js-line').count(), 2)
  assert.equal(await traces().nth(1).locator('.js-line').count(), 1)
  passed('Null splits a same-segment line and equal segment IDs never connect different bindings')
  await choose('Overlapping points')
  await traces().first().locator('.point').hover({ force: true })
  await page.waitForFunction(() => {
    const text = document.querySelector('.hoverlayer')?.textContent ?? ''
    return text.includes('Series A') && text.includes('Series B')
  })
  passed('Coincident points in separate bindings remain inspectable with legend hidden')
  for (const name of ['Zoom only', 'Pan only', 'Disabled']) {
    await choose(name); const before = await ranges()
    assert.equal(await plot.locator('[data-title="Reset axes"]').count(), 0)
    if (name !== 'Zoom only') {
      assert.equal(await plot.locator('[data-title="Zoom"]').count(), 0)
      const area = await plot.locator('.nsewdrag').boundingBox()
      await page.mouse.move(area.x + area.width / 2, area.y + area.height / 2); await page.mouse.wheel(0, -180)
    }
    if (name !== 'Pan only') assert.equal(await plot.locator('[data-title="Pan"]').count(), 0)
    await drag(.3, .3, .7, .7, 'Shift')
    await page.keyboard.down('Control'); await drag(.3, .3, .7, .7, 'Shift'); await page.keyboard.up('Control')
    if (name === 'Zoom only') await drag(.3, .3, .7, .7, 'Control')
    if (name === 'Pan only') {
      const end = await plot.locator('.edrag').boundingBox()
      await page.mouse.move(end.x + end.width / 2, end.y + end.height / 2)
      await page.mouse.down(); await page.mouse.move(end.x + end.width / 2 - 50, end.y + end.height / 2, { steps: 10 }); await page.mouse.up()
    }
    const area = await plot.locator('.nsewdrag').boundingBox()
    await page.mouse.dblclick(area.x + area.width / 2, area.y + area.height / 2)
    assert.deepEqual(await ranges(), before, `${name}: disabled shortcut/gesture changed ranges`)
    if (name === 'Disabled') { await drag(.3, .3, .7, .7); assert.deepEqual(await ranges(), before); assert.equal(await plot.locator('.legend .traces').count(), 0) }
  }
  passed('Disabled zoom/pan/reset controls, wheel, modifier shortcuts and double-click cannot bypass Presentation')
  for (const name of ['All null', 'Empty series', 'Empty view']) {
    await choose(name); await page.getByText('No numeric data').waitFor()
    assert.equal(await plot.locator('.scatterlayer .point').count(), 0)
    if (name !== 'Empty view') assert.equal(await plot.locator('.legend .traces').count(), 2)
  }
  passed('Empty/all-null content has explicit no-numeric-data presentation and no invented points')
  await choose('Long ordinal')
  const fullOrdinal = await ranges()
  await plot.locator('.scatterlayer .point').nth(12).hover({ force: true })
  await page.waitForFunction(() => /\d{4}-\d{2}-\d{2}/.test(document.querySelector('.hoverlayer .axistext')?.textContent ?? ''))
  assert.ok(await plot.evaluate(el => el._fullLayout.xaxis.ticktext.length <= 8))
  await drag(.25, .5, .4, .5); await waitChanged(fullOrdinal)
  await page.waitForFunction(() => {
    const axis = document.querySelector('.js-plotly-plot')._fullLayout.xaxis
    return axis.tickvals.length > 0 && axis.tickvals.length <= 8 && axis.tickvals.every(v => v >= axis.range[0] && v <= axis.range[1])
  })
  await plot.locator('[data-title="Pan"]').click()
  const ordinalZoom = await ranges()
  await drag(.5, .5, .65, .5); await waitChanged(ordinalZoom)
  await reset(fullOrdinal)
  await page.waitForFunction(() => document.querySelector('.js-plotly-plot')._fullLayout.xaxis.tickvals[0] === 0)
  await page.screenshot({ path: resolve(output, 'long-ordinal.png'), fullPage: true })
  await choose('Index grid')
  const gridLabels = await plot.locator('.yaxislayer-above .ytick text').allTextContents()
  assert.ok(gridLabels.includes('−100') && gridLabels.includes('100'), JSON.stringify(gridLabels))
  assert.ok(await plot.locator('.ygrid').evaluateAll(nodes => nodes.some(n => getComputedStyle(n).strokeDasharray !== 'none')))
  await page.screenshot({ path: resolve(output, 'index-grid.png'), fullPage: true })
  await choose('Near zero ratio')
  const labels = await plot.locator('.yaxislayer-above .ytick text').allTextContents()
  assert.ok(labels.length > 0)
  assert.ok(labels.every(label => label.endsWith('%') && !/[-−]0\.0%/.test(label)), JSON.stringify(labels))
  passed('Long ordinal labels adapt after Zoom/Pan/Reset; near-zero percentage ticks never show negative zero')
  await choose('V1 mixed')
  assert.equal(await traces().count(), 2); assert.equal(await traces().nth(1).locator('.point').count(), 3)
  assert.ok(await traces().first().locator('.js-line').getAttribute('d'))
  await choose('V1 bar'); assert.equal(await plot.locator('.barlayer .point').count(), 2)
  await page.screenshot({ path: resolve(output, 'v1-regression.png'), fullPage: true })
  passed('V1 line/point and categorical bar still render through the original path')
  assert.deepEqual(evidence.errors, [])
  passed('No business/data HTTP requests or browser runtime errors')
  evidence.status = 'PASS'
} catch (error) {
  evidence.status = 'PARTIAL'; evidence.failure = String(error)
  if (page) {
    await page.screenshot({ path: resolve(output, 'failure.png'), fullPage: true }).catch(() => {})
    evidence.body = await page.locator('body').innerText().catch(() => 'unavailable')
  }
  throw error
} finally {
  await writeFile(resolve(output, 'acceptance.json'), JSON.stringify(evidence, null, 2) + '\n')
  console.log(`Browser evidence: ${output}`)
  await browser?.close(); await server.close()
}
