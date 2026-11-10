import type { OptionChain } from '../api/moOptionChain'
import { serializeJson } from '../../../shared/clipboard/text'

export function optionChainContextJson(chain: OptionChain): string {
  return serializeJson({
    format_version: 'daily-data-context-v1',
    metadata: {
      product: 'MO Option Chain',
      response_identity: {
        target_trade_date: chain.target_trade_date,
        option_product: chain.option_product,
        price_type: chain.price_type,
        underlying_instrument_id: chain.underlying.instrument_id,
      },
      reading_notes: [
        'A null price means the price is unavailable; numeric zero is a valid price.',
        'futures: null means no structurally matching same-expiry IM contract exists; no substitute reference is implied.',
        'Contracts retain their parent expiry and Call/Put grouping.',
      ],
    },
    data: chain,
  })
}

export function optionChainContextFilename(chain: OptionChain): string {
  return `mo-option-chain_${chain.target_trade_date}_${chain.price_type}_context.json`
}
