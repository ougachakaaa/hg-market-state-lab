import type { PremiumPlane } from '../api/moOptionPremium'
import { jsonFence, serializeJson } from '../../../shared/clipboard/text'

export function premiumPlaneForGpt(plane: PremiumPlane, rawPayload: unknown): string {
  return [
    '# MO Premium Plane',
    `- observation.kind: ${plane.observation.kind}\n- observation.value: ${plane.observation.value}\n- option_product: ${plane.option_product}\n- price_type: ${plane.price_type}\n- underlying.instrument_id: ${plane.underlying.instrument_id}`,
    'The plane contains sparse Points. An absent Point is no analytical observation; a null metric is an unavailable fact in a real Point; numeric zero is a valid value. These states differ. futures: null means no eligible same-expiry futures reference exists; no substitute reference is implied.',
    jsonFence(serializeJson(rawPayload)),
  ].join('\n\n')
}
