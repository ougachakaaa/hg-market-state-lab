import { describe, expect, it } from 'vitest'
import { formatPrice } from './priceDisplay'

describe('price display', () => {
  it.each([
    [7312.45, '7312.5'],
    [7000, '7000.0'],
    [0, '0.0'],
    [null, '—'],
  ])('formats %s as %s', (value, expected) => {
    expect(formatPrice(value)).toBe(expected)
  })
})
