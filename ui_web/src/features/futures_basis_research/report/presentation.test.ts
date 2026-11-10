import { expect, it } from 'vitest'
import { fixtureV2 } from '../../../shared/visualization/fixturesV2'
import { chartViewToPlotly } from '../../../shared/visualization/figure'
import { ordinalTicks } from '../../../shared/visualization/presentation'
import type { ChartViewContract } from '../../../shared/visualization'
import { historyOptions, histogramOptions } from './presentation'

it('maps the complete candidate calendar, including missing days, events, nulls and segments without mutation', () => {
  const view = structuredClone(fixtureV2)
  const before = structuredClone(view)
  const dates = ['2026-01-02', '2026-01-05', '2026-01-06', '2026-01-07', '2026-01-08']
  const trading = chartViewToPlotly(view, historyOptions(view, dates, true, false)) as any
  const calendar = chartViewToPlotly(view) as any
  expect(trading.data.map((t: any) => t.x)).toEqual([[0], [1, 2], [3], [0, 1]])
  expect(calendar.data[3].x.map(Date.parse).reduce((a: number, b: number) => b - a)).toBe(3 * 86400000)
  expect(trading.layout.xaxis.labelalias['1']).toBe('2026-01-05')
  expect(trading.layout.xaxis.hoverformat).toBe('d')
  expect(trading.layout.shapes[0].x0).toBe(1)
  expect(trading.layout.annotations[0].x).toBe(1)
  expect(trading.layout.xaxis.range[1]).toBeGreaterThan(4)
  expect(trading.data.map((t: any) => t.y)).toEqual(calendar.data.map((t: any) => t.y))
  expect(trading.data[1].text[0]).toContain('2026-01-05')
  expect(trading.data.every((t: any) => t.connectgaps === false)).toBe(true)
  expect(view).toEqual(before)
  expect(() => chartViewToPlotly(view, { ordinalDates: dates.slice(1) })).toThrow(/absent/)
  const eventOnly = structuredClone(view); eventOnly.events[0].x = '2026-01-09'
  expect(() => chartViewToPlotly(eventOnly, { ordinalDates: dates })).toThrow(/absent/)
  expect(() => chartViewToPlotly(view, { ordinalDates: [...dates, dates[0]] })).toThrow(/increasing/)
})
it('handles empty domains and bounds ordinal date labels to eight visible positions', () => {
  expect(ordinalTicks([]).tickvals).toEqual([])
  const dates = Array.from({ length: 1000 }, (_, i) => String(i))
  expect(ordinalTicks(dates).tickvals.length).toBeLessThanOrEqual(8)
  const zoomed = ordinalTicks(dates, [500.2, 510.8])
  expect(zoomed.tickvals[0]).toBe(501)
  expect(zoomed.ticktext).toEqual(zoomed.tickvals.map(String))
  const empty = { ...fixtureV2, axes: [], layers: [], events: [] }
  expect((chartViewToPlotly(empty, { ordinalDates: [] }) as any).data).toEqual([])
})
it('uses unit-aware percentage hover and feature result details, with a basis-only grid', () => {
  const view = structuredClone(fixtureV2)
  view.axes[1].coordinate.unit = 'decimal_ratio'
  view.layers.forEach(b => { b.layer.y.unit = 'decimal_ratio' })
  view.layers[0].layer.data[0].y = -0.000001
  view.layers[0].layer.data[0].details = [{ label: '结果', value: '-0.000001' }, { label: '期货 Close', value: '123' }]
  const f = chartViewToPlotly(view, historyOptions(view, [], false, false)) as any
  expect(f.layout.yaxis.tickformat).toBe('.1%')
  expect(f.layout.yaxis.dtick).toBeUndefined()
  expect(f.data[0].text[0]).toContain('结果: 0.0%')
  expect(f.data[0].text[0]).toContain('期货 Close: 123')
  expect(f.data[0].y[0]).toBe(-0.000001)
  view.axes[1].coordinate.unit = 'index_points'
  view.layers.forEach(b => { b.layer.y.unit = 'index_points' })
  const grid = chartViewToPlotly(view, historyOptions(view, [], false, true)) as any
  expect(grid.layout.yaxis).toMatchObject({ tick0: 0, dtick: 100, griddash: 'dash' })
  expect(grid.layout.yaxis.range).toEqual(f.layout.yaxis.range)
  expect(grid.layout.shapes).toHaveLength(view.events.length)
})
it('keeps colliding formatted bins distinct and preserves counts, order and inclusion', () => {
  const result = { method: 'interval_count', unit: 'decimal_ratio', sample_count: 7, edges: [0.00001, 0.00002, 0.00003], bins: [
    { left: 0.00001, right: 0.00002, left_inclusive: true, right_inclusive: false, count: 2, frequency: 2 / 7 },
    { left: 0.00002, right: 0.00003, left_inclusive: true, right_inclusive: false, count: 3, frequency: 3 / 7 },
  ] }
  const categories = ['< 1e-05', '[1e-05, 2e-05)', '[2e-05, 3e-05)', '> 3e-05']
  const view: ChartViewContract = { version: 1, axes: [{ id: 'bins', orientation: 'x', coordinate: { kind: 'category', unit: 'category' } }, { id: 'n', orientation: 'y', coordinate: { kind: 'number', unit: 'count' } }], layers: [{ id: 'b', x_axis: 'bins', y_axis: 'n', layer: { type: 'bar', version: 1, x: { kind: 'category', unit: 'category' }, y: { kind: 'number', unit: 'count' }, data: categories.map((x, i) => ({ x, y: [1, 2, 3, 1][i] })) } }], layout: { title: '' }, presentation: { show_legend: false } }
  const before = structuredClone({ view, result })
  const figure = chartViewToPlotly(view, histogramOptions(view, result)) as any
  expect(figure.layout.xaxis.tickvals).toEqual(categories)
  expect(figure.layout.xaxis.ticktext).toEqual(['&lt; 0.0%', '[0.0%, 0.0%)', '[0.0%, 0.0%)', '&gt; 0.0%'])
  expect(figure.data[0].x).toEqual(categories)
  expect(figure.data[0].y).toEqual([1, 2, 3, 1])
  expect(figure.layout.yaxis.tickformat).toBeUndefined()
  expect({ view, result }).toEqual(before)
})
