import { describe, expect, it } from 'vitest'
import { strikeViewport } from './strikeViewport'

describe('shared strike viewport', () => {
  it.each([
    [7501, 300, [7200, 7900]],
    [7500, 300, [7200, 7800]],
    [7499.96, 300, [7100, 7800]],
  ])('uses raw spot %s and half range %s', (spot, range, expected) => {
    expect(strikeViewport(spot, range)).toEqual(expected)
  })
})
