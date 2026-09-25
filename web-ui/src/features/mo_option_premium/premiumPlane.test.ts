import { describe, expect, it } from 'vitest'
import type { PremiumPlane } from './api/moOptionPremium'
import { formatMetric, formatPlaneNumber, projectPremiumPlane } from './premiumPlane'

const plane = {
  observation: { kind: 'trade_date', value: '2026-09-21' }, option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', dte: 5, futures: { instrument_id: 'IM2609.CFE', price: 7301.6 } },
    { expiry_date: '2026-10-23', dte: 33, futures: null },
  ],
  points: [
    { instrument_id: 'A', expiry_date: '2026-09-25', option_type: 'call', strike: 7012.45, premium: 1, annualized_premium_points: 0, annualized_seller_premium_yield: 0 },
    { instrument_id: 'B', expiry_date: '2026-09-25', option_type: 'call', strike: 7200, premium: null, annualized_premium_points: null, annualized_seller_premium_yield: null },
    { instrument_id: 'C', expiry_date: '2026-10-23', option_type: 'call', strike: 7300, premium: 1, annualized_premium_points: 12.34, annualized_seller_premium_yield: 0.0998 },
    { instrument_id: 'D', expiry_date: '2026-10-23', option_type: 'call', strike: 7612.45, premium: 1, annualized_premium_points: 9, annualized_seller_premium_yield: 0.1 },
    { instrument_id: 'E', expiry_date: '2026-09-25', option_type: 'put', strike: 7300, premium: 1, annualized_premium_points: 20, annualized_seller_premium_yield: 0.2 },
    { instrument_id: 'F', expiry_date: '2026-09-25', option_type: 'call', strike: 7700, premium: 1, annualized_premium_points: 30, annualized_seller_premium_yield: 0.3 },
  ],
} satisfies PremiumPlane

describe('premium plane projection', () => {
  it('uses a sparse union, preserves expiry order and includes raw viewport boundaries', () => {
    const projection = projectPremiumPlane(
      plane, 'call', 'annualized_premium_points', new Set(['2026-10-23', '2026-09-25']), 300,
    )

    expect(projection.expiries.map((expiry) => expiry.expiry_date)).toEqual(['2026-09-25', '2026-10-23'])
    expect(projection.rows.map((row) => row.strike)).toEqual([7012.45, 7200, 7300, 7612.45])
    expect(projection.rows[0].cells).toEqual([{ kind: 'value', value: 0 }, { kind: 'absent' }])
    expect(projection.rows[1].cells).toEqual([{ kind: 'unavailable' }, { kind: 'absent' }])
    expect(projection.rows[2].cells).toEqual([{ kind: 'absent' }, { kind: 'value', value: 12.34 }])
  })

  it('filters by side and selected expiry without creating coordinates', () => {
    expect(projectPremiumPlane(plane, 'put', 'annualized_premium_points', new Set(['2026-09-25']), 300))
      .toMatchObject({ rows: [{ strike: 7300, cells: [{ kind: 'value', value: 20 }] }] })
    expect(projectPremiumPlane(plane, 'put', 'annualized_premium_points', new Set(['2026-10-23']), 300).rows)
      .toEqual([])
  })

  it('formats display values without changing facts', () => {
    expect(formatPlaneNumber(7312.45)).toBe('7312.5')
    expect(formatMetric(3825.24, 'annualized_premium_points')).toBe('3825.2')
    expect(formatMetric(0, 'annualized_premium_points')).toBe('0.0')
    expect(formatMetric(0.0998, 'annualized_seller_premium_yield')).toBe('9.98%')
    expect(formatMetric(0, 'annualized_seller_premium_yield')).toBe('0.00%')
  })
})
