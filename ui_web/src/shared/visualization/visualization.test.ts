import type { XYMark } from './contract'
import { describe, expect, it } from 'vitest'
import { validateChartView, validateLayer } from './contract'
import { chartViewToPlotly, UnsupportedLayerError } from './figure'
import { fixtures } from './fixtures'

const copy = <T>(v: T): T => structuredClone(v)
const layer = () => copy(fixtures.line.layers[0].layer)
const view = () => copy(fixtures.mixed)

describe('Layer V1', () => {
  it('accepts line, bar, point and empty data without mutation', () => {
    for (const fixture of [fixtures.line, fixtures.bar, fixtures.point]) {
      const input = copy(fixture.layers[0].layer); const before = copy(input)
      expect(() => validateLayer(input)).not.toThrow(); expect(input).toEqual(before)
      input.data = []; expect(() => validateLayer(input)).not.toThrow()
    }
  })
  it.each([
    ['version', (l: any) => { l.version = 2 }], ['unknown type', (l: any) => { l.type = 'other' }],
    ['extra field', (l: any) => { l.extra = true }], ['extra mark field', (l: any) => { l.data[0].extra = true }],
    ['nonfinite', (l: any) => { l.data[0].y = Infinity }], ['wrong type', (l: any) => { l.data[0].y = '3' }],
    ['category unit', (l: any) => { l.x.unit = 'other' }], ['empty unit', (l: any) => { l.y.unit = '' }],
    ['invalid date', (l: any) => { l.x = { kind: 'date', unit: 'date' }; l.data[0].x = '2025-02-29' }],
    ['date unit', (l: any) => { l.x = { kind: 'date', unit: 'day' } }],
  ])('rejects %s', (_, mutate) => { const l = layer(); mutate(l); expect(() => validateLayer(l)).toThrow() })
  it('checks leap dates and canonical representation', () => {
    const l = layer(); l.x = { kind: 'date', unit: 'date' }; l.data = [{ x: '2024-02-29', y: 1 }]
    expect(() => validateLayer(l)).not.toThrow()
    l.data[0].x = '2024-2-29'; expect(() => validateLayer(l)).toThrow()
  })
  it('rejects duplicate bars and retains exact category identities', () => {
    const l = copy(fixtures.bar.layers[0].layer); const marks = l.data as XYMark[]; marks[1].x = marks[0].x
    expect(() => validateLayer(l)).toThrow(/duplicate/)
    marks[1].x = ' B'; expect(() => validateLayer(l)).not.toThrow()
  })
  it.each([
    { type: 'segment', data: [{ x1: 'a', y1: 0, x2: 'b', y2: 1 }] },
    { type: 'candlestick', data: [{ x: 'a', open: 1, high: 3, low: 0, close: 2 }] },
    { type: 'area', data: [{ x: 'a', y0: 0, y1: 1 }] },
  ])('validates but does not render $type', (item) => {
    const l = { ...layer(), ...item }; expect(() => validateLayer(l)).not.toThrow()
    const v = view(); v.layers = [{ ...v.layers[0], layer: l as never }]
    expect(() => chartViewToPlotly(v)).toThrow(UnsupportedLayerError)
  })
})

describe('ChartView and projection', () => {
  it('accepts fixtures and empty view', () => {
    for (const v of [fixtures.line, fixtures.bar, fixtures.point, fixtures.mixed, { ...view(), axes: [], layers: [] }]) expect(() => validateChartView(v)).not.toThrow()
    expect(chartViewToPlotly({ ...view(), axes: [], layers: [] }).data).toEqual([])
    expect(() => chartViewToPlotly(fixtures.invalid)).toThrow(/unknown axis/)
  })
  it.each([
    ['version', (v: any) => { v.version = 2 }], ['extra field', (v: any) => { v.layout.extra = 1 }],
    ['axis reference', (v: any) => { v.layers[0].x_axis = 'missing' }], ['orientation', (v: any) => { v.layers[0].x_axis = 'vertical' }],
    ['kind', (v: any) => { v.axes[0].coordinate = { kind: 'number', unit: 'category' } }], ['unit', (v: any) => { v.axes[1].coordinate = { kind: 'number', unit: 'other' } }],
    ['duplicate axis', (v: any) => { v.axes.push(copy(v.axes[0])) }], ['duplicate binding', (v: any) => { v.layers[1].id = v.layers[0].id }],
  ])('rejects %s', (_, mutate) => { const v = view(); mutate(v); expect(() => chartViewToPlotly(v)).toThrow() })
  it('preserves mark and binding order, zero and duplicate points', () => {
    const line = chartViewToPlotly(fixtures.line).data[0] as any
    expect(line.x).toEqual(['B', 'A']); expect(line.y).toEqual([3, 1]); expect(line.mode).toBe('lines'); expect(line.connectgaps).toBe(false)
    const bar = chartViewToPlotly(fixtures.bar).data[0] as any
    expect(bar.x).toEqual(['B', 'A']); expect(bar.y).toEqual([0, 2]); expect(bar.type).toBe('bar')
    const mixed = chartViewToPlotly(fixtures.mixed); const point = mixed.data[1] as any
    expect(mixed.data.map((t: any) => t.name)).toEqual(['series-1', 'series-2'])
    expect(point.mode).toBe('markers'); expect(point.x).toEqual(['A', 'A', 'C']); expect(point.y).toEqual([2, 2, 4])
    expect(mixed.layout.xaxis?.categoryorder).toBe('array'); expect(mixed.layout.xaxis?.categoryarray).toEqual(['B', 'A', 'C'])
    expect(point.xaxis).toBe('x'); expect(point.yaxis).toBe('y')
  })
  it('binds distinct axes explicitly', () => {
    const v = view(); v.axes.push({ ...copy(v.axes[1]), id: 'second' }); v.layers[1].y_axis = 'second'
    const f = chartViewToPlotly(v); expect((f.data[1] as any).yaxis).toBe('y2'); expect(f.layout.yaxis2?.overlaying).toBe('y')
  })
})

it('exposes reproducible fixture projections for inspection', () => {
  if (import.meta.env.VITE_VISUALIZATION_FIXTURES !== '1') return
  for (const name of ['line', 'bar', 'point', 'mixed'] as const) {
    console.log(`${name}: ${JSON.stringify(chartViewToPlotly(fixtures[name]))}`)
  }
  try { chartViewToPlotly(fixtures.invalid) } catch (error) { console.log(`invalid: ${String(error)}`) }
})

it('rejects sparse input instead of silently dropping marks', () => {
  const l = layer(); l.data = new Array(1)
  expect(() => validateLayer(l)).toThrow(/data\[0\]/)
})
it('renders numerical and date axes without changing their order', () => {
  const v = view()
  v.axes[0].coordinate = { kind: 'date', unit: 'date' }
  v.layers = [v.layers[0]]
  v.layers[0].layer.x = { kind: 'date', unit: 'date' }
  v.layers[0].layer.data = [{ x: '2024-02-29', y: 0 }, { x: '2023-01-01', y: 2 }]
  const figure = chartViewToPlotly(v)
  expect((figure.data[0] as any).x).toEqual(['2024-02-29', '2023-01-01'])
  expect(figure.layout.xaxis?.type).toBe('date')
  v.axes[0].coordinate = { kind: 'number', unit: 'distance' }
  v.layers[0].layer.x = { kind: 'number', unit: 'distance' }
  v.layers[0].layer.data = [{ x: 2, y: 0 }, { x: 1, y: 2 }]
  expect((chartViewToPlotly(v).data[0] as any).x).toEqual([2, 1])
})
it('validates a noncategorical bar but reports its unsupported renderer', () => {
  const v = view(); v.layers = [v.layers[0]]
  v.axes[0].coordinate = { kind: 'number', unit: 'distance' }
  v.layers[0].layer = { type: 'bar', version: 1, x: { kind: 'number', unit: 'distance' }, y: { kind: 'number', unit: 'count' }, data: [{ x: 1, y: 2 }] }
  expect(() => validateChartView(v)).not.toThrow()
  expect(() => chartViewToPlotly(v)).toThrow(UnsupportedLayerError)
})
