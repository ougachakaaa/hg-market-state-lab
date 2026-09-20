// These types mirror GET /mo-option-chain; the backend contract owns their meaning.
export type OptionPoint = {
  instrument_id: string
  strike: number
  price: number | null
}

export type ExpiryGroup = {
  expiry_date: string
  futures: { instrument_id: string; price: number }
  calls: OptionPoint[]
  puts: OptionPoint[]
}

export type OptionChain = {
  target_trade_date: string
  option_product: 'MO'
  price_type: 'open' | 'high' | 'low' | 'close'
  underlying: { instrument_id: string; price: number }
  expiries: ExpiryGroup[]
}

export type ChainErrorKind =
  | 'invalid_request'
  | 'unsupported_query'
  | 'date_not_available'
  | 'option_chain_unavailable'
  | 'service_not_wired'

export type ChainError = {
  kind: ChainErrorKind
  detail: string
  param?: 'target_trade_date' | 'option_product' | 'price_type' | null
}

export class ChainRequestError extends Error {
  readonly kind: ChainErrorKind | 'network' | 'invalid_response'
  readonly param?: ChainError['param']

  constructor(
    kind: ChainErrorKind | 'network' | 'invalid_response',
    message: string,
    param?: ChainError['param'],
  ) {
    super(message)
    this.name = 'ChainRequestError'
    this.kind = kind
    this.param = param
  }
}

const errorKinds: readonly ChainErrorKind[] = [
  'invalid_request',
  'unsupported_query',
  'date_not_available',
  'option_chain_unavailable',
  'service_not_wired',
]

const errorParams = ['target_trade_date', 'option_product', 'price_type']
const priceTypes = ['open', 'high', 'low', 'close']

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

function isOptionPoint(value: unknown): value is OptionPoint {
  return isRecord(value)
    && typeof value.instrument_id === 'string'
    && isFiniteNumber(value.strike)
    && (value.price === null || isFiniteNumber(value.price))
}

function isExpiryGroup(value: unknown): value is ExpiryGroup {
  return isRecord(value)
    && typeof value.expiry_date === 'string'
    && isRecord(value.futures)
    && typeof value.futures.instrument_id === 'string'
    && isFiniteNumber(value.futures.price)
    && Array.isArray(value.calls)
    && value.calls.every(isOptionPoint)
    && Array.isArray(value.puts)
    && value.puts.every(isOptionPoint)
}

function isOptionChain(value: unknown): value is OptionChain {
  return isRecord(value)
    && typeof value.target_trade_date === 'string'
    && value.option_product === 'MO'
    && priceTypes.includes(value.price_type as string)
    && isRecord(value.underlying)
    && typeof value.underlying.instrument_id === 'string'
    && isFiniteNumber(value.underlying.price)
    && Array.isArray(value.expiries)
    && value.expiries.every(isExpiryGroup)
}

function parseError(value: unknown): ChainError | null {
  if (!isRecord(value) || !isRecord(value.error)) return null
  const { kind, detail, param } = value.error
  if (!errorKinds.includes(kind as ChainErrorKind) || typeof detail !== 'string') return null
  if (param !== undefined && param !== null && !errorParams.includes(param as string)) return null
  return { kind: kind as ChainErrorKind, detail, param: param as ChainError['param'] }
}

export async function loadMoOptionChain(targetTradeDate: string, signal?: AbortSignal): Promise<OptionChain> {
  const query = new URLSearchParams({
    target_trade_date: targetTradeDate,
    option_product: 'MO',
    price_type: 'close',
  })

  let response: Response
  try {
    response = await fetch(`/mo-option-chain?${query}`, { signal })
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

  if (response.ok) {
    if (isOptionChain(body)) return body
  } else {
    const chainError = parseError(body)
    if (chainError) throw new ChainRequestError(chainError.kind, chainError.detail, chainError.param)
  }
  throw new ChainRequestError('invalid_response', '数据服务返回了不符合契约的响应')
}
