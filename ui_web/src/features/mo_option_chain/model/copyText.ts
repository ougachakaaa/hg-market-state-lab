import type { OptionChain } from '../api/moOptionChain'
import { jsonFence, serializeJson } from '../../../shared/clipboard/text'

export function optionChainForGpt(chain: OptionChain): string {
  return [
    '# MO Option Chain',
    `- target_trade_date: ${chain.target_trade_date}\n- option_product: ${chain.option_product}\n- price_type: ${chain.price_type}\n- underlying.instrument_id: ${chain.underlying.instrument_id}`,
    'A null price means the price is unavailable; numeric zero is a valid price. futures: null means no structurally matching same-expiry IM contract exists; no substitute reference is implied. Contracts retain their parent expiry and Call/Put grouping.',
    jsonFence(serializeJson(chain)),
  ].join('\n\n')
}
