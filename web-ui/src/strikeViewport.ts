export const MIN_STRIKE_HALF_RANGE_POINTS = 300
export const STRIKE_HALF_RANGE_STEP = 100

export function strikeViewport(spot: number, halfRangePoints: number): [number, number] {
  return [
    Math.floor((spot - halfRangePoints) / 100) * 100,
    Math.ceil((spot + halfRangePoints) / 100) * 100,
  ]
}
