import { expect, it } from 'vitest'
import { histogramFixture } from '../model/histogramAggregation.fixture'
import { histogramAggregation } from '../model/histogramAggregation'
import { distributionTraces } from './distributionFigure'

it('encodes shared edges, Slot colors and distinguishable percentage interval closures with Count/Frequency/N', () => {
  const projection = histogramAggregation(histogramFixture([[0, .001, .002], [.001], [], [.002]], 'basis_ratio'), 'basis_ratio', .1)
  if (projection.status !== 'ready') throw new Error(projection.message)
  const traces = distributionTraces(projection, 'basis_ratio') as any[]
  expect(traces.map(t => t.name)).toEqual(['M0', 'M1', 'Q1', 'Q2'])
  expect(traces.map(t => t.line.color)).toEqual(['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
  expect(traces[0].x).toEqual([0, .001, .001, .002])
  expect(traces[1].x).toEqual(traces[0].x)
  expect(traces[0].customdata).toEqual([
    ['[0.0%, 0.1%)', 1, 1/3, 3], ['[0.0%, 0.1%)', 1, 1/3, 3],
    ['[0.1%, 0.2%]', 2, 2/3, 3], ['[0.1%, 0.2%]', 2, 2/3, 3],
  ])
  expect(traces[0].hovertemplate).toContain('Count：%{customdata[1]:d}')
  expect(traces[0].hovertemplate).toContain('Frequency：%{customdata[2]:.1%}')
  expect(traces[0].hovertemplate).toContain('Eligible N：%{customdata[3]:d}')
  expect(traces[2].y).toEqual([null])
})

it('omits the curve for failed formal IntervalCount without mutating aggregation', () => {
  const report = histogramFixture([[0], [5]])
  report.distributions[0].methods[0].failure_category = 'CalculationFailure'
  const projection = histogramAggregation(report, 'basis_value', 5)
  if (projection.status !== 'ready') throw new Error(projection.message)
  const before = structuredClone(projection)
  const traces = distributionTraces(projection, 'basis_value') as any[]
  expect(traces[0].y).toEqual([null])
  expect(traces[1].customdata[0]).toEqual(['[0.00 点, 5.00 点]', 1, 1, 1])
  expect(projection).toEqual(before)
})

it('reuses the history Binding color even when producer Binding order differs', () => {
  const report = histogramFixture([[1], [2], [3], [4]])
  const view = report.views.history.basis_value
  if (view.version !== 2) throw new Error('expected V2')
  view.layers.reverse()
  const projection = histogramAggregation(report, 'basis_value', 10)
  if (projection.status !== 'ready') throw new Error(projection.message)
  const traces = distributionTraces(projection, 'basis_value') as any[]
  expect(traces.map(t => t.name)).toEqual(['M0', 'M1', 'Q1', 'Q2'])
  expect(traces.map(t => t.line.color)).toEqual(['#d62728', '#2ca02c', '#ff7f0e', '#1f77b4'])
})

it('preserves fine raw bins when one-decimal interval labels collide', () => {
  const projection = histogramAggregation(histogramFixture([[0, .0005, .001, .002]], 'basis_ratio'), 'basis_ratio', .05)
  if (projection.status !== 'ready') throw new Error(projection.message)
  const trace = distributionTraces(projection, 'basis_ratio')[0] as any
  expect(trace.x).toEqual([0, .0005, .0005, .001, .001, .0015, .0015, .002])
  expect(trace.customdata[2][0]).toBe(trace.customdata[4][0])
  expect(projection.slots[0].bins.map(bin => bin.count)).toEqual([1, 1, 1, 1])
  expect(trace.customdata.map((item: any[]) => item[2])).toEqual([.25, .25, .25, .25, .25, .25, .25, .25])
})
