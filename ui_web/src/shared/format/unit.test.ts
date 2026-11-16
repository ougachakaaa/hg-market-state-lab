import { expect, it } from 'vitest'
import { formatUnit, isRatioUnit, unitKind } from './unit'

it.each([[0.15342, '15.3%'], [-0.0868, '-8.7%'], [0, '0.0%'], [-0, '0.0%'], [-0.000001, '0.0%'], [0.000001, '0.0%']])('formats explicit decimal ratios %s', (value, expected) => {
  expect(formatUnit(value, 'decimal_ratio')).toBe(expected)
})
it('formats probability and frequency as percentages', () => {
  expect(formatUnit(0.5, 'probability')).toBe('50.0%')
  expect(formatUnit(0.15342, 'frequency')).toBe('15.3%')
})
it('formats non-integer values with two decimals and counts as integers', () => {
  for (const unit of ['index_points', 'index_points_per_365_natural_days', undefined]) expect(formatUnit(0.15342, unit)).toBe('0.15')
  expect(formatUnit(10, 'index_points')).toBe('10.00')
  expect(formatUnit(2, 'count')).toBe('2')
  expect(formatUnit(-0, 'count')).toBe('0')
})
it('retains plain date/category text and explicit missing presentation', () => {
  expect(formatUnit(123, 'date')).toBe('123')
  expect(formatUnit(123, 'category')).toBe('123')
  for (const value of [null, undefined, NaN, Infinity]) expect(formatUnit(value, 'decimal_ratio')).toBe('不适用')
})
it('classifies only explicit ratio/count/plain units', () => {
  expect(unitKind('decimal_ratio')).toBe('ratio')
  expect(unitKind('probability')).toBe('ratio')
  expect(unitKind('frequency')).toBe('ratio')
  expect(isRatioUnit('frequency')).toBe(true)
  expect(unitKind('count')).toBe('count')
  expect(unitKind('date')).toBe('plain')
  expect(unitKind('category')).toBe('plain')
  expect(unitKind('index_points')).toBe('decimal')
  expect(unitKind(undefined)).toBe('decimal')
})
