import { describe, expect, it } from 'vitest'
import bundle from '../../../../demo/bundles/basis.json'
import { BIN_PRESETS, histogramAggregation, type BasisMetric, type HistogramProjection } from './histogramAggregation'
import { histogramFixture } from './histogramAggregation.fixture'
import type { ReportData } from '../report/types'

function ready(result: HistogramProjection) {
  expect(result.status).toBe('ready')
  if (result.status !== 'ready') throw new Error(JSON.stringify(result))
  return result
}
function conserved(result: ReturnType<typeof ready>) {
  for (const slot of result.slots) {
    expect(slot.bins.reduce((sum, b) => sum + b.count, 0)).toBe(slot.n)
    if (slot.n) {
      expect(slot.bins.reduce((sum, b) => sum + b.frequency, 0)).toBeCloseTo(1, 14)
      slot.bins.forEach(b => expect(b.frequency).toBe(b.count / slot.n))
    }
  }
}
describe('presentation-only histogram', () => {
  it('partitions negatives, exact edges, signed zero, duplicates and the closed final endpoint', () => {
    const r = ready(histogramAggregation(histogramFixture([[-10, -5, 0, -0, 5, 10, 10], [0], [1, 1], []]), 'basis_value', 5))
    expect(r.edges).toEqual([-10, -5, 0, 5, 10])
    expect(r.slots[0].bins.map(b => b.count)).toEqual([1, 1, 2, 3])
    expect(r.slots[0].bins.map(b => b.rightInclusive)).toEqual([false, false, false, true])
    conserved(r)
  })
  it.each([[3, 3, 3], [0], [-10, -10], [1, 2, 3]])('handles one-bin/singleton/repeated samples %j', (...values) => {
    const r = ready(histogramAggregation(histogramFixture([values]), 'basis_value', 10))
    expect(r.slots[0].bins).toHaveLength(1)
    expect(r.slots[0].bins[0].count).toBe(values.length)
    conserved(r)
  })
  it('shows all-empty without fabricated data', () => {
    expect(histogramAggregation(histogramFixture([[], [], [], []]), 'basis_value', 10).status).toBe('empty')
  })
  it('keeps different Slot populations including expiry-day nulls and empty Slots', () => {
    const r = ready(histogramAggregation(histogramFixture([[null, -.05], [0, .1], [.2], []], 'annualized_basis_ratio'), 'annualized_basis_ratio', 5))
    expect(r.slots.map(s => s.n)).toEqual([1, 2, 1, 0]); conserved(r)
    expect(r.slots[3].bins).toEqual([])
  })
  it.each([['basis_ratio', .1, .001], ['basis_ratio', .2, .002], ['annualized_basis_ratio', 5, .05]] as const)('converts %s width %s to raw %s', (metric, width, raw) => {
    const r = ready(histogramAggregation(histogramFixture([[-raw, 0, raw]], metric), metric, width))
    expect(r.edges).toEqual([-raw, 0, raw]); expect(r.slots[0].bins.map(b => b.count)).toEqual([1, 2]); conserved(r)
  })
  it('does not snap near-boundary floating values', () => {
    const r = ready(histogramAggregation(histogramFixture([[.001 - Number.EPSILON * .001, .001, .001 + Number.EPSILON * .001, .002]], 'basis_ratio'), 'basis_ratio', .1))
    expect(r.slots[0].bins.map(b => b.count)).toEqual([1, 3]); conserved(r)
  })
  it.each(Object.keys(BIN_PRESETS) as BasisMetric[])('conserves real Bundle %s for every width deterministically without mutation', metric => {
    const report = structuredClone(bundle.result) as ReportData
    const before = structuredClone(report)
    for (const width of BIN_PRESETS[metric].widths) {
      const r = ready(histogramAggregation(report, metric, width)); conserved(r)
      expect(r.slots.map(s => s.n)).toEqual(metric === 'annualized_basis_ratio' ? [140, 147, 147, 147] : [147, 147, 147, 147])
      expect(histogramAggregation(report, metric, width)).toEqual(r)
    }
    expect(report).toEqual(before)
  })
  it.each([
    (r: ReportData) => { r.distributions[0].binding.pop() },
    (r: ReportData) => { r.accounting.push({ ...r.accounting[0], slot: 'unknown' }) },
    (r: ReportData) => { const view = r.views.history.basis_value; if (view.version === 2) view.layers.push({ ...view.layers[0], id: 'unknown' }) },
    (r: ReportData) => { r.distributions[0].binding[0] = ['IM', '2024-10-02', 'Q2'] },
    (r: ReportData) => { r.distributions.push(r.distributions[0]) },
    (r: ReportData) => { r.accounting[0].outcomes[0].identities = [] },
    (r: ReportData) => { r.distributions[0].methods[0].result!.sample_count = 999 },
    (r: ReportData) => { r.distributions[0].methods = [] },
    (r: ReportData) => { r.views.history.basis_value.layers = [] },
    (r: ReportData) => { if(r.views.history.basis_value.version === 2) r.views.history.basis_value.layers[0].layer.data[0].y = Infinity },
    (r: ReportData) => { r.distributions[0].binding = [r.distributions[0].binding[0], r.distributions[0].binding[0]] },
    (r: ReportData) => { r.distributions[0].request.histogram!.unit = 'wrong' },
  ])('refuses corrupt/incomplete/mismatched inputs %#', change => {
    const report = histogramFixture([[1, 2], [3, 4], [5, 6], [7, 8]])
    change(report)
    expect(histogramAggregation(report, 'basis_value', 10).status).toBe('inconsistent')
  })
  it('retains IntervalCount failure even when a stale successful result exists', () => {
    const report = histogramFixture([[-50], [1]])
    report.distributions[0].methods[0].failure_category = 'CalculationFailure'
    const r = ready(histogramAggregation(report, 'basis_value', 10))
    expect(r.slots[0].failure).toBe('CalculationFailure'); expect(r.edges[0]).toBe(-50)
  })
  it('treats no_eligible_sample as an empty finding only for an empty Eligible population', () => {
    const r = ready(histogramAggregation(histogramFixture([[], [1, 2], [], []]), 'basis_value', 10))
    expect(r.slots.map(s => s.failure)).toEqual([null, null, null, null])
    expect(r.slots[0].bins).toEqual([])
    expect(r.slots[1].n).toBe(2); conserved(r)
  })
  it('rejects the whole Metric when a nonempty Eligible Slot reports no_eligible_sample', () => {
    const report = histogramFixture([[1], [2], [3], [4]])
    report.distributions[1].methods[0].failure_category = 'no_eligible_sample'
    const result = histogramAggregation(report, 'basis_value', 10)
    expect(result.status).toBe('inconsistent')
    if (result.status !== 'inconsistent') throw new Error('expected inconsistent')
    expect(result.message).toContain('M1')
    expect(result.message).toContain('no_eligible_sample')
  })
  it('keeps one Slot formal failure from erasing sibling Slot results or shared edges', () => {
    const report = histogramFixture([[-5], [1, 2, 3], [4], [7]])
    report.distributions[0].methods[0].failure_category = 'CalculationFailure'
    const r = ready(histogramAggregation(report, 'basis_value', 5))
    expect(r.slots[0].failure).toBe('CalculationFailure')
    expect(r.slots.slice(1).map(s => [s.failure, s.n])).toEqual([[null, 3], [null, 1], [null, 1]])
    expect(r.edges[0]).toBe(-5); conserved(r)
  })
  it('allows the exact capacity limit and refuses one additional bin', () => {
    const atLimit = ready(histogramAggregation(histogramFixture([[0, 10000]]), 'basis_value', 5))
    expect(atLimit.edges).toHaveLength(2001); conserved(atLimit)
    expect(histogramAggregation(histogramFixture([[0, 10005]]), 'basis_value', 5).status).toBe('capacity')
  })
  it.each([1e10, Number.MAX_VALUE])('explicitly refuses excessive range/unsafe edges %s', max => {
    expect(histogramAggregation(histogramFixture([[0, max]]), 'basis_value', 5).status).toBe('capacity')
  })
})
