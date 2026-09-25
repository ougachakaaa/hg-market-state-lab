import type { ExpiryGroup } from '../api/moOptionChain'
import type { SeriesColors } from '../model/presentationState'

export type ExpiryColors = SeriesColors & { opacity: number }

function withOpacity(color: string, opacity: number): string {
  const red = parseInt(color.slice(1, 3), 16)
  const green = parseInt(color.slice(3, 5), 16)
  const blue = parseInt(color.slice(5, 7), 16)
  return `rgba(${red}, ${green}, ${blue}, ${opacity})`
}

export function buildExpiryPalette(expiries: ExpiryGroup[], colors: SeriesColors): Record<string, ExpiryColors> {
  const ordered = [...expiries].sort((a, b) => a.expiry_date.localeCompare(b.expiry_date))
  return Object.fromEntries(ordered.map((group, rank) => {
    const opacity = ordered.length === 1 ? 1
      : rank === ordered.length - 1 ? 0.15
      : 1 - 0.85 * rank / (ordered.length - 1)
    return [group.expiry_date, {
      opacity,
      call: withOpacity(colors.call, opacity),
      put: withOpacity(colors.put, opacity),
      futures: withOpacity(colors.futures, opacity),
    }]
  }))
}
