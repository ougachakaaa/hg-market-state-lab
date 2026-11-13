import Ajv2020 from 'ajv/dist/2020.js'
import openapi from './futuresBasis.openapi.json'
import { validateReportData } from '../report/validate'
import type { ReportData } from '../report/types'
import type { components } from './futuresBasis.generated'

// Transport-free validation of the published Futures Basis wire contract. Production
// transport and static Embedded Report composition both consume these functions; neither
// owns a second DTO or a second reader schema.
type Schemas = components['schemas']
export type Preflight = Schemas['FuturesBasisPreflightResponse']
export type RunRequest = Schemas['FuturesBasisRunRequest']
export type Run = Schemas['FuturesBasisRun']
export type Accepted = Schemas['FuturesBasisRunAccepted']
export type ImmutableRequest = Schemas['FuturesBasisImmutableRequest']
export type ReportResponse = Omit<Schemas['FuturesBasisReportResponse'], 'data'> & { data: ReportData }
export const products = openapi.components.schemas.FuturesBasisRunRequest.properties.product_code.enum
export const REPORT_PROFILE = 'futures_basis_report_evidence_v1'

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
const immutableRequest = ajv.compile({ ...openapi.components.schemas.FuturesBasisImmutableRequest, components: openapi.components })

/** Generated-schema check for one committed HTTP response body. Transport keeps error mapping. */
export function matchesResponse(method: string, path: string, status: number, body: unknown): boolean {
  return validators.get(`${method} ${path} ${status}`)?.(body) === true
}

/** The immutable request identity a Run (or a fixed static Example) answers. */
export function validateImmutableRequest(value: unknown): ImmutableRequest {
  if (!immutableRequest(value)) throw new Error('Invalid Futures Basis immutable request')
  return value as ImmutableRequest
}

/**
 * Shared producer-reader boundary. `validateReportData` owns the reader profile, status,
 * definition and Visualization validation; this adds the Fixed Request / Observation
 * association and the optional Report Status agreement with an HTTP envelope. No financial
 * value is recomputed and the payload is returned unchanged.
 */
export function validateReaderReport(value: unknown, request: ImmutableRequest, resultStatus?: 'complete' | 'partial'): ReportData {
  validateReportData(value)
  const data = value
  if (!data.definition_version.trim()) throw new Error('Missing Futures Basis definition version')
  const observed = data.request.observation
  if (observed.case !== request.case) throw new Error('Futures Basis report case does not match its request')
  if (['product_code', 'start_date', 'end_date'].some(key => observed[key] !== request[key])) {
    throw new Error('Futures Basis report observation does not match its request')
  }
  if (resultStatus !== undefined && data.status !== resultStatus) {
    throw new Error('Futures Basis report status does not match its Run')
  }
  return data
}

export interface EmbeddedReportPayload {
  /** Fixed immutable request identity of the committed Example. */
  request: unknown
  /** Complete producer reader payload (`futures_basis_report_evidence_v1`). */
  report: unknown
}

export interface ValidatedEmbeddedReport {
  request: ImmutableRequest
  report: ReportData
}

/**
 * Static composition validates the fixed request and the complete producer reader payload
 * directly. It deliberately accepts no HTTP Run envelope: the browser did not receive or
 * complete a server Run.
 */
export function validateEmbeddedReport(payload: EmbeddedReportPayload): ValidatedEmbeddedReport {
  if (typeof payload !== 'object' || payload === null) throw new Error('Invalid embedded report payload')
  const request = validateImmutableRequest(payload.request)
  const report = validateReaderReport(payload.report, request)
  return { request, report }
}
