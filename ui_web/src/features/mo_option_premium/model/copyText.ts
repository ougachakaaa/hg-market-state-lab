import type { PremiumPlane } from '../api/moOptionPremium'
import { serializeJson } from '../../../shared/clipboard/text'

export function premiumPlaneContextJson(plane: PremiumPlane, rawPayload: unknown): string {
  return serializeJson({
    format_version: 'daily-data-context-v1',
    metadata: {
      product: 'MO Premium Plane',
      response_identity: {
        observation: { kind: plane.observation.kind, value: plane.observation.value },
        option_product: plane.option_product,
        price_type: plane.price_type,
        underlying_instrument_id: plane.underlying.instrument_id,
      },
      reading_notes: [
        'The plane contains sparse Points. An absent Point is no analytical observation; a null metric is an unavailable fact in a real Point; numeric zero is a valid value. These states differ.',
        'futures: null means no eligible same-expiry futures reference exists; no substitute reference is implied.',
      ],
    },
    data: rawPayload,
  })
}

export function premiumPlaneContextFilename(plane: PremiumPlane): string {
  return `mo-premium-plane_${plane.observation.value}_${plane.price_type}_context.json`
}
