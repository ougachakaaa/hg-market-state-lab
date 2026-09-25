import type { PremiumExpiry, PremiumPlane, PremiumPoint } from './api/moOptionPremium'

export const MIN_STRIKE_HALF_RANGE_POINTS = 300
export const STRIKE_HALF_RANGE_STEP = 100

export type SelectedOptionType = PremiumPoint['option_type']
export type SelectedMetric = 'annualized_premium_points' | 'annualized_seller_premium_yield'

export type PremiumCell =
  | { kind: 'absent' }
  | { kind: 'unavailable' }
  | { kind: 'value'; value: number }

export interface PremiumPlaneRow {
  strike: number
  cells: PremiumCell[]
}

export interface PremiumPlaneProjection {
  expiries: PremiumExpiry[]
  rows: PremiumPlaneRow[]
}

const oneDecimal = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  useGrouping: false,
})
const twoDecimals = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  useGrouping: false,
})

export function formatPlaneNumber(value: number): string {
  return oneDecimal.format(value)
}

export function formatMetric(value: number, metric: SelectedMetric): string {
  return metric === 'annualized_seller_premium_yield'
    ? `${twoDecimals.format(value * 100)}%`
    : oneDecimal.format(value)
}

export function projectPremiumPlane(
  plane: PremiumPlane,
  optionType: SelectedOptionType,
  metric: SelectedMetric,
  selectedExpiries: ReadonlySet<string>,
  strikeHalfRangePoints: number,
): PremiumPlaneProjection {
  const expiries = plane.expiries.filter((expiry) => selectedExpiries.has(expiry.expiry_date))
  const visibleExpiryDates = new Set(expiries.map((expiry) => expiry.expiry_date))
  const lower = plane.underlying.price - strikeHalfRangePoints
  const upper = plane.underlying.price + strikeHalfRangePoints
  const points = plane.points.filter((point) => (
    point.option_type === optionType
    && visibleExpiryDates.has(point.expiry_date)
    && point.strike >= lower
    && point.strike <= upper
  ))
  const strikes = [...new Set(points.map((point) => point.strike))].sort((left, right) => left - right)
  const pointByCoordinate = new Map(
    points.map((point) => [`${point.expiry_date}\u0000${point.strike}`, point]),
  )

  return {
    expiries,
    rows: strikes.map((strike) => ({
      strike,
      cells: expiries.map((expiry): PremiumCell => {
        const point = pointByCoordinate.get(`${expiry.expiry_date}\u0000${strike}`)
        if (point === undefined) return { kind: 'absent' }
        const value = point[metric]
        return value === null ? { kind: 'unavailable' } : { kind: 'value', value }
      }),
    })),
  }
}
