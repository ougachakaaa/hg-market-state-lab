import type { ExpiryGroup } from './api/moOptionChain'

export const DEFAULT_BASE_COLOR = '#2563eb'

function hueFromHex(color: string): number {
  const [red, green, blue] = [1, 3, 5].map((offset) => parseInt(color.slice(offset, offset + 2), 16) / 255)
  const maximum = Math.max(red, green, blue)
  const minimum = Math.min(red, green, blue)
  const chroma = maximum - minimum
  if (chroma < 0.01) return hueFromHex(DEFAULT_BASE_COLOR) // An achromatic input has no hue.
  if (maximum === red) return ((green - blue) / chroma + 6) % 6 * 60
  if (maximum === green) return ((blue - red) / chroma + 2) * 60
  return ((red - green) / chroma + 4) * 60
}

export function buildExpiryPalette(expiries: ExpiryGroup[], baseColor: string): Record<string, string> {
  const ordered = [...expiries].sort((a, b) => a.expiry_date.localeCompare(b.expiry_date))
  const hue = hueFromHex(baseColor)
  return Object.fromEntries(ordered.map((group, rank) => {
    const saturation = ordered.length === 1 ? 80 : 80 - rank * 45 / (ordered.length - 1)
    return [group.expiry_date, `hsl(${hue.toFixed(1)} ${saturation.toFixed(1)}% 42%)`]
  }))
}
