import { protectedRequest } from '../../../shared/http/protectedRequest'
import { matchesPremiumResult, matchesResponse } from './validatePremiumPlane'
import type { PremiumPlaneResult, PremiumPriceType, PremiumError, PremiumErrorResponse } from './validatePremiumPlane'
import type { paths } from './moOptionPremium.generated'
export type { PremiumPlane, PremiumExpiry, PremiumPoint, PremiumPriceType, PremiumError, PremiumErrorKind, PremiumPlaneResult } from './validatePremiumPlane'

const path = '/mo-option-premium-plane' satisfies keyof paths
type Operation = paths[typeof path]['get']
type Query = Operation['parameters']['query']

export class PremiumRequestError extends Error {
  readonly kind: PremiumErrorResponse['error']['kind'] | 'network' | 'invalid_response'
  readonly param?: PremiumError['param']

  constructor(
    kind: PremiumErrorResponse['error']['kind'] | 'network' | 'invalid_response',
    message: string,
    param?: PremiumError['param'],
  ) {
    super(message)
    this.name = 'PremiumRequestError'
    this.kind = kind
    this.param = param
  }
}

export async function loadMoOptionPremiumPlane(
  asOf: string,
  priceType: PremiumPriceType,
  signal?: AbortSignal,
): Promise<PremiumPlaneResult> {
  const parameters = {
    as_of: asOf,
    option_product: 'MO',
    price_type: priceType,
  } satisfies Query
  const query = new URLSearchParams(parameters)

  let response: Response
  try {
    response = await protectedRequest(`${path}?${query}`, signal)
  } catch (error) {
    if (signal?.aborted) throw error
    throw new PremiumRequestError('network', '无法连接数据服务')
  }

  let body: unknown
  try {
    body = await response.json()
  } catch (error) {
    if (signal?.aborted) throw error
    throw new PremiumRequestError('invalid_response', '数据服务返回了无法读取的响应')
  }

  if (response.ok && response.status === 200 && matchesPremiumResult(body)) {
    return { plane: body, rawPayload: body }
  }
  if (!response.ok && matchesResponse(response.status, body)) {
    const { error } = body as PremiumErrorResponse
    throw new PremiumRequestError(error.kind, error.detail, error.param)
  }
  throw new PremiumRequestError('invalid_response', '数据服务返回了不符合契约的响应')
}
