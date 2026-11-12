import Ajv2020 from 'ajv/dist/2020.js'
import openapi from './catalog.openapi.json'
import type { components, operations } from './catalog.generated'

// Public Capability types are projections of the generated HTTP contract.
export type Capability = components['schemas']['CapabilityDescription']
export type CapabilityList = operations['list_research_capabilities']['responses'][200]['content']['application/json']

const ajv = new Ajv2020({ strictSchema: false })
const validators = Object.fromEntries(Object.entries(openapi.paths).map(([path, entry]) => [path,
  Object.fromEntries(Object.entries(entry.get.responses).map(([status, response]) => [status,
    ajv.compile({ ...response.content['application/json'].schema, components: openapi.components })]))]))
type Route = keyof typeof openapi.paths

export function matchesResponse(route: Route, status: number, body: unknown): boolean {
  const validator = (validators[route] as Record<string, (value: unknown) => boolean> | undefined)?.[status]
  return validator?.(body) === true
}

export function matchesCapabilityList(body: unknown): body is CapabilityList {
  return matchesResponse('/research/capabilities', 200, body)
}

export function matchesCapabilityDetail(body: unknown): body is Capability {
  return matchesResponse('/research/capabilities/{id}', 200, body)
}

export function validateCapabilityList(body: unknown): CapabilityList {
  if (!matchesCapabilityList(body)) throw new Error('Invalid Research capability list')
  return body
}

export function validateCapabilityDetail(body: unknown): Capability {
  if (!matchesCapabilityDetail(body)) throw new Error('Invalid Research capability detail')
  return body
}

export interface EmbeddedCatalogPayload {
  list: unknown
  details: readonly unknown[]
}

export interface ValidatedEmbeddedCatalog {
  capabilities: CapabilityList
  details: ReadonlyMap<string, Capability>
}

// Static embedded descriptors are the same published CapabilityDescription schema as
// Production. Association is validated locally: IDs are unique and every bundled detail
// belongs to an embedded list item. A list item may legitimately have no detail.
export function validateEmbeddedCatalog(payload: EmbeddedCatalogPayload): ValidatedEmbeddedCatalog {
  if (typeof payload !== 'object' || payload === null || !Array.isArray(payload.details)) {
    throw new Error('Invalid embedded Research catalog')
  }
  const capabilities = validateCapabilityList(payload.list)
  const listedIds = new Set<string>()
  for (const capability of capabilities) {
    if (listedIds.has(capability.id)) throw new Error(`Duplicate embedded capability id: ${capability.id}`)
    listedIds.add(capability.id)
  }
  const details = new Map<string, Capability>()
  for (const raw of payload.details) {
    const detail = validateCapabilityDetail(raw)
    if (details.has(detail.id)) throw new Error(`Duplicate embedded capability detail: ${detail.id}`)
    if (!listedIds.has(detail.id)) throw new Error(`Embedded capability detail is not listed: ${detail.id}`)
    details.set(detail.id, detail)
  }
  return { capabilities, details }
}
