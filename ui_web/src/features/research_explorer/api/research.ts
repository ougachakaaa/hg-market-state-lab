import Ajv2020 from 'ajv/dist/2020.js'
import { protectedRequest } from '../../../shared/http/protectedRequest'
import { validateChartView, type ChartViewContract } from '../../../shared/visualization'
import openapi from './research.openapi.json'
import type { components } from './research.generated'

type Schemas = components['schemas']
export type PublicationList = Schemas['PublicationList']
export type Manifest = Schemas['Manifest']
export type Analysis = Schemas['Analysis']
export type FailureKind = Schemas['ErrorBody']['kind'] | Schemas['AuthErrorBody']['kind'] | 'network' | 'invalid_response' | 'invalid_view'
export class ResearchError extends Error {
  readonly kind: FailureKind
  constructor(kind: FailureKind) { super(kind); this.kind = kind }
}
const ajv = new Ajv2020({ strictSchema: false })
ajv.addFormat('date', /^\d{4}-\d{2}-\d{2}$/)
const validators = Object.fromEntries(Object.entries(openapi.paths).map(([path, entry]) => [path,
  Object.fromEntries(Object.entries(entry.get.responses).map(([status, response]) => [status,
    ajv.compile({ ...response.content['application/json'].schema, components: openapi.components })]))]))
type Route = keyof typeof openapi.paths
async function request<T>(route: Route, url: string, signal: AbortSignal): Promise<T> {
  let response: Response
  try { response = await protectedRequest(url, signal) } catch (e) {
    if (signal.aborted || (e instanceof DOMException && e.name === 'AbortError')) throw e
    throw new ResearchError('network')
  }
  let body: unknown
  try { body = await response.json() } catch { throw new ResearchError('invalid_response') }
  const validator = (validators[route] as Record<string, ((v: unknown) => boolean)>)[response.status]
  if (!validator?.(body)) throw new ResearchError('invalid_response')
  if (!response.ok) throw new ResearchError((body as Schemas['ErrorResponse'] | Schemas['AuthErrorResponse']).error.kind)
  return body as T
}
const base = '/research/publications'
const part = encodeURIComponent
export function listPublications(after: string | null, signal: AbortSignal) {
  return request<PublicationList>(base, after === null ? base : `${base}?${new URLSearchParams({ after })}`, signal)
}
export async function getPublication(id: string, signal: AbortSignal) {
  return (await request<Schemas['ManifestResponse']>('/research/publications/{publication_id}', `${base}/${part(id)}`, signal)).data
}
export async function getAnalysis(id: string, analysis: string, signal: AbortSignal) {
  return (await request<Schemas['AnalysisResponse']>('/research/publications/{publication_id}/analyses/{analysis_id}', `${base}/${part(id)}/analyses/${part(analysis)}`, signal)).data
}
export async function getChartView(id: string, view: string, signal: AbortSignal): Promise<ChartViewContract> {
  const data = (await request<Schemas['ViewResponse']>('/research/publications/{publication_id}/views/{view_id}', `${base}/${part(id)}/views/${part(view)}`, signal)).data
  try { validateChartView(data) } catch { throw new ResearchError('invalid_view') }
  return data
}
