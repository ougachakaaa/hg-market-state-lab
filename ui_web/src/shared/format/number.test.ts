import { expect, it } from 'vitest'
import { formatDecimal, formatInteger, formatPercent } from './number'

it.each([
  [0.15342, '15.3%'], [-0.0868, '-8.7%'], [0, '0.0%'], [-0, '0.0%'],
  [-0.000001, '0.0%'], [0.000001, '0.0%'], [1, '100.0%'],
])('formats decimal ratios as one-decimal percentages (%s)', (value, expected) => {
  expect(formatPercent(value)).toBe(expected)
})

it.each([
  [0.15342, '0.15'], [7312.456, '7312.46'], [-12.3, '-12.30'], [0, '0.00'],
  [-0, '0.00'], [-0.000001, '0.00'], [7000, '7000.00'], [1000, '1000.00'],
])('formats non-integer values as two decimals without grouping (%s)', (value, expected) => {
  expect(formatDecimal(value)).toBe(expected)
})

it.each([[5, '5'], [0, '0'], [-0, '0'], [5.0, '5']])('retains integer counts (%s)', (value, expected) => {
  expect(formatInteger(value)).toBe(expected)
})

it('uses explicit missing presentation for absent or non-finite values', () => {
  for (const value of [null, undefined, NaN, Infinity, -Infinity]) {
    expect(formatPercent(value)).toBe('不适用')
    expect(formatDecimal(value)).toBe('不适用')
    expect(formatInteger(value)).toBe('不适用')
  }
  expect(formatPercent(null, 'N/A')).toBe('N/A')
  expect(formatDecimal(undefined, '—')).toBe('—')
  expect(formatInteger(NaN, '未提供')).toBe('未提供')
})
