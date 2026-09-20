import type { ExpiryGroup, OptionPoint } from './api/moOptionChain'

export type ChartPoint = OptionPoint & { side: 'Call' | 'Put'; price: number }

function drawable(points: OptionPoint[], side: ChartPoint['side']): ChartPoint[] {
  return points.flatMap((point) => point.price === null ? [] : [{ ...point, price: point.price, side }])
}

function paddedDomain(values: number[]): [number, number] {
  const minimum = Math.min(...values)
  const maximum = Math.max(...values)
  const padding = maximum === minimum
    ? Math.max(Math.abs(maximum) * 0.02, 1)
    : (maximum - minimum) * 0.04
  return [minimum - padding, maximum + padding]
}

export function projectExpiry(group: ExpiryGroup) {
  const calls = drawable(group.calls, 'Call')
  const puts = drawable(group.puts, 'Put')
  const points = [...calls, ...puts]

  return {
    calls,
    puts,
    missingPriceCount: group.calls.length + group.puts.length - points.length,
    yDomain: paddedDomain([0, ...points.map((point) => point.price)]),
  }
}
