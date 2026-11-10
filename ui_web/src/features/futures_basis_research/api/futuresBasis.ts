import Ajv2020 from 'ajv/dist/2020.js'
import { protectedRequest } from '../../../shared/http/protectedRequest'
import { validateReportData } from '../report/validate'
import type { ReportData } from '../report/types'
import type { components } from './futuresBasis.generated'
import openapi from './futuresBasis.openapi.json'

export type Preflight = components['schemas']['FuturesBasisPreflightResponse']
export type RunRequest = components['schemas']['FuturesBasisRunRequest']
export type Run = components['schemas']['FuturesBasisRun']
export type Accepted = components['schemas']['FuturesBasisRunAccepted']
export type ReportResponse = Omit<components['schemas']['FuturesBasisReportResponse'], 'data'> & { data: ReportData }
export const products = openapi.components.schemas.FuturesBasisRunRequest.properties.product_code.enum
export class ResearchError extends Error {
  readonly kind: string
  readonly detail: string
  readonly param: string | null
  constructor(kind: string, detail = '', param: string | null = null) { super(kind); this.kind = kind; this.detail = detail; this.param = param }
}
const ajv = new Ajv2020({ strictSchema: false, strictTypes: false, formats: {
  date: (value: string) => /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value,
  'date-time': (value: string) => /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value)),
} })
const base = '/research/futures-basis/runs'
const routes = [base, `${base}/{run_id}`, `${base}/{run_id}/report`, '/research/futures-basis/preflight'] as const
const validators = new Map<string, ReturnType<typeof ajv.compile>>()
for (const [path, operations] of Object.entries(openapi.paths)) {
  for (const [method, operation] of Object.entries(operations)) {
    for (const [status, response] of Object.entries(operation.responses)) {
      validators.set(`${method} ${path} ${status}`, ajv.compile({ ...(response as { content: { 'application/json': { schema: object } } }).content['application/json'].schema, components: openapi.components }))
    }
  }
}
const kinds: Record<string, Record<number, string[]>> = {
  preflight: { 400: ['invalid_request', 'request_too_large'], 403: ['origin_forbidden'], 500: ['internal_error'] },
  post: { 400: ['invalid_request', 'request_too_large'], 403: ['origin_forbidden'], 409: ['run_busy'], 500: ['internal_error'], 503: ['unavailable'] },
  status: { 400: ['invalid_request'], 404: ['run_not_found'], 409: ['corrupt', 'unsupported_version'], 500: ['internal_error'], 503: ['unavailable'] },
  report: { 400: ['invalid_request'], 404: ['run_not_found'], 409: ['result_not_ready', 'result_unavailable', 'corrupt', 'unsupported_version'], 413: ['response_too_large'], 500: ['internal_error'], 503: ['unavailable', 'read_busy'] },
}
async function request<T>(index: number, id: string | undefined, signal: AbortSignal, body?: RunRequest): Promise<T> {
  const method = body ? 'post' : 'get'
  const path = routes[index]
  const url = `/api${path.replace('{run_id}', encodeURIComponent(id ?? ''))}`
  let response: Response
  try { response = await protectedRequest(url, signal, body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : undefined) }
  catch (error) { if (signal.aborted || (error instanceof DOMException && error.name === 'AbortError')) throw error; throw new ResearchError('network') }
  if (response.status === 401) throw new DOMException('Authentication required', 'AbortError')
  let value: any
  try { value = await response.json() } catch { throw new ResearchError('invalid_response') }
  if (!validators.get(`${method} ${path} ${response.status}`)?.(value)) throw new ResearchError('invalid_response')
  if (!response.ok) {
    if (!kinds[index === 0 ? 'post' : index === 1 ? 'status' : index === 2 ? 'report' : 'preflight'][response.status]?.includes(value.error.kind)) throw new ResearchError('invalid_response')
    throw new ResearchError(value.error.kind, value.error.detail ?? '', value.error.param ?? null)
  }
  if (response.status !== (index === 0 ? 202 : 200) || (id !== undefined && value.run_id !== id)) throw new ResearchError('invalid_response')
  if ((index === 0 || index === 3) && (['product_code', 'start_date', 'end_date'] as const).some(k => value.request[k] !== body?.[k])) throw new ResearchError('invalid_response')
  if (index === 1) {
    const complete = value.status === 'COMPLETED'; const failed = ['FAILED', 'INTERRUPTED'].includes(value.status)
    if ((value.status === 'PENDING' && value.started_at !== null) || (['PENDING', 'RUNNING'].includes(value.status) ? value.finished_at !== null : value.finished_at === null)) throw new ResearchError('invalid_response')
    if (value.result_available !== complete || (complete ? !['complete', 'partial'].includes(value.result_status) : value.result_status !== null) || (failed ? !value.failure : value.failure !== null)) throw new ResearchError('invalid_response')
  }
  if (index === 2) {
    try {
      validateReportData(value.data)
      const obs = value.data.request.observation
      if (value.data.status !== value.result_status || ['product_code', 'start_date', 'end_date'].some(k => obs[k] !== value.request[k])) throw new Error('Association mismatch')
    } catch { throw new ResearchError('invalid_response') }
  }
  return value as T
}
export const submitRun = (body: RunRequest, signal: AbortSignal) => request<Accepted>(0, undefined, signal, body)
export const getRun = (id: string, signal: AbortSignal) => request<Run>(1, id, signal)
export const getReport = (id: string, signal: AbortSignal) => request<ReportResponse>(2, id, signal)

export const checkInputs = (body: RunRequest, signal: AbortSignal) => request<Preflight>(3, undefined, signal, body)
