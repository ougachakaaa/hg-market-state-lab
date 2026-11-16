import { protectedRequest } from '../../../shared/http/protectedRequest'
import { matchesResponse, validateResult, type Query, type Result, type ErrorResult } from './validateResult'
export class QueryError extends Error {
  readonly kind: string
  readonly param: string | null
  constructor(kind: string, param: string | null = null) { super(kind); this.kind = kind; this.param = param }
}
const errors: Record<number, string[]> = {
  400: ['invalid_request'], 403: ['origin_forbidden'], 409: ['incomplete_inputs'],
  413: ['request_too_large', 'response_too_large'],
  422: ['slot_resolution_error', 'calculation_failure', 'statistical_failure'],
  502: ['input_contract_error'], 503: ['upstream_unavailable', 'transport_busy'], 500: ['internal_error'],
}
export async function loadQuery(query: Query, signal: AbortSignal): Promise<Result> {
  let response: Response
  try { response = await protectedRequest(`/api/data/futures-calendar-spread?${new URLSearchParams({ product_code: query.product_code, trade_date: query.trade_date })}`, signal) }
  catch (e) { if (signal.aborted || (e instanceof DOMException && e.name === 'AbortError')) throw e; throw new QueryError('network') }
  if (response.status === 401) throw new DOMException('Authentication required', 'AbortError')
  let body: unknown
  try { body = await response.json() } catch { throw new QueryError('invalid_response') }
  if (signal.aborted) throw new DOMException('Cancelled', 'AbortError')
  if (!matchesResponse(response.status, body)) throw new QueryError('invalid_response')
  if (response.status !== 200) {
    const error = (body as ErrorResult).error
    if (!errors[response.status]?.includes(error.kind)) throw new QueryError('invalid_response')
    throw new QueryError(error.kind, error.param ?? null)
  }
  try { return validateResult(body, query) } catch { throw new QueryError('invalid_response') }
}
