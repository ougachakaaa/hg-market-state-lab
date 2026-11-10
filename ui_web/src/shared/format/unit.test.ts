import { expect, it } from 'vitest'
import { formatUnit } from './unit'

it.each([[0.15342, '15.3%'], [-0.0868, '-8.7%'], [0, '0.0%'], [-0, '0.0%'], [-0.000001, '0.0%'], [0.000001, '0.0%']])('formats explicit decimal ratios %s', (value, expected) => {
  expect(formatUnit(value, 'decimal_ratio')).toBe(expected)
})
it('retains other units and explicit missing presentation', () => {
  for (const unit of ['frequency', 'count', 'index_points', 'probability', undefined]) expect(formatUnit(0.15342, unit)).toBe('0.15342')
  for (const value of [null, undefined, NaN, Infinity]) expect(formatUnit(value, 'decimal_ratio')).toBe('不适用')
})
