import { describe, expect, it } from 'vitest'
import { projectExpiry } from './expiryChartData'

describe('expiry chart projection', () => {
  it('retains numeric zero and excludes null from drawable points', () => {
    const result = projectExpiry({
      expiry_date: '2026-09-25',
      futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
      calls: [{ instrument_id: 'C1', strike: 7000, price: null }],
      puts: [{ instrument_id: 'P1', strike: 7100, price: 0 }],
    })
    expect(result.calls).toEqual([])
    expect(result.puts).toEqual([{ instrument_id: 'P1', strike: 7100, price: 0, side: 'Put' }])
    expect(result.missingPriceCount).toBe(1)
    expect(result).not.toHaveProperty('xDomain')
    expect(result.yDomain[0]).toBeLessThan(0)
    expect(result.yDomain[1]).toBeGreaterThan(0)
  })

  it('returns a usable domain when all strikes and prices are identical', () => {
    const result = projectExpiry({
      expiry_date: '2026-09-25',
      futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
      calls: [{ instrument_id: 'C1', strike: 7000, price: 0 }],
      puts: [],
    })
    expect(result.yDomain[0]).toBeLessThan(0)
    expect(result.yDomain[1]).toBeGreaterThan(0)
  })
})
