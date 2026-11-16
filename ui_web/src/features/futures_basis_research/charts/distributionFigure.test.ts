import { expect, it } from 'vitest'
import { histogramFixture } from '../model/histogramAggregation.fixture'
import { histogramAggregation } from '../model/histogramAggregation'
import { distributionTraces } from './distributionFigure'

it('encodes shared edges, Slot colors and precise percentage interval closures with Count/Frequency/N', () => {
  const projection = histogramAggregation(histogramFixture([[0, .0005, .001], [.0005], [], [.001]], 'basis_ratio'), 'basis_ratio', .05)
  if (projection.status !== 'ready') throw new Error(projection.message)
  const traces = distributionTraces(projection, 'basis_ratio', .05) as any[]
  expect(traces.map(t => t.name)).toEqual(['M0', 'M1', 'Q1', 'Q2'])
  expect(traces.map(t => t.line.color)).toEqual(['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
  expect(traces[0].x).toEqual([0, .0005, .0005, .001])
  expect(traces[1].x).toEqual(traces[0].x)
  expect(traces[0].customdata).toEqual([
    ['[0.00%, 0.05%)', 1, 1/3, 3], ['[0.00%, 0.05%)', 1, 1/3, 3],
    ['[0.05%, 0.10%]', 2, 2/3, 3], ['[0.05%, 0.10%]', 2, 2/3, 3],
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
  const traces = distributionTraces(projection, 'basis_value', 5) as any[]
  expect(traces[0].y).toEqual([null])
  expect(traces[1].customdata[0]).toEqual(['[0 点, 5 点]', 1, 1, 1])
  expect(projection).toEqual(before)
})
