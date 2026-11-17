import { expect, it } from 'vitest'
import { count, number } from './format'

it('formats ratios as one-decimal percentages and other values as two decimals', () => {
  expect(number(1.1222005041476968, true)).toBe('112.2%')
  expect(number(-0.5206418459215554, true)).toBe('-52.1%')
  expect(number(0, true)).toBe('0.0%')
  expect(number(-0, true)).toBe('0.0%')
  expect(number(117.74193548387096)).toBe('117.74')
  expect(number(-10)).toBe('-10.00')
  expect(number(0)).toBe('0.00')
})

it('retains integer counts and feature missing text', () => {
  expect(count(31)).toBe('31')
  expect(count(0)).toBe('0')
  expect(number(null)).toBe('未提供')
  expect(number(undefined, true)).toBe('未提供')
  expect(count(NaN)).toBe('未提供')
})

import { sourceNote } from './format'
it('translates known source notes and preserves unknown prose verbatim', () => {
  expect(sourceNote('Read-only queries require separately prepared complete caches; they never ensure or repair missing data.')).toContain('只读查询')
  expect(sourceNote('Unrecognized captured statement.')).toBe('Unrecognized captured statement.')
})
