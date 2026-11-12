import { protectedRequest } from '../../../shared/http/protectedRequest'
import { matchesResponse, type Capability } from './validateCatalog'

export type { Capability } from './validateCatalog'
export type CatalogFailure = 'network' | 'invalid_response' | 'unavailable' | 'not_found'

export class CatalogError extends Error {
  readonly kind: CatalogFailure
  constructor(kind: CatalogFailure) { super(kind); this.kind = kind }
}

type Route = '/research/capabilities' | '/research/capabilities/{id}'

async function request<T>(route: Route, url: string, signal: AbortSignal): Promise<T> {
  let response: Response
  try { response = await protectedRequest(url, signal) } catch (error) {
    if (signal.aborted || (error instanceof DOMException && error.name === 'AbortError')) throw error
    throw new CatalogError('network')
  }
  let body: unknown
  try { body = await response.json() } catch { throw new CatalogError('invalid_response') }
  if (!matchesResponse(route, response.status, body)) throw new CatalogError('invalid_response')
  if (!response.ok) throw new CatalogError(response.status === 404 ? 'not_found' : 'unavailable')
  return body as T
}

export function listCapabilities(signal: AbortSignal) {
  return request<Capability[]>('/research/capabilities', '/api/research/capabilities', signal)
}

export function getCapability(id: string, signal: AbortSignal) {
  return request<Capability>('/research/capabilities/{id}', `/api/research/capabilities/${encodeURIComponent(id)}`, signal)
}
