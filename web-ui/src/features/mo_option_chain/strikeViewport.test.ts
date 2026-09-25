import { describe, expect, it } from 'vitest'
import { strikeViewport } from './strikeViewport'

describe('shared strike viewport', () => {
  it.each([
    [7501, 300, [7189, 7813]],
    [7500, 300, [7188, 7812]],
    [7499.96, 300, [7187.96, 7811.96]],
  ])('centers raw spot %s within half range %s plus 2%% edge padding', (spot, range, expected) => {
    const actual = strikeViewport(spot, range)
    expect(actual[0]).toBeCloseTo(expected[0])
    expect(actual[1]).toBeCloseTo(expected[1])
    expect((actual[0] + actual[1]) / 2).toBeCloseTo(spot)
  })
})
