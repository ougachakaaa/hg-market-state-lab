import { expect, it } from 'vitest'
import type { OptionChain } from '../api/moOptionChain'
import { optionChainCsv } from './csvExport'

it('maps all real contracts in backend order with exact context and null/zero facts', () => {
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
  const { csv, filename } = optionChainCsv(chain)
  expect(filename).toBe('mo-option-chain_2026-09-17_high.csv')
  expect(csv).toBe('\uFEFFtarget_trade_date,option_product,price_type,underlying_instrument_id,underlying_price,expiry_date,futures_present,futures_instrument_id,futures_price,option_type,instrument_id,strike,price\r\n' +
    '2026-09-17,MO,high,000852.SH,7312.456789,2026-09-25,true,IM,0,call,A,7000,null\r\n' +
    '2026-09-17,MO,high,000852.SH,7312.456789,2026-09-25,true,IM,0,call,B,7000,0\r\n' +
    '2026-09-17,MO,high,000852.SH,7312.456789,2026-09-25,true,IM,0,put,P,6900,-1.23456789\r\n' +
    '2026-09-17,MO,high,000852.SH,7312.456789,2026-10-23,false,null,null,call,C,9000,2\r\n')
  expect(csv.split('\r\n').length - 2).toBe(chain.expiries.reduce((n, e) => n + e.calls.length + e.puts.length, 0))
  for (const expiries of [[], [chain.expiries[2]]]) {
    expect(optionChainCsv({ ...chain, expiries }).csv).toBe(csv.split('\r\n')[0] + '\r\n')
  }
})
