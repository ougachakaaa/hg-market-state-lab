import type { ExpiryGroup, OptionPoint } from './api/moOptionChain'

export type ChartPoint = OptionPoint & { side: 'Call' | 'Put'; price: number }

function drawable(points: OptionPoint[], side: ChartPoint['side']): ChartPoint[] {
  return points.flatMap((point) => point.price === null ? [] : [{ ...point, price: point.price, side }])
}

export function projectExpiry(group: ExpiryGroup, xDomain: [number, number]) {
  const calls = drawable(group.calls, 'Call')
  const puts = drawable(group.puts, 'Put')
  const points = [...calls, ...puts]
  const visiblePrices = points
    .filter((point) => xDomain[0] <= point.strike && point.strike <= xDomain[1])
    .map((point) => point.price)
  const upper = Math.max(100, Math.ceil(Math.max(0, ...visiblePrices) * 1.2 / 100) * 100)
  const lower = Math.min(0, ...visiblePrices) - Math.max(1, upper * 0.02)

  return {
    calls,
    puts,
    missingPriceCount: group.calls.length + group.puts.length - points.length,
    yDomain: [lower, upper] as [number, number],
  }
}
