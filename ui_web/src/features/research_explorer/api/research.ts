import { protectedRequest } from '../../../shared/http/protectedRequest'
import { ResearchError, type FailureKind } from '../model/failures'
import {
  matchesResponse,
  validateChartViewResponse,
  type PublicationList,
} from './validateResearch'
import type { components } from './research.generated'

export { ResearchError } from '../model/failures'
export type { FailureKind } from '../model/failures'
export type { Analysis, Manifest, PublicationList } from './validateResearch'

type Schemas = components['schemas']
type Route =
  | '/research/publications'
  | '/research/publications/{publication_id}'
  | '/research/publications/{publication_id}/analyses/{analysis_id}'
  | '/research/publications/{publication_id}/views/{view_id}'

async function request<T>(route: Route, url: string, signal: AbortSignal): Promise<T> {
  let response: Response
  try { response = await protectedRequest(url, signal) } catch (e) {
    if (signal.aborted || (e instanceof DOMException && e.name === 'AbortError')) throw e
    throw new ResearchError('network')
  }
  const badResponse: FailureKind = response.ok && route === '/research/publications/{publication_id}/views/{view_id}' ? 'invalid_view' : 'invalid_response'
  let body: unknown
  try { body = await response.json() } catch { throw new ResearchError(badResponse) }
  if (!matchesResponse(route, response.status, body)) throw new ResearchError(badResponse)
  if (!response.ok) throw new ResearchError((body as Schemas['ErrorResponse'] | Schemas['AuthErrorResponse']).error.kind)
  return body as T
}

const base = '/research/publications'
const apiBase = `/api${base}`
const part = encodeURIComponent
export function listPublications(after: string | null, signal: AbortSignal) {
  return request<PublicationList>(base, after === null ? apiBase : `${apiBase}?${new URLSearchParams({ after })}`, signal)
}
export async function getPublication(id: string, signal: AbortSignal) {
  return (await request<Schemas['ManifestResponse']>('/research/publications/{publication_id}', `${apiBase}/${part(id)}`, signal)).data
}
export async function getAnalysis(id: string, analysis: string, signal: AbortSignal) {
  return (await request<Schemas['AnalysisResponse']>('/research/publications/{publication_id}/analyses/{analysis_id}', `${apiBase}/${part(id)}/analyses/${part(analysis)}`, signal)).data
}
export async function getChartView(id: string, view: string, signal: AbortSignal) {
  const body = await request<Schemas['ViewResponse']>('/research/publications/{publication_id}/views/{view_id}', `${apiBase}/${part(id)}/views/${part(view)}`, signal)
  try { return validateChartViewResponse(body) } catch { throw new ResearchError('invalid_view') }
}
