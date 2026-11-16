import { expect, it } from 'vitest'
import { distributionMean, distributionSummary } from './basisPresentation'
import type { Distribution, Method } from '../report/types'

const mean: Method = { spec: { method: 'mean' }, failure_category: null, reason: null,
  result: { method: 'mean', unit: 'decimal_ratio', sample_count: 2, value: .15342 } }
function distribution(methods: Method[]): Distribution {
  return { request: { analysis_id: 'test', metric: 'basis_ratio', slot: 'M0' }, candidates: [], binding: [], methods }
}
it('selects mean by identity and preserves producer values and units', () => {
  const source = distribution([{ ...mean, spec: { method: 'quantile' } }, mean])
  const before = structuredClone(source)
  expect(distributionMean(source)).toBe('15.3%')
  expect(source).toEqual(before)
})
it('preserves zero and explicit unavailable states', () => {
  expect(distributionMean(distribution([{ ...mean, result: { ...mean.result!, value: 0 } }]))).toBe('0.0%')
  expect(distributionMean(distribution([]))).toBe('不可用')
  expect(distributionMean(distribution([{ ...mean, result: null }]))).toBe('不可用')
  expect(distributionMean(distribution([{ ...mean, failure_category: 'no_eligible_sample', result: null }]))).toContain('no_eligible_sample')
})

it('projects four ordered Slots, exact quantile identities and independent Metric populations', () => {
  const quantile: Method = { ...mean, spec: { method: 'quantile' }, result: {
    method: 'quantile', unit: 'index_points', sample_count: 2,
    points_and_values: [[1, 40], [.5, 20], [0, 0], [.75, 30], [.25, 10]],
  } }
  const source = ['Q2', 'M1', 'Q1', 'M0'].map((slot, i) => ({
    ...distribution([quantile, { ...mean, result: { ...mean.result!, unit: 'index_points', value: i } }]),
    request: { analysis_id: slot, metric: 'basis_value', slot }, binding: [{}, {}],
  }))
  const before = structuredClone(source)
  expect(distributionSummary(source, 'basis_value')).toEqual(['M0', 'M1', 'Q1', 'Q2'].map((slot, i) => ({
    slot, n: 2, min: '0', p25: '10', median: '20', p75: '30', max: '40', mean: String([3, 1, 2, 0][i]),
  })))
  expect(distributionSummary(source, 'basis_ratio').every(row => row.n === '不可用')).toBe(true)
  expect(source).toEqual(before)
})

it('keeps failed, absent, mismatched and empty methods unavailable without losing successful siblings', () => {
  const quantile: Method = { ...mean, spec: { method: 'quantile' }, result: {
    method: 'quantile', unit: 'decimal_ratio', sample_count: 2, points_and_values: [[0, -.1], [.5, 0], [1, .1]],
  } }
  const row = (methods: Method[], binding: unknown[] = [{}, {}]) => distributionSummary([
    { ...distribution(methods), binding },
  ], 'basis_ratio')[0]
  expect(row([quantile, { ...mean, failure_category: 'numerical_failure' }])).toMatchObject({
    n: 2, min: '-10.0%', p25: '不可用', median: '0.0%', max: '10.0%', mean: '不可用（numerical_failure）',
  })
  expect(row([{ ...quantile, failure_category: 'numerical_failure' }, mean])).toMatchObject({ min: '不可用（numerical_failure）', mean: '15.3%' })
  expect(row([mean])).toMatchObject({ min: '不可用', mean: '15.3%' })
  expect(row([{ ...quantile, result: mean.result }])).toMatchObject({ min: '不可用', mean: '不可用' })
  expect(row([mean, quantile], [])).toMatchObject({ n: 0, min: '不可用', mean: '不可用' })
  expect(row([{ ...mean, result: { ...mean.result!, sample_count: 0 } }])).toMatchObject({ mean: '不可用' })
  expect(row([{ ...mean, failure_category: 'no_eligible_sample', result: null }], [])).toMatchObject({ n: 0, mean: '不可用（no_eligible_sample）' })
})
