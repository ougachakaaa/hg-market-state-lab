import { protectedRequest } from '../../../shared/http/protectedRequest'
import Ajv2020 from 'ajv/dist/2020.js'
import openApi from './moOptionChain.openapi.json'
import type { components, paths } from './moOptionChain.generated'

const path = '/mo-option-chain' satisfies keyof paths
type Operation = paths[typeof path]['get']
type Query = Operation['parameters']['query']

// Public client types are projections of the generated HTTP contract.
export type OptionChain = Operation['responses'][200]['content']['application/json']
export type ExpiryGroup = OptionChain['expiries'][number]
export type OptionPoint = ExpiryGroup['calls'][number]
export type ChainError = components['schemas']['ChainErrorBody']
export type ChainErrorKind = ChainError['kind']
type ErrorStatus = Exclude<keyof Operation['responses'], 200>
type ChainErrorResponse = Operation['responses'][ErrorStatus]['content']['application/json']

export class ChainRequestError extends Error {
  readonly kind: ChainErrorResponse['error']['kind'] | 'network' | 'invalid_response'
  readonly param?: ChainError['param']

  constructor(
    kind: ChainErrorResponse['error']['kind'] | 'network' | 'invalid_response',
    message: string,
    param?: ChainError['param'],
  ) {
    super(message)
    this.name = 'ChainRequestError'
    this.kind = kind
    this.param = param
  }
}

// Validate against the response schemas exported by FastAPI. The front end has
// no separately maintained field rules or enum lists.
// "components" is an OpenAPI reference container, not a JSON Schema keyword.
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

export async function loadMoOptionChain(targetTradeDate: string, signal?: AbortSignal): Promise<OptionChain> {
  const parameters = {
    target_trade_date: targetTradeDate,
    option_product: 'MO',
    price_type: 'close',
  } satisfies Query
  const query = new URLSearchParams(parameters)

  let response: Response
  try {
    response = await protectedRequest(`${path}?${query}`, signal)
  } catch (error) {
    if (signal?.aborted) throw error
    throw new ChainRequestError('network', '无法连接数据服务')
  }

  let body: unknown
  try {
    body = await response.json()
  } catch (error) {
    if (signal?.aborted) throw error
    throw new ChainRequestError('invalid_response', '数据服务返回了无法读取的响应')
  }

  if (response.ok && response.status === 200 && matchesResponse(200, body)) {
    return body as OptionChain
  }
  if (!response.ok && matchesResponse(response.status, body)) {
    const { error } = body as ChainErrorResponse
    throw new ChainRequestError(error.kind, error.detail, error.param)
  }
  throw new ChainRequestError('invalid_response', '数据服务返回了不符合契约的响应')
}
