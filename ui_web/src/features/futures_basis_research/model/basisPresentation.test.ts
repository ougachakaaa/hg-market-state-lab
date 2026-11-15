import { expect, it } from 'vitest'
import { distributionMean } from './basisPresentation'
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
