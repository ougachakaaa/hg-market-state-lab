import Ajv2020 from 'ajv/dist/2020.js'
import openApi from './moOptionPremium.openapi.json'
import type { components, paths } from './moOptionPremium.generated'

const path = '/mo-option-premium-plane' satisfies keyof paths
type Operation = paths[typeof path]['get']
type Query = Operation['parameters']['query']

export type PremiumPlane = Operation['responses'][200]['content']['application/json']
export type PremiumExpiry = PremiumPlane['expiries'][number]
export type PremiumPoint = PremiumPlane['points'][number]
export type PremiumPriceType = NonNullable<Query['price_type']>
export type PremiumError = components['schemas']['PremiumErrorBody']
export type PremiumErrorKind = PremiumError['kind']
export interface PremiumPlaneResult {
  plane: PremiumPlane
  rawPayload: unknown
}
type ErrorStatus = Exclude<keyof Operation['responses'], 200>
type PremiumErrorResponse = Operation['responses'][ErrorStatus]['content']['application/json']

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

const ajv = new Ajv2020({ strictSchema: false })
const responseValidators = new Map(
  Object.entries(openApi.paths[path].get.responses).map(([status, response]) => [
    Number(status),
    ajv.compile({
      ...response.content['application/json'].schema,
      components: openApi.components,
    }),
  ]),
)

function matchesResponse(status: number, body: unknown): boolean {
  return responseValidators.get(status)?.(body) === true
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
    response = await fetch(`${path}?${query}`, { signal })
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

  if (response.ok && response.status === 200 && matchesResponse(200, body)) {
    return { plane: body as PremiumPlane, rawPayload: body }
  }
  if (!response.ok && matchesResponse(response.status, body)) {
    const { error } = body as PremiumErrorResponse
    throw new PremiumRequestError(error.kind, error.detail, error.param)
  }
  throw new PremiumRequestError('invalid_response', '数据服务返回了不符合契约的响应')
}
