export const MIN_STRIKE_HALF_RANGE_POINTS = 300
export const STRIKE_HALF_RANGE_STEP = 100
const EDGE_PADDING_RATIO = 0.02

export function strikeViewport(spot: number, halfRangePoints: number): [number, number] {
  const edgePadding = halfRangePoints * 2 * EDGE_PADDING_RATIO
  return [
    spot - halfRangePoints - edgePadding,
    spot + halfRangePoints + edgePadding,
  ]
}
