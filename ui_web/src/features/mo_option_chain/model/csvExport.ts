import type { OptionChain } from '../api/validateOptionChain'
import { serializeCsv, type CsvCell } from '../../../shared/csv/csv'

export const optionChainCsvHeader = [
  'target_trade_date', 'option_product', 'price_type',
  'underlying_instrument_id', 'underlying_price', 'expiry_date',
  'futures_present', 'futures_instrument_id', 'futures_price',
  'option_type', 'instrument_id', 'strike', 'price',
] as const

export function optionChainCsv(chain: OptionChain) {
  const rows: CsvCell[][] = []
  for (const expiry of chain.expiries) {
    for (const side of ['call', 'put'] as const) {
      for (const point of side === 'call' ? expiry.calls : expiry.puts) {
        rows.push([
          chain.target_trade_date, chain.option_product, chain.price_type,
          chain.underlying.instrument_id, chain.underlying.price, expiry.expiry_date,
          expiry.futures !== null, expiry.futures?.instrument_id ?? null, expiry.futures?.price ?? null,
          side, point.instrument_id, point.strike, point.price,
        ])
      }
    }
  }
  return {
    csv: serializeCsv(optionChainCsvHeader, rows),
    filename: `mo-option-chain_${chain.target_trade_date}_${chain.price_type}.csv`,
  }
}
