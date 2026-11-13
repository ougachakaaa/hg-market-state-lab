import Ajv2020 from 'ajv/dist/2020.js'
import { validateChartView, type ChartView as ChartViewContract } from '../../../shared/visualization/contract'
import openapi from './research.openapi.json'
import type { components } from './research.generated'

type Schemas = components['schemas']
export type PublicationList = Schemas['PublicationList']
export type Manifest = Schemas['Manifest']
export type Analysis = Schemas['Analysis']

const ajv = new Ajv2020({ strictSchema: false })
// The generated schemas annotate date-only fields with `format: date`.
ajv.addFormat('date', /^\d{4}-\d{2}-\d{2}$/)
const validators = Object.fromEntries(Object.entries(openapi.paths).map(([path, entry]) => [path,
  Object.fromEntries(Object.entries(entry.get.responses).map(([status, response]) => [status,
    ajv.compile({ ...response.content['application/json'].schema, components: openapi.components })]))]))
const chartViewValidator = ajv.compile({ ...openapi.components.schemas.ChartView, components: openapi.components })
type Route = keyof typeof openapi.paths

export function matchesResponse(route: Route, status: number, body: unknown): boolean {
  const validator = (validators[route] as Record<string, (value: unknown) => boolean> | undefined)?.[status]
  return validator?.(body) === true
}

export function matchesPublicationList(body: unknown): body is PublicationList {
  return matchesResponse('/research/publications', 200, body)
}

export function matchesManifest(body: unknown): body is Manifest {
  return matchesResponse('/research/publications/{publication_id}', 200, { data: body })
}

export function matchesAnalysis(body: unknown): body is Analysis {
  return matchesResponse('/research/publications/{publication_id}/analyses/{analysis_id}', 200, { data: body })
}

export function validatePublicationList(body: unknown): PublicationList {
  if (!matchesPublicationList(body)) throw new Error('Invalid Research publication list')
  return body
}

export function validateManifest(body: unknown): Manifest {
  if (!matchesManifest(body)) throw new Error('Invalid Research publication manifest')
  return body
}

export function validateAnalysis(body: unknown): Analysis {
  if (!matchesAnalysis(body)) throw new Error('Invalid Research analysis')
  return body
}

// The HTTP View body is a generated-contract ChartView that must also satisfy the
// shared Visualization contract. Both checks are required; neither is a second DTO.
export function validateChartViewData(view: unknown): ChartViewContract {
  if (!chartViewValidator(view)) throw new Error('Invalid Research ChartView payload')
  try {
    validateChartView(view)
  } catch {
    throw new Error('Invalid Research ChartView contract')
  }
  return view
}

export function validateChartViewResponse(body: unknown): ChartViewContract {
  if (!matchesResponse('/research/publications/{publication_id}/views/{view_id}', 200, body)) {
    throw new Error('Invalid Research View response')
  }
  return validateChartViewData((body as Schemas['ViewResponse']).data)
}
