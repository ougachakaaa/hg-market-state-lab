import { protectedRequest } from '../../../shared/http/protectedRequest'
import { matchesResponse } from './validateOptionChain'
import type { OptionChain, ChainError, ChainErrorResponse } from './validateOptionChain'
import type { paths } from './moOptionChain.generated'
export type { OptionChain, ExpiryGroup, OptionPoint, ChainError, ChainErrorKind } from './validateOptionChain'

const path = '/mo-option-chain' satisfies keyof paths
type Operation = paths[typeof path]['get']
type Query = Operation['parameters']['query']

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
