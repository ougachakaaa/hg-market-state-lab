import { describe, expect, it } from 'vitest'
import type { ExpiryGroup } from './api/moOptionChain'
import { buildExpiryPalette, DEFAULT_BASE_COLOR } from './expiryPalette'

const expiries = ['2026-09-25', '2026-10-23', '2026-11-27', '2026-12-25']
  .map((expiry_date) => ({ expiry_date, futures: null, calls: [], puts: [] })) satisfies ExpiryGroup[]

function saturation(color: string): number {
  return Number(color.match(/ ([\d.]+)% /)?.[1])
}

describe('expiry palette', () => {
  it('uses the complete ascending response rank, with decreasing saturation', () => {
    const palette = buildExpiryPalette([...expiries].reverse(), DEFAULT_BASE_COLOR)
    const colors = expiries.map((group) => palette[group.expiry_date])
    expect(colors.every((color) => color.startsWith('hsl('))).toBe(true)
    expect(colors.map(saturation)).toEqual([...colors.map(saturation)].sort((a, b) => b - a))
    expect(new Set(colors).size).toBe(4)
    expect(buildExpiryPalette(expiries, DEFAULT_BASE_COLOR)[expiries[2].expiry_date]).toBe(palette[expiries[2].expiry_date])
  })

  it('changes the hue without changing rank and falls back to blue for gray', () => {
    const blue = buildExpiryPalette(expiries, DEFAULT_BASE_COLOR)
    const red = buildExpiryPalette(expiries, '#e11d48')
    expect(red[expiries[2].expiry_date]).not.toBe(blue[expiries[2].expiry_date])
    expect(expiries.map((group) => saturation(red[group.expiry_date])))
      .toEqual(expiries.map((group) => saturation(blue[group.expiry_date])))
    expect(buildExpiryPalette(expiries, '#888888')).toEqual(blue)
  })
})
