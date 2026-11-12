// Regression data only; not an official Synthetic Example.
import type { PremiumPlane } from '../api/validatePremiumPlane'

function leaf(points: number | null, yieldValue: number | null) {
  return { points, yield: yieldValue }
}

export const plane = {
  observation: { kind: 'trade_date', value: '2026-09-21' }, option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', dte: 5, futures: { instrument_id: 'IM2609.CFE', price: 7301.6 } },
    { expiry_date: '2026-10-23', dte: 33, futures: null },
  ],
  points: [
    { instrument_id: 'A', expiry_date: '2026-09-25', option_type: 'call', strike: 7000, premium: 0, metrics: {
      underlying_spot: { total: { unannualized: leaf(0, 0), annualized: leaf(0, 0) }, time_value: { unannualized: leaf(-3, -0.003), annualized: leaf(-30, -0.03) } },
      expiry_futures: { total: { unannualized: leaf(0, 0), annualized: leaf(0, 0) }, time_value: { unannualized: leaf(-2, -0.002), annualized: leaf(-20, -0.02) } },
    } },
    { instrument_id: 'B', expiry_date: '2026-10-23', option_type: 'call', strike: 7300, premium: 1, metrics: {
      underlying_spot: { total: { unannualized: leaf(1, 0.001), annualized: leaf(10, 0.01) }, time_value: { unannualized: leaf(-1, -0.001), annualized: leaf(-10, -0.01) } },
      expiry_futures: { total: { unannualized: leaf(1, null), annualized: leaf(10, null) }, time_value: { unannualized: leaf(null, null), annualized: leaf(null, null) } },
    } },
    { instrument_id: 'P', expiry_date: '2026-09-25', option_type: 'put', strike: 7300, premium: 1, metrics: {
      underlying_spot: { total: { unannualized: leaf(20, 0.02), annualized: leaf(200, 0.2) }, time_value: { unannualized: leaf(20, 0.02), annualized: leaf(200, 0.2) } },
      expiry_futures: { total: { unannualized: leaf(20, 0.02), annualized: leaf(200, 0.2) }, time_value: { unannualized: leaf(20, 0.02), annualized: leaf(200, 0.2) } },
    } },
  ],
} satisfies PremiumPlane
