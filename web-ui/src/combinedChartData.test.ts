import { describe, expect, it } from 'vitest'
import type { OptionChain } from './api/moOptionChain'
import { missingPriceCount, projectCombinedChain } from './combinedChartData'

const chain: OptionChain = {
  target_trade_date: '2026-09-17', option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', futures: { instrument_id: 'IM2609.CFE', price: 9000 },
      calls: [{ instrument_id: 'A1', strike: 7100, price: 200 }, { instrument_id: 'A2', strike: 8000, price: 2000 }],
      puts: [{ instrument_id: 'A3', strike: 7200, price: 0 }, { instrument_id: 'A4', strike: 7300, price: null }] },
    { expiry_date: '2026-10-23', futures: null,
      calls: [{ instrument_id: 'B1', strike: 7100, price: 450 }],
      puts: [{ instrument_id: 'B2', strike: 7200, price: -5 }] },
  ],
}

describe('combined chart projection', () => {
  it('calculates one Y-domain from selected prices inside the shared viewport', () => {
    const both = projectCombinedChain(chain, new Set(['2026-09-25', '2026-10-23']), [7000, 7700])
    expect(both.yDomain).toEqual([-17, 600])
    expect(both.groups).toEqual(chain.expiries)
    const first = projectCombinedChain(chain, new Set(['2026-09-25']), [7000, 7700])
    expect(first.yDomain).toEqual([-6, 300])
    expect(first.groups).toEqual([chain.expiries[0]])
    expect(missingPriceCount(chain.expiries[0])).toBe(1)
    expect(first.hasDrawablePrice).toBe(true)
  })

  it('retains a usable zero-inclusive domain if every selected price is null', () => {
    const empty: OptionChain = { ...chain, expiries: [{ ...chain.expiries[0], calls: [{ instrument_id: 'C', strike: 7200, price: null }], puts: [] }] }
    const result = projectCombinedChain(empty, new Set(['2026-09-25']), [7000, 7700])
    expect(result.yDomain).toEqual([-2, 100])
    expect(result.hasDrawablePrice).toBe(false)
    expect(missingPriceCount(result.groups[0])).toBe(1)
  })
})
