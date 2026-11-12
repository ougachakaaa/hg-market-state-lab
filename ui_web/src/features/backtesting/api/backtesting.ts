import { protectedRequest } from '../../../shared/http/protectedRequest'
import { CASE_ID, matchesResponse, validateResultResponse, validateRunState } from './validateResult'
import type { Accepted, Preflight, ResultResponse, Run, RunRequest } from './validateResult'

export type {
  Accepted,
  BacktestResult,
  ImmutableRequest,
  Preflight,
  ResultResponse,
  Run,
  RunRequest,
} from './validateResult'
export { products, sameRequest, strategies } from './validateResult'

export class BacktestingError extends Error {
  readonly kind: string
  readonly detail: string
  readonly param: string | null
  constructor(kind: string, detail = '', param: string | null = null) { super(kind); this.kind = kind; this.detail = detail; this.param = param }
}
const base = '/backtesting/futures-roll/runs'
const routes = [base, `${base}/{run_id}`, `${base}/{run_id}/result`, '/backtesting/futures-roll/preflight'] as const
const kinds: Record<string, Record<number, string[]>> = {
  preflight: { 400: ['invalid_request', 'request_too_large'], 403: ['origin_forbidden'], 500: ['internal_error'], 503: ['unavailable'] },
  post: { 400: ['invalid_request', 'request_too_large'], 403: ['origin_forbidden'], 409: ['run_busy'], 500: ['internal_error'], 503: ['unavailable'] },
  status: { 400: ['invalid_request'], 404: ['run_not_found'], 409: ['corrupt'], 500: ['internal_error'], 503: ['unavailable'] },
  result: { 400: ['invalid_request'], 404: ['run_not_found'], 409: ['result_not_ready', 'corrupt'], 413: ['result_too_large', 'response_too_large'], 500: ['internal_error'], 503: ['unavailable', 'read_busy'] },
}
async function request<T>(index: number, id: string | undefined, signal: AbortSignal, body?: RunRequest): Promise<T> {
  const method = body ? 'post' : 'get'
  const path = routes[index]
  const url = `/api${path.replace('{run_id}', encodeURIComponent(id ?? ''))}`
  let response: Response
  try { response = await protectedRequest(url, signal, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : undefined) }
  catch (error) { if (signal.aborted || (error instanceof DOMException && error.name === 'AbortError')) throw error; throw new BacktestingError('network') }
  if (response.status === 401) throw new DOMException('Authentication required', 'AbortError')
  let value: any
  try { value = await response.json() } catch { throw new BacktestingError('invalid_response') }
  if (!matchesResponse(method, path, response.status, value)) throw new BacktestingError('invalid_response')
  if (!response.ok) {
    if (!kinds[index === 0 ? 'post' : index === 1 ? 'status' : index === 2 ? 'result' : 'preflight'][response.status]?.includes(value.error.kind)) throw new BacktestingError('invalid_response')
    throw new BacktestingError(value.error.kind, value.error.detail ?? '', value.error.param ?? null)
  }
  if (response.status !== (index === 0 ? 202 : 200) || (id !== undefined && value.run_id !== id)) throw new BacktestingError('invalid_response')
  if ((index === 0 || index === 3) && (['case', 'product_code', 'start_date', 'end_date', 'strategy_profile'] as const).some(k => value.request[k] !== (k === 'case' ? CASE_ID : body?.[k]))) throw new BacktestingError('invalid_response')
  if (index === 1) {
    try { validateRunState(value) } catch { throw new BacktestingError('invalid_response') }
  }
  if (index === 2) {
    try { validateResultResponse(value) } catch { throw new BacktestingError('invalid_response') }
  }
  return value as T
}
export const submitRun = (body: RunRequest, signal: AbortSignal) => request<Accepted>(0, undefined, signal, body)
export const getRun = (id: string, signal: AbortSignal) => request<Run>(1, id, signal)
export const getResult = (id: string, signal: AbortSignal) => request<ResultResponse>(2, id, signal)

export const checkInputs = (body: RunRequest, signal: AbortSignal) => request<Preflight>(3, undefined, signal, body)
