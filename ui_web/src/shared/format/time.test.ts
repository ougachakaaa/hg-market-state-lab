import { expect, it } from 'vitest'
import { formatBeijingTime } from './time'

it('converts UTC instants to Beijing time, including day rollover', () => {
  expect(formatBeijingTime('2026-11-09T00:00:00Z')).toBe('2026-11-09 08:00:00（北京时间）')
  expect(formatBeijingTime('2026-11-09T15:59:59Z')).toBe('2026-11-09 23:59:59（北京时间）')
  expect(formatBeijingTime('2026-11-09T16:00:00Z')).toBe('2026-11-10 00:00:00（北京时间）')
  expect(formatBeijingTime('2026-11-09T08:00:00+08:00')).toBe('2026-11-09 08:00:00（北京时间）')
})

it('accepts Date values and truncates sub-second precision', () => {
  expect(formatBeijingTime(new Date('2026-11-09T00:00:00.999Z'))).toBe('2026-11-09 08:00:00（北京时间）')
})

it('rejects date-only, malformed and missing values instead of guessing a timezone', () => {
  for (const value of ['2026-11-09', '2026-11-09T00:00:00', 'not-a-date', null, undefined]) {
    expect(formatBeijingTime(value)).toBe('—')
  }
  expect(formatBeijingTime(null, '未提供')).toBe('未提供')
  expect(formatBeijingTime('2026-11-09', 'N/A')).toBe('N/A')
  expect(formatBeijingTime(new Date('invalid'))).toBe('—')
})
