// Regression test data only; not an official synthetic Example.
import type { OptionChain } from '../api/validateOptionChain'

export const chain: OptionChain = {
  target_trade_date: '2026-09-17', option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
      calls: [{ instrument_id: 'A-call', strike: 7200, price: 200 }, { instrument_id: 'A-out', strike: 8000, price: 2000 }],
      puts: [{ instrument_id: 'A-zero', strike: 7100, price: 0 }, { instrument_id: 'A-null', strike: 7300, price: null }] },
    { expiry_date: '2026-10-23', futures: { instrument_id: 'IM2610.CFE', price: 7560.25 },
      calls: [{ instrument_id: 'B-call', strike: 7200, price: 450 }],
      puts: [{ instrument_id: 'B-put', strike: 7300, price: 10 }] },
    { expiry_date: '2026-11-27', futures: null,
      calls: [{ instrument_id: 'C-call', strike: 7200, price: 50 }],
      puts: [{ instrument_id: 'C-put', strike: 7300, price: 5 }] },
  ],
}
