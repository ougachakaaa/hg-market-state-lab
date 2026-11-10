import { expect, it } from 'vitest'
import type { OptionChain } from '../api/moOptionChain'
import { optionChainContextJson, optionChainContextFilename } from './copyText'

const chain: OptionChain = {
  target_trade_date: '2026-09-17', option_product: 'MO', price_type: 'high',
  underlying: { instrument_id: '000852.SH', price: 7312.456789 },
  expiries: [
    { expiry_date: '2026-09-25', futures: { instrument_id: 'IM', price: 0 },
      calls: [{ instrument_id: 'A', strike: 7000, price: null }, { instrument_id: 'B', strike: 7000, price: 0 }],
      puts: [{ instrument_id: 'P', strike: 6900, price: -1.23456789 }] },
    { expiry_date: '2026-10-23', futures: null,
      calls: [{ instrument_id: 'C', strike: 9000, price: 2 }], puts: [] },
    { expiry_date: '2026-11-27', futures: null, calls: [], puts: [] },
  ],
}

it('serializes complete Context V1 without mutating data or losing Unicode, null or zero', () => {
  chain.expiries[0].calls[0].instrument_id = '中文 🧪 ```'
  const before = JSON.stringify(chain)
  const text = optionChainContextJson(chain)
  const context = JSON.parse(text)
  expect(Object.keys(context)).toEqual(['format_version', 'metadata', 'data'])
  expect(context.format_version).toBe('daily-data-context-v1')
  expect(context.metadata.product).toBe('MO Option Chain')
  expect(context.metadata.response_identity).toEqual({ target_trade_date: chain.target_trade_date, option_product: chain.option_product, price_type: chain.price_type, underlying_instrument_id: chain.underlying.instrument_id })
  expect(context.metadata.reading_notes.length).toBeGreaterThan(0)
  expect(context.metadata.reading_notes.every((note: unknown) => typeof note === 'string')).toBe(true)
  expect(context.data).toEqual(JSON.parse(before))
  expect(JSON.stringify(chain)).toBe(before)
  expect(text).toBe(JSON.stringify(context, null, 2))
  expect(optionChainContextFilename(chain)).toBe('mo-option-chain_2026-09-17_high_context.json')
})
