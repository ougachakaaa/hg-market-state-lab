import Ajv2020 from 'ajv/dist/2020.js'
import { validateViewV2 } from '../../../shared/visualization/contractV2'
import type { components } from './backtesting.generated'
import openapi from './backtesting.openapi.json'

// Transport-free validation of the published Futures Roll Long wire contract.
// Production transport and static Embedded Result composition consume the same functions;
// neither owns a second Result DTO or recomputes a W2 financial value.
type Schemas = components['schemas']
export type Preflight = Schemas['FuturesRollPreflight']
export type RunRequest = Schemas['FuturesRollRunRequest']
export type ImmutableRequest = Schemas['FuturesRollImmutableRequest']
export type Run = Schemas['FuturesRollRun']
export type Accepted = Schemas['FuturesRollRunAccepted']
export type ResultResponse = Schemas['FuturesRollResultResponse']
export type BacktestResult = ResultResponse['data']

export const products = openapi.components.schemas.FuturesRollRunRequest.properties.product_code.enum
export const strategies = openapi.components.schemas.FuturesRollRunRequest.properties.strategy_profile.enum
export const CASE_ID = 'futures_roll_long_v1' as const
export const RESULT_PROFILE = 'futures_roll_long_result_v1' as const
export const DEFINITION_VERSION = 'futures_roll_long_definition_v1' as const
const RESULT_PATH = '/backtesting/futures-roll/runs/{run_id}/result'

const ajv = new Ajv2020({ strictSchema: false, strictTypes: false, formats: {
  date: (value: string) => /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value,
  'date-time': (value: string) => /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value)),
} })
const validators = new Map<string, ReturnType<typeof ajv.compile>>()
for (const [path, operations] of Object.entries(openapi.paths)) {
  for (const [method, operation] of Object.entries(operations)) {
    for (const [status, response] of Object.entries(operation.responses)) {
      validators.set(`${method} ${path} ${status}`, ajv.compile({
        ...(response as { content: { 'application/json': { schema: object } } }).content['application/json'].schema,
        components: openapi.components,
      }))
    }
  }
}
const immutableRequest = ajv.compile({ ...openapi.components.schemas.FuturesRollImmutableRequest, components: openapi.components })
const result = ajv.compile({ ...openapi.components.schemas.FuturesRollResult, components: openapi.components })

/** Generated-schema check for one committed HTTP response body. Transport keeps error mapping. */
export function matchesResponse(method: string, path: string, status: number, body: unknown): boolean {
  return validators.get(`${method} ${path} ${status}`)?.(body) === true
}

/** The immutable request identity a Run (or a fixed static Example) answers. */
export function validateImmutableRequest(value: unknown): ImmutableRequest {
  if (!immutableRequest(value)) throw new Error('Invalid Futures Roll immutable request')
  return value as ImmutableRequest
}

/** The five-field structural identity used by the published request contract. */
export function sameRequest(a: ImmutableRequest, b: ImmutableRequest) {
  return (['case', 'product_code', 'start_date', 'end_date', 'strategy_profile'] as const).every(key => a[key] === b[key])
}

/** Generated Status shape plus the cross-field lifecycle coherence required by the contract. */
export function validateRunState(value: Run): Run {
  const complete = value.status === 'COMPLETED'
  const failed = value.status === 'FAILED' || value.status === 'INTERRUPTED'
  if ((value.status === 'RUNNING' && value.started_at === null) || (value.status === 'PENDING' && value.started_at !== null) || (['PENDING', 'RUNNING'].includes(value.status) ? value.finished_at !== null : value.finished_at === null)) {
    throw new Error('Invalid Futures Roll Run timestamps')
  }
  if (value.result_available !== complete || (failed ? !value.failure : value.failure !== null)) {
    throw new Error('Invalid Futures Roll Run lifecycle')
  }
  return value
}

/**
 * Shared producer-result boundary. The generated Result schema owns the complete payload,
 * while this function adds the published profile/definition/case identity, the optional
 * Fixed Request association and both V2 Views. The Result is returned unchanged.
 */
export function validateResult(value: unknown, request?: ImmutableRequest): BacktestResult {
  if (!result(value)) throw new Error('Invalid Futures Roll Result')
  const data = value as BacktestResult
  if (data.profile !== RESULT_PROFILE) throw new Error('Unsupported Futures Roll Result profile')
  if (data.definition_version !== DEFINITION_VERSION) throw new Error('Unsupported Futures Roll definition version')
  if (data.case !== CASE_ID) throw new Error('Unsupported Futures Roll case')
  if (data.status !== 'complete') throw new Error('Unsupported Futures Roll Result status')
  validateImmutableRequest(data.request)
  if (request !== undefined && !sameRequest(request, data.request)) throw new Error('Futures Roll Result does not match its request')
  try {
    validateViewV2(data.views.returns)
    validateViewV2(data.views.drawdown)
  } catch {
    throw new Error('Invalid Futures Roll V2 view')
  }
  return data
}

/** Production Result envelope: generated HTTP response, internal association and V2 Views. */
export function validateResultResponse(value: unknown): ResultResponse {
  if (!matchesResponse('get', RESULT_PATH, 200, value)) throw new Error('Invalid Futures Roll Result response')
  const response = value as ResultResponse
  validateResult(response.data, response.request)
  return response
}

export interface EmbeddedBacktestResultPayload {
  /** Fixed immutable request identity of the committed Example. */
  request: unknown
  /** Complete producer BacktestResult (`futures_roll_long_result_v1`). */
  result: unknown
}

export interface ValidatedEmbeddedBacktestResult {
  request: ImmutableRequest
  result: BacktestResult
}

/**
 * Static composition validates the fixed request and complete producer Result directly.
 * It deliberately accepts no HTTP Run envelope: the browser did not receive or complete a
 * server Run, so no Run ID is required or fabricated.
 */
export function validateEmbeddedBacktestResult(payload: EmbeddedBacktestResultPayload): ValidatedEmbeddedBacktestResult {
  if (typeof payload !== 'object' || payload === null) throw new Error('Invalid embedded Backtest Result payload')
  const request = validateImmutableRequest(payload.request)
  const result = validateResult(payload.result, request)
  return { request, result }
}
