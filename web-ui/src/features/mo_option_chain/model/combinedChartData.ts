import type { ExpiryGroup, OptionChain } from '../api/moOptionChain'

export function missingPriceCount(group: ExpiryGroup): number {
  return [...group.calls, ...group.puts].filter((point) => point.price === null).length
}

export function projectCombinedChain(
  chain: OptionChain,
  selectedExpiries: ReadonlySet<string>,
  xDomain: [number, number],
) {
  const groups = chain.expiries.filter((group) => selectedExpiries.has(group.expiry_date))
  let visibleMax = 0
  let visibleMin = 0
  let hasDrawablePrice = false
  for (const group of groups) {
    for (const point of [...group.calls, ...group.puts]) {
      if (point.price === null) continue
      hasDrawablePrice = true
      if (xDomain[0] <= point.strike && point.strike <= xDomain[1]) {
        visibleMax = Math.max(visibleMax, point.price)
        visibleMin = Math.min(visibleMin, point.price)
      }
    }
  }
  const upper = Math.max(100, Math.ceil(visibleMax * 1.2 / 100) * 100)
  const lower = visibleMin - Math.max(1, upper * 0.02)

  return { groups, yDomain: [lower, upper] as [number, number], hasDrawablePrice }
}
