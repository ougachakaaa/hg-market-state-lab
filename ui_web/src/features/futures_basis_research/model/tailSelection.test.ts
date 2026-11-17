import { expect, it } from 'vitest'
import { histogramFixture } from './histogramAggregation.fixture'
import { BIN_PRESETS, histogramAggregation, TAIL_EXCLUSION_OPTIONS, type BasisMetric, type HistogramProjection } from './histogramAggregation'

function audit(result: HistogramProjection) {
  if (result.status === 'inconsistent') throw new Error(result.message)
  return result.selections
}

const hundred = Array.from({ length: 100 }, (_, i) => i - 50)

it.each(TAIL_EXCLUSION_OPTIONS)('selects exact ranks and preserves identities for %s percent', pct => {
  const report = histogramFixture([hundred, hundred.slice(0, 50), [0, -0, 0], []])
  const before = structuredClone(report)
  const result = histogramAggregation(report, 'basis_value', 10, pct)
  expect(result.status).toBe('ready')
  if (result.status !== 'ready') throw new Error('expected ready')
  for (const [i, selection] of result.selections.entries()) {
    const k = Math.floor(selection.original.length * pct / 100)
    expect(selection.excluded).toHaveLength(i < 2 ? 2 * k : 0)
    expect(selection.lowerCutoff).toBe(k ? selection.original[k].value : null)
    expect(selection.upperCutoff).toBe(k ? selection.original.at(-k - 1)!.value : null)
    expect(selection.original.length).toBe(selection.retained.length + selection.excluded.length)
    expect(selection.excluded.length).toBe(selection.lowerExcludedN + selection.upperExcludedN)
    expect(selection.actualExcludedFraction).toBe(selection.original.length ? selection.excluded.length / selection.original.length : null)
    const rows = [...selection.retained, ...selection.excluded]
    expect(new Set(rows.map(row => row.date)).size).toBe(selection.original.length)
    expect(rows.map(({ product, date, slot, metric, value, unit }) => ({ product, date, slot, metric, value, unit })).sort((a, b) => a.date.localeCompare(b.date))).toEqual(selection.original)
    expect(result.slots[i].bins.reduce((sum, bin) => sum + bin.count, 0)).toBe(selection.retained.length)
    for (const bin of result.slots[i].bins) expect(bin.frequency).toBe(bin.count / selection.retained.length)
    if (selection.retained.length) expect(result.slots[i].bins.reduce((sum, bin) => sum + bin.frequency, 0)).toBeCloseTo(1)
  }
  expect(report).toEqual(before)
  expect(audit(histogramAggregation(report, 'basis_value', 20, pct))).toEqual(result.selections)
})

it('protects boundary ties, all equal values and signed zero', () => {
  const values = [...hundred]; values[0] = values[1]
  const report = histogramFixture([values, Array(100).fill(7), Array(100).fill(-0), []])
  const result = histogramAggregation(report, 'basis_value', 10, 1)
  if (result.status !== 'ready') throw new Error('expected ready')
  expect(result.selections[0].lowerExcludedN).toBe(0)
  expect(result.selections[0].upperExcludedN).toBe(1)
  expect(result.selections[0].actualExcludedFraction).toBe(.01)
  expect(result.selections[1].excluded).toEqual([])
  expect(result.selections[1].lowerCutoff).toBe(7)
  expect(result.selections[2].excluded).toEqual([])
})

it.each(Object.keys(BIN_PRESETS) as BasisMetric[])('selects from original %s across all widths', metric => {
  const values = hundred.map(n => n / 100)
  const report = histogramFixture([values, values, values, values], metric)
  const baseline = histogramAggregation(report, metric, BIN_PRESETS[metric].default, 5)
  for (const width of BIN_PRESETS[metric].widths) {
    expect(audit(histogramAggregation(report, metric, width, 5))).toEqual(audit(baseline))
  }
  expect(audit(histogramAggregation(report, metric, BIN_PRESETS[metric].default, 0))[0].retained).toHaveLength(100)
})

it('retains audits for capacity and formal failures, rejecting corrupt originals first', () => {
  const report = histogramFixture([hundred.map(n => n * 10000), hundred, [], []])
  report.distributions[0].methods[0].failure_category = 'CalculationFailure'
  const capacity = histogramAggregation(report, 'basis_value', 2, 10)
  expect(capacity.status).toBe('capacity')
  if (capacity.status !== 'capacity') throw new Error('expected capacity')
  expect(capacity.selections[0].excluded).toHaveLength(20)
  const valid = histogramFixture([hundred, hundred, [], []])
  valid.distributions[0].methods[0].failure_category = 'CalculationFailure'
  const result = histogramAggregation(valid, 'basis_value', 10, 10)
  if (result.status !== 'ready') throw new Error('expected ready')
  expect(result.slots[0].failure).toBe('CalculationFailure')
  expect(result.selections[0].retained).toHaveLength(80)
  valid.distributions[0].binding.pop()
  expect(histogramAggregation(valid, 'basis_value', 10, 10).status).toBe('inconsistent')
})

it('preserves empty population audit without cutoffs', () => {
  const result = histogramAggregation(histogramFixture([]), 'basis_value', 10, 10)
  expect(result.status).toBe('empty')
  if (result.status !== 'empty') throw new Error('expected empty')
  expect(result.selections.every(s => s.lowerCutoff === null && s.retainedMin === null && s.excluded.length === 0)).toBe(true)
})
