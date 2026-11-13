import { expect, it } from 'vitest'
import fixture from '../api/result.fixture.json'
import { chartViewToPlotly } from '../../../shared/visualization/figure'
import { resultChartOptions, tradingDates } from './dateAxis'

const dates = tradingDates(fixture.daily)
const project = (view: 'returns' | 'drawdown', mode: 'trading' | 'calendar') =>
  chartViewToPlotly(fixture.views[view], resultChartOptions(dates, mode)) as any

it('derives the authoritative CFFEX session domain from daily rows without sorting or mutation', () => {
  const before = structuredClone(fixture)
  expect(dates).toEqual(['2025-02-17', '2025-03-20', '2025-03-21', '2025-03-24', '2025-03-25'])
  expect(new Set(dates).size).toBe(dates.length)
  expect(dates.every((date, i) => i === 0 || date > dates[i - 1])).toBe(true)
  expect(fixture).toEqual(before)
})

it.each(['returns', 'drawdown'] as const)('maps %s to ordinal positions or original dates with unchanged values and events', view => {
  const trading = project(view, 'trading')
  const calendar = project(view, 'calendar')
  const source = fixture.views[view]
  expect(trading.layout.xaxis.type).toBe('linear')
  expect(calendar.layout.xaxis.type).toBe('date')
  expect(trading.data.map((trace: any) => trace.x)).toEqual(source.layers.map(() => dates.map((_, i) => i)))
  expect(calendar.data.map((trace: any) => trace.x)).toEqual(source.layers.map(binding => binding.layer.data.map(mark => mark.x)))
  // Only the x presentation changes: every supplied y value is identical.
  expect(trading.data.map((trace: any) => trace.y)).toEqual(calendar.data.map((trace: any) => trace.y))
  expect(trading.data.map((trace: any) => trace.y)).toEqual(source.layers.map(binding => binding.layer.data.map(mark => mark.y)))
  expect(trading.layout.shapes.map((shape: any) => shape.x0)).toEqual(source.events.map(event => dates.indexOf(event.x)))
  expect(trading.layout.annotations.map((annotation: any) => annotation.x)).toEqual(source.events.map(event => dates.indexOf(event.x)))
  expect(calendar.layout.shapes.map((shape: any) => shape.x0)).toEqual(source.events.map(event => event.x))
  expect(calendar.layout.annotations.map((annotation: any) => annotation.x)).toEqual(source.events.map(event => event.x))
  expect(trading.layout.annotations.map((annotation: any) => annotation.text)).toEqual(source.events.map(event => event.label))
  expect(trading.layout.xaxis.ticktext.length).toBeLessThanOrEqual(8)
  expect(trading.layout.xaxis.ticktext).toEqual(trading.layout.xaxis.tickvals.map((i: number) => dates[i]))
  expect(trading.layout.xaxis.labelalias['0']).toBe('2025-02-17')
})

it('keeps entry, roll and exit annotations aligned in both modes', () => {
  const events = fixture.views.returns.events
  expect(events.map(event => [event.id, event.x])).toEqual([
    ['entry', '2025-02-17'], ['roll-0', '2025-03-21'], ['exit', '2025-03-25'],
  ])
  const trading = project('returns', 'trading')
  const calendar = project('returns', 'calendar')
  expect(trading.layout.annotations.map((annotation: any) => [annotation.text, annotation.x])).toEqual([
    ['Entry', 0], ['Roll', 2], ['Exit', 4],
  ])
  expect(calendar.layout.annotations.map((annotation: any) => annotation.x)).toEqual(events.map(event => event.x))
  expect(trading.data.map((trace: any) => trace.y)).toEqual(calendar.data.map((trace: any) => trace.y))
})

it('fails explicitly when a mark lies outside the supplied domain instead of shifting it', () => {
  expect(() => chartViewToPlotly(fixture.views.returns, resultChartOptions(dates.slice(1), 'trading'))).toThrow(/absent/)
  expect(() => chartViewToPlotly(fixture.views.returns, resultChartOptions([...dates, dates[0]], 'trading'))).toThrow(/increasing/)
})
