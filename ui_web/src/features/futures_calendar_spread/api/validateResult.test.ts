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
