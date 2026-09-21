import { describe, expect, it } from 'vitest'
import type { ExpiryGroup } from './api/moOptionChain'
import { buildExpiryPalette, DEFAULT_SERIES_COLORS } from './expiryPalette'

const expiries = ['2026-09-25', '2026-10-23', '2026-11-27', '2026-12-25']
  .map((expiry_date) => ({ expiry_date, futures: null, calls: [], puts: [] })) satisfies ExpiryGroup[]

describe('expiry opacity palette', () => {
  it('uses full ascending response rank with exact endpoints and linear middle values', () => {
    const palette = buildExpiryPalette([...expiries].reverse(), DEFAULT_SERIES_COLORS)
    const values = expiries.map((group) => palette[group.expiry_date].opacity)
    expect(values[0]).toBe(1)
    expect(values[1]).toBeCloseTo(1 - 0.85 / 3)
    expect(values[2]).toBeCloseTo(1 - 2 * 0.85 / 3)
    expect(values[3]).toBe(0.15)
    expect(buildExpiryPalette(expiries, DEFAULT_SERIES_COLORS)[expiries[2].expiry_date])
      .toEqual(palette[expiries[2].expiry_date])
  })

  it('uses full opacity for a single expiry and one opacity for all three elements', () => {
    const value = buildExpiryPalette([expiries[0]], DEFAULT_SERIES_COLORS)[expiries[0].expiry_date]
    expect(value.opacity).toBe(1)
    expect(value.call).toBe('rgba(37, 99, 235, 1)')
    expect(value.put).toBe('rgba(234, 88, 12, 1)')
    expect(value.futures).toBe('rgba(124, 58, 237, 1)')
  })

  it('changes only the selected element color and retains every expiry opacity', () => {
    const before = buildExpiryPalette(expiries, DEFAULT_SERIES_COLORS)
    const after = buildExpiryPalette(expiries, { ...DEFAULT_SERIES_COLORS, put: '#00ff00' })
    for (const group of expiries) {
      const date = group.expiry_date
      expect(after[date].opacity).toBe(before[date].opacity)
      expect(after[date].call).toBe(before[date].call)
      expect(after[date].futures).toBe(before[date].futures)
      expect(after[date].put).not.toBe(before[date].put)
      expect(after[date].put).toBe(`rgba(0, 255, 0, ${after[date].opacity})`)
    }
  })
})
