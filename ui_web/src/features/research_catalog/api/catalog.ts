import Ajv2020 from 'ajv/dist/2020.js'
import { protectedRequest } from '../../../shared/http/protectedRequest'
import openapi from './catalog.openapi.json'
import type { components } from './catalog.generated'

export type Capability = components['schemas']['CapabilityDescription']
export type CatalogFailure = 'network' | 'invalid_response' | 'unavailable' | 'not_found'

export class CatalogError extends Error {
  readonly kind: CatalogFailure
  constructor(kind: CatalogFailure) { super(kind); this.kind = kind }
}

const ajv = new Ajv2020({ strictSchema: false })
const validators = Object.fromEntries(Object.entries(openapi.paths).map(([path, entry]) => [path,
  Object.fromEntries(Object.entries(entry.get.responses).map(([status, response]) => [status,
    ajv.compile({ ...response.content['application/json'].schema, components: openapi.components })]))]))
type Route = keyof typeof openapi.paths

async function request<T>(route: Route, url: string, signal: AbortSignal): Promise<T> {
  let response: Response
  try { response = await protectedRequest(url, signal) } catch (error) {
    if (signal.aborted || (error instanceof DOMException && error.name === 'AbortError')) throw error
    throw new CatalogError('network')
  }
  let body: unknown
  try { body = await response.json() } catch { throw new CatalogError('invalid_response') }
  const validator = (validators[route] as Record<string, (value: unknown) => boolean>)[response.status]
  if (!validator?.(body)) throw new CatalogError('invalid_response')
  if (!response.ok) throw new CatalogError(response.status === 404 ? 'not_found' : 'unavailable')
  return body as T
}

export function listCapabilities(signal: AbortSignal) {
  return request<Capability[]>('/research/capabilities', '/api/research/capabilities', signal)
}

export function getCapability(id: string, signal: AbortSignal) {
  return request<Capability>('/research/capabilities/{id}', `/api/research/capabilities/${encodeURIComponent(id)}`, signal)
}
