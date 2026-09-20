import { describe, expect, it } from 'vitest'
import { projectExpiry } from './expiryChartData'

describe('expiry chart projection', () => {
  it('retains numeric zero and excludes null from drawable points', () => {
    const result = projectExpiry({
      expiry_date: '2026-09-25',
      futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
      calls: [{ instrument_id: 'C1', strike: 7000, price: null }],
      puts: [{ instrument_id: 'P1', strike: 7100, price: 0 }],
    }, [7000, 7700])
    expect(result.calls).toEqual([])
    expect(result.puts).toEqual([{ instrument_id: 'P1', strike: 7100, price: 0, side: 'Put' }])
    expect(result.missingPriceCount).toBe(1)
    expect(result).not.toHaveProperty('xDomain')
    expect(result.yDomain).toEqual([-2, 100])
  })

  it('returns a usable domain when all strikes and prices are identical', () => {
    const result = projectExpiry({
      expiry_date: '2026-09-25',
      futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
      calls: [{ instrument_id: 'C1', strike: 7000, price: 0 }],
      puts: [],
    }, [7000, 7700])
    expect(result.yDomain).toEqual([-2, 100])
  })

  it('uses only points in the plotted range and rounds 120% of the maximum up to 100', () => {
    const group = {
      expiry_date: '2026-09-25', futures: null,
      calls: [
        { instrument_id: 'C-left', strike: 6999, price: 2000 },
        { instrument_id: 'C-edge', strike: 7001, price: 151 },
        { instrument_id: 'C-far', strike: 7600, price: 800 },
      ],
      puts: [{ instrument_id: 'P-low', strike: 7100, price: -5 }],
    }

    expect(projectExpiry(group, [7000, 7300]).yDomain).toEqual([-9, 200])
    expect(projectExpiry(group, [7000, 7700]).yDomain).toEqual([-25, 1000])
    expect(projectExpiry(group, [7200, 7300]).yDomain).toEqual([-2, 100])
  })
})
