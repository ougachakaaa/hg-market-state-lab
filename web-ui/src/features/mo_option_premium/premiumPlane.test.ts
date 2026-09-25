import { describe, expect, it } from 'vitest'
import type { PremiumPlane } from './api/moOptionPremium'
import {
  classifyStrikeRelativeToReference,
  formatMetric,
  projectPremiumPlane,
  resolveMetric,
} from './premiumPlane'

function leaf(points: number | null, yieldValue: number | null) {
  return { points, yield: yieldValue }
}

function metrics(value: number | null) {
  const annualized = value === null ? null : value * 10
  const normalized = {
    unannualized: leaf(value, value === null ? null : value / 1000),
    annualized: leaf(annualized, annualized === null ? null : annualized / 1000),
  }
  return {
    underlying_spot: { total: normalized, time_value: normalized },
    expiry_futures: { total: normalized, time_value: normalized },
  }
}

const plane = {
  observation: { kind: 'trade_date', value: '2026-09-21' }, option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', dte: 5, futures: { instrument_id: 'IM2609.CFE', price: 7301.6 } },
    { expiry_date: '2026-10-23', dte: 33, futures: null },
  ],
  points: [
    { instrument_id: 'A', expiry_date: '2026-09-25', option_type: 'call', strike: 7012.45, premium: 1, metrics: metrics(0) },
    { instrument_id: 'B', expiry_date: '2026-09-25', option_type: 'call', strike: 7200, premium: null, metrics: metrics(null) },
    { instrument_id: 'C', expiry_date: '2026-10-23', option_type: 'call', strike: 7305, premium: 1, metrics: metrics(-12.34) },
    { instrument_id: 'D', expiry_date: '2026-10-23', option_type: 'call', strike: 7612.45, premium: 1, metrics: metrics(9) },
    { instrument_id: 'E', expiry_date: '2026-09-25', option_type: 'put', strike: 7300, premium: 1, metrics: metrics(20) },
  ],
} satisfies PremiumPlane

describe('premium plane projection', () => {
  it('resolves every four-axis coordinate without recalculating it', () => {
    const point = plane.points[2]
    for (const reference of ['underlying_spot', 'expiry_futures'] as const) {
      for (const value of ['total', 'time_value'] as const) {
        for (const normalization of ['unannualized', 'annualized'] as const) {
          for (const representation of ['points', 'yield'] as const) {
            expect(resolveMetric(point, reference, value, normalization, representation))
              .toBe(point.metrics[reference][value][normalization][representation])
          }
        }
      }
    }
  })

  it('uses the full sparse strike union and preserves absence, null, zero, and negative values', () => {
    const projection = projectPremiumPlane(
      plane, 'call', 'underlying_spot', 'time_value', 'unannualized', 'points',
      new Set(['2026-10-23', '2026-09-25']),
    )

    expect(projection.expiries.map((expiry) => expiry.expiry_date)).toEqual(['2026-09-25', '2026-10-23'])
    expect(projection.rows.map((row) => row.strike)).toEqual([7012.45, 7200, 7305, 7612.45])
    expect(projection.rows[0].cells).toEqual([{ kind: 'value', value: 0 }, { kind: 'absent' }])
    expect(projection.rows[1].cells).toEqual([{ kind: 'unavailable' }, { kind: 'absent' }])
    expect(projection.rows[2].cells).toEqual([{ kind: 'absent' }, { kind: 'value', value: -12.34 }])
  })

  it('keeps reference coloring independent of the selected metric coordinate', () => {
    expect(classifyStrikeRelativeToReference(7305, plane.underlying.price)).toBe('below-reference')
    expect(classifyStrikeRelativeToReference(7305, plane.expiries[0].futures!.price)).toBe('above-reference')
    expect(classifyStrikeRelativeToReference(7305, plane.expiries[1].futures?.price ?? null)).toBe('neutral')
    expect(formatMetric(-0.0123, 'yield')).toBe('-1.23%')
  })
})
