import { describe, expect, it } from 'vitest'
import { validateResult } from './validateResult'
import daily from '../testing/daily.json'
import closed from '../testing/closed.json'
import empty from '../testing/empty.json'
import excluded from '../testing/excluded.json'
describe('Daily result association', () => {
  it.each([daily, closed, empty, excluded])('accepts the actual HTTP DTO projection', r => expect(validateResult(r)).toBe(r))
  it('retains zero and null, and rejects an echoed identity mismatch', () => {
    expect(validateResult(daily).day.observations[2].metrics!.signed_spread.value).toBe(0)
    expect(validateResult(empty).day.observations[0].metrics).toBeNull()
    expect(() => validateResult(daily, { product_code: 'IF', trade_date: daily.request.trade_date })).toThrow()
  })
  it.each([
    (r: any) => r.day.observations.reverse(),
    (r: any) => r.day.observations[0].metrics.signed_spread.value = NaN,
    (r: any) => r.day.observations[0].trade_date = '2024-02-30',
    (r: any) => r.accounting.valid_count = 5,
    (r: any) => r.day.observations[0].metrics.signed_spread.unit = 'decimal_ratio',
    (r: any) => r.day.observations[0].near = null,
  ])('rejects malformed or inconsistent results', mutate => { const r = structuredClone(daily); mutate(r); expect(() => validateResult(r)).toThrow() })
})

import { referenceStates, withReference } from '../testing/reference'
it.each(referenceStates)('accepts independent reference state %s/%s/%s without mutation', (...state) => {
  const r = withReference(daily, state)
  const before = JSON.stringify(r)
  expect(validateResult(r)).toBe(r)
  expect(JSON.stringify(r)).toBe(before)
})
it.each(['IF', 'IH', 'IC', 'IM'] as const)('validates the authority index mapping for %s', product => {
  const r = withReference(closed)
  r.request.product_code = product
  r.underlying_index!.index_code = { IF: '000300.SH', IH: '000016.SH', IC: '000905.SH', IM: '000852.SH' }[product] as NonNullable<typeof r.underlying_index>['index_code']
  expect(validateResult(r)).toBe(r)
  r.underlying_index!.index_code = product === 'IM' ? '000300.SH' : '000852.SH'
  expect(() => validateResult(r)).toThrow()
})
it.each([
  (r: any) => r.underlying_index = null,
  (r: any) => r.underlying_index.index_code = '000300.SH',
  (r: any) => r.underlying_index.trade_date = '2024-10-19',
  (r: any) => r.underlying_index.extra = true,
  (r: any) => r.underlying_index.close = null,
  (r: any) => r.underlying_index.close = Infinity,
  (r: any) => r.underlying_index.reason_code = 'cache_incomplete',
  (r: any) => r.underlying_index.failure_category = 'incomplete_inputs',
  ...['index_code', 'trade_date', 'close', 'availability', 'reason_code', 'failure_category'].map(field => (r: any) => delete r.underlying_index[field]),
])('rejects invalid reference structure and association', mutate => {
  const r = withReference(); mutate(r); expect(() => validateResult(r)).toThrow()
})
it('rejects every cross-state reason/category/close mismatch', () => {
  for (const state of referenceStates) for (const other of referenceStates) {
    const r = withReference(daily, state)
    Object.assign(r.underlying_index!, { reason_code: other[1], failure_category: other[2] })
    if (state[0] !== other[0]) expect(() => validateResult(r)).toThrow()
  }
  const r = withReference(daily, referenceStates[2]); r.underlying_index!.close = 0
  expect(() => validateResult(r)).toThrow()
  r.underlying_index!.close = null; r.underlying_index!.failure_category = 'incomplete_inputs'
  expect(() => validateResult(r)).toThrow()
})
