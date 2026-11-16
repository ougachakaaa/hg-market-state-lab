import { describe, expect, it } from 'vitest'
import { formatPrice } from './priceDisplay'

describe('price display', () => {
  it.each([
    [7312.45, '7312.45'],
    [7312.456, '7312.46'],
    [7000, '7000.00'],
    [0, '0.00'],
    [-0, '0.00'],
    [null, '—'],
  ])('formats %s as %s', (value, expected) => {
    expect(formatPrice(value)).toBe(expected)
  })
})
