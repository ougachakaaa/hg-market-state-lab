import { expect, it } from 'vitest'
import type { PremiumPlane, PremiumPoint } from '../api/moOptionPremium'
import { premiumPlaneContextJson, premiumPlaneContextFilename } from './copyText'

const metrics: PremiumPoint['metrics'] = {
  underlying_spot: {
    total: { unannualized: { points: 1, yield: 0.0123456789012345 }, annualized: { points: 3, yield: -0.04 } },
    time_value: { unannualized: { points: 5, yield: 0 }, annualized: { points: 7, yield: null } },
  },
  expiry_futures: {
    total: { unannualized: { points: 9, yield: 0.10 }, annualized: { points: 11, yield: 0.12 } },
    time_value: { unannualized: { points: null, yield: -0.14 }, annualized: { points: 15, yield: 0.16 } },
  },
}
const plane: PremiumPlane = {
  observation: { kind: 'trade_date', value: '2026-09-21' }, option_product: 'MO', price_type: 'low',
  underlying: { instrument_id: '000852.SH', price: 7312.456789 },
  expiries: [
    { expiry_date: '2026-09-25', dte: 123, futures: { instrument_id: 'IM', price: 0 } },
    { expiry_date: '2026-10-23', dte: 456, futures: null },
    { expiry_date: '2026-11-27', dte: 789, futures: null },
  ],
  points: [
    { instrument_id: 'A', expiry_date: '2026-09-25', option_type: 'call', strike: 7100, premium: 0, metrics },
    { instrument_id: 'B', expiry_date: '2026-09-25', option_type: 'put', strike: 7000, premium: null, metrics },
    { instrument_id: 'C', expiry_date: '2026-10-23', option_type: 'call', strike: 9000, premium: -2, metrics },
  ],
}

it('serializes complete Context V1 without mutating data or losing Unicode, null or zero', () => {
  const rawPayload = { ...plane, retained_unknown: { unicode: '中文 🧪 ```', values: [null, 0, -1.23456789] } }
  const before = JSON.stringify(rawPayload)
  const text = premiumPlaneContextJson(plane, rawPayload)
  const context = JSON.parse(text)
  expect(Object.keys(context)).toEqual(['format_version', 'metadata', 'data'])
  expect(context.format_version).toBe('daily-data-context-v1')
  expect(context.metadata.product).toBe('MO Premium Plane')
  expect(context.metadata.response_identity).toEqual({ observation: plane.observation, option_product: plane.option_product, price_type: plane.price_type, underlying_instrument_id: plane.underlying.instrument_id })
  expect(context.metadata.reading_notes.length).toBeGreaterThan(0)
  expect(context.metadata.reading_notes.every((note: unknown) => typeof note === 'string')).toBe(true)
  expect(context.data).toEqual(JSON.parse(before))
  expect(JSON.stringify(rawPayload)).toBe(before)
  expect(text).toBe(JSON.stringify(context, null, 2))
  expect(premiumPlaneContextFilename(plane)).toBe('mo-premium-plane_2026-09-21_low_context.json')
})
