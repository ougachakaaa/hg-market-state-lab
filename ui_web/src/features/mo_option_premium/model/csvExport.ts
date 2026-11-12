import type { PremiumPlane } from '../api/validatePremiumPlane'
import { serializeCsv, type CsvCell } from '../../../shared/csv/csv'

const references = ['underlying_spot', 'expiry_futures'] as const
const values = ['total', 'time_value'] as const
const normalizations = ['unannualized', 'annualized'] as const
const representations = ['points', 'yield'] as const
const coordinates = references.flatMap((reference) => values.flatMap((value) =>
  normalizations.flatMap((normalization) => representations.map((representation) =>
    ({ reference, value, normalization, representation }))),
))
export const premiumCsvHeader = [
  'observation_kind', 'observation_value', 'option_product', 'price_type',
  'underlying_instrument_id', 'underlying_price', 'expiry_date', 'dte',
  'futures_present', 'futures_instrument_id', 'futures_price',
  'instrument_id', 'option_type', 'strike', 'premium',
  ...coordinates.map(({ reference, value, normalization, representation }) =>
    `metric_${reference}_${value}_${normalization}_${representation}`),
] as const

export function premiumPlaneCsv(plane: PremiumPlane) {
  const expiries = new Map(plane.expiries.map((expiry) => [expiry.expiry_date, expiry]))
  if (expiries.size !== plane.expiries.length) throw new Error('Duplicate expiry context')
  const rows: CsvCell[][] = plane.points.map((point) => {
    const expiry = expiries.get(point.expiry_date)
    if (!expiry) throw new Error('Missing expiry context')
    return [
      plane.observation.kind, plane.observation.value, plane.option_product, plane.price_type,
      plane.underlying.instrument_id, plane.underlying.price, point.expiry_date, expiry.dte,
      expiry.futures !== null, expiry.futures?.instrument_id ?? null, expiry.futures?.price ?? null,
      point.instrument_id, point.option_type, point.strike, point.premium,
      ...coordinates.map(({ reference, value, normalization, representation }) =>
        point.metrics[reference][value][normalization][representation]),
    ]
  })
  return {
    csv: serializeCsv(premiumCsvHeader, rows),
    filename: `mo-premium-plane_${plane.observation.value}_${plane.price_type}.csv`,
  }
}
