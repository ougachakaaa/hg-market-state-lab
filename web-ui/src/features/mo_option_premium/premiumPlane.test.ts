import { describe, expect, it } from 'vitest'
import type { PremiumPlane } from './api/moOptionPremium'
import {
  classifyStrikeRelativeToReference,
  formatMetric,
  formatPlaneNumber,
  projectPremiumPlane,
  resolveMetric,
} from './premiumPlane'

const plane = {
  observation: { kind: 'trade_date', value: '2026-09-21' }, option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', dte: 5, futures: { instrument_id: 'IM2609.CFE', price: 7301.6 } },
    { expiry_date: '2026-10-23', dte: 33, futures: null },
  ],
  points: [
    { instrument_id: 'A', expiry_date: '2026-09-25', option_type: 'call', strike: 7012.45, premium: 1, annualized_premium_points: 0, annualized_time_value_points: 0, annualized_seller_premium_yield: 0, annualized_time_value_yield: 0 },
    { instrument_id: 'B', expiry_date: '2026-09-25', option_type: 'call', strike: 7200, premium: null, annualized_premium_points: null, annualized_time_value_points: null, annualized_seller_premium_yield: null, annualized_time_value_yield: null },
    { instrument_id: 'C', expiry_date: '2026-10-23', option_type: 'call', strike: 7305, premium: 1, annualized_premium_points: 12.34, annualized_time_value_points: -12.34, annualized_seller_premium_yield: 0.0998, annualized_time_value_yield: -0.0123 },
    { instrument_id: 'D', expiry_date: '2026-10-23', option_type: 'call', strike: 7612.45, premium: 1, annualized_premium_points: 9, annualized_time_value_points: 9, annualized_seller_premium_yield: 0.1, annualized_time_value_yield: 0.01 },
    { instrument_id: 'E', expiry_date: '2026-09-25', option_type: 'put', strike: 7300, premium: 1, annualized_premium_points: 20, annualized_time_value_points: 20, annualized_seller_premium_yield: 0.2, annualized_time_value_yield: 0.02 },
    { instrument_id: 'F', expiry_date: '2026-09-25', option_type: 'call', strike: 7700, premium: 1, annualized_premium_points: 30, annualized_time_value_points: 30, annualized_seller_premium_yield: 0.3, annualized_time_value_yield: 0.03 },
  ],
} satisfies PremiumPlane

describe('premium plane projection', () => {
  it('uses the full real-strike sparse union and preserves expiry order', () => {
    const projection = projectPremiumPlane(
      plane, 'call', 'total', 'points', new Set(['2026-10-23', '2026-09-25']),
    )

    expect(projection.expiries.map((expiry) => expiry.expiry_date)).toEqual(['2026-09-25', '2026-10-23'])
    expect(projection.rows.map((row) => row.strike)).toEqual([7012.45, 7200, 7305, 7612.45, 7700])
    expect(projection.rows[0].cells).toEqual([{ kind: 'value', value: 0 }, { kind: 'absent' }])
    expect(projection.rows[1].cells).toEqual([{ kind: 'unavailable' }, { kind: 'absent' }])
    expect(projection.rows[2].cells).toEqual([{ kind: 'absent' }, { kind: 'value', value: 12.34 }])
  })

  it('filters by side and selected expiry without creating coordinates', () => {
    expect(projectPremiumPlane(plane, 'put', 'total', 'points', new Set(['2026-09-25'])))
      .toMatchObject({ rows: [{ strike: 7300, cells: [{ kind: 'value', value: 20 }] }] })
    expect(projectPremiumPlane(plane, 'put', 'total', 'points', new Set(['2026-10-23'])).rows)
      .toEqual([])
  })

  it('projects the third metric while preserving negative, zero, null and absence', () => {
    const projection = projectPremiumPlane(
      plane, 'call', 'time_value', 'points', new Set(['2026-09-25', '2026-10-23']),
    )

    expect(projection.rows[0].cells).toEqual([{ kind: 'value', value: 0 }, { kind: 'absent' }])
    expect(projection.rows[1].cells).toEqual([{ kind: 'unavailable' }, { kind: 'absent' }])
    expect(projection.rows[2].cells).toEqual([{ kind: 'absent' }, { kind: 'value', value: -12.34 }])
  })

  it('maps the two presentation axes to all four backend facts', () => {
    expect(resolveMetric('total', 'points')).toBe('annualized_premium_points')
    expect(resolveMetric('time_value', 'points')).toBe('annualized_time_value_points')
    expect(resolveMetric('total', 'yield')).toBe('annualized_seller_premium_yield')
    expect(resolveMetric('time_value', 'yield')).toBe('annualized_time_value_yield')

    const projection = projectPremiumPlane(
      plane, 'call', 'time_value', 'yield', new Set(['2026-09-25', '2026-10-23']),
    )
    expect(projection.rows[2].cells).toEqual([
      { kind: 'absent' },
      { kind: 'value', value: -0.0123 },
    ])
  })

  it('classifies raw strikes against spot or futures and keeps null references neutral', () => {
    expect(classifyStrikeRelativeToReference(7305, plane.underlying.price)).toBe('below-reference')
    expect(classifyStrikeRelativeToReference(7305, plane.expiries[0].futures!.price)).toBe('above-reference')
    expect(classifyStrikeRelativeToReference(7305, plane.expiries[1].futures?.price ?? null)).toBe('neutral')
    expect(classifyStrikeRelativeToReference(7312.45, 7312.45)).toBe('at-reference')
    expect(formatPlaneNumber(7312.45)).toBe(formatPlaneNumber(7312.46))
    expect(classifyStrikeRelativeToReference(7312.45, 7312.46)).toBe('below-reference')
  })

  it('formats display values without changing facts', () => {
    expect(formatPlaneNumber(7312.45)).toBe('7312.5')
    expect(formatMetric(3825.24, 'points')).toBe('3825.2')
    expect(formatMetric(-12.34, 'points')).toBe('-12.3')
    expect(formatMetric(0, 'points')).toBe('0.0')
    expect(formatMetric(0.0998, 'yield')).toBe('9.98%')
    expect(formatMetric(-0.0123, 'yield')).toBe('-1.23%')
    expect(formatMetric(0, 'yield')).toBe('0.00%')
  })
})
