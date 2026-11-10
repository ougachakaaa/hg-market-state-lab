import { expect, it } from 'vitest'
import type { PremiumPlane, PremiumPoint } from '../api/moOptionPremium'
import { premiumPlaneCsv } from './csvExport'

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

it('exports exactly one row per real Point with all 16 leaves and backend context', () => {
  const result = premiumPlaneCsv(plane)
  expect(result.filename).toBe('mo-premium-plane_2026-09-21_low.csv')
  const lines = result.csv.slice(1).split('\r\n')
  const headers = lines[0].split(',')
  expect(headers.slice(0, 15)).toEqual(['observation_kind', 'observation_value', 'option_product', 'price_type', 'underlying_instrument_id', 'underlying_price', 'expiry_date', 'dte', 'futures_present', 'futures_instrument_id', 'futures_price', 'instrument_id', 'option_type', 'strike', 'premium'])
  expect(headers.slice(15)).toEqual([
    'metric_underlying_spot_total_unannualized_points', 'metric_underlying_spot_total_unannualized_yield',
    'metric_underlying_spot_total_annualized_points', 'metric_underlying_spot_total_annualized_yield',
    'metric_underlying_spot_time_value_unannualized_points', 'metric_underlying_spot_time_value_unannualized_yield',
    'metric_underlying_spot_time_value_annualized_points', 'metric_underlying_spot_time_value_annualized_yield',
    'metric_expiry_futures_total_unannualized_points', 'metric_expiry_futures_total_unannualized_yield',
    'metric_expiry_futures_total_annualized_points', 'metric_expiry_futures_total_annualized_yield',
    'metric_expiry_futures_time_value_unannualized_points', 'metric_expiry_futures_time_value_unannualized_yield',
    'metric_expiry_futures_time_value_annualized_points', 'metric_expiry_futures_time_value_annualized_yield',
  ])
  expect(lines.length - 2).toBe(plane.points.length)
  expect(lines[1]).toBe('trade_date,2026-09-21,MO,low,000852.SH,7312.456789,2026-09-25,123,true,IM,0,A,call,7100,0,1,0.0123456789012345,3,-0.04,5,0,7,null,9,0.1,11,0.12,null,-0.14,15,0.16')
  expect(lines[2].split(',').slice(11, 15)).toEqual(['B', 'put', '7000', 'null'])
  expect(lines[3].split(',').slice(6, 15)).toEqual(['2026-10-23', '456', 'false', 'null', 'null', 'C', 'call', '9000', '-2'])
  for (const line of lines.slice(1, -1)) expect(line.split(',')).toHaveLength(31)
  expect(premiumPlaneCsv({ ...plane, points: [] }).csv).toBe('\uFEFF' + lines[0] + '\r\n')
})
it('fails explicitly on missing or duplicate expiry context', () => {
  expect(() => premiumPlaneCsv({ ...plane, expiries: [] })).toThrow('Missing')
  expect(() => premiumPlaneCsv({ ...plane, expiries: [...plane.expiries, plane.expiries[0]] })).toThrow('Duplicate')
})
