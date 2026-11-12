import Ajv2020 from 'ajv/dist/2020.js'
import openApi from './moOptionPremium.openapi.json'
import type { components, paths } from './moOptionPremium.generated'

const path = '/mo-option-premium-plane' satisfies keyof paths
type Operation = paths[typeof path]['get']
type Query = Operation['parameters']['query']

export type PremiumPlane = Operation['responses'][200]['content']['application/json']
export type PremiumExpiry = PremiumPlane['expiries'][number]
export type PremiumPoint = PremiumPlane['points'][number]
export type PremiumPriceType = NonNullable<Query['price_type']>
export type PremiumError = components['schemas']['PremiumErrorBody']
export type PremiumErrorKind = PremiumError['kind']
export interface PremiumPlaneResult {
  plane: PremiumPlane
  rawPayload: unknown
}
type ErrorStatus = Exclude<keyof Operation['responses'], 200>
export type PremiumErrorResponse = Operation['responses'][ErrorStatus]['content']['application/json']

const ajv = new Ajv2020({ strictSchema: false })
const responseValidators = new Map(
  Object.entries(openApi.paths[path].get.responses).map(([status, response]) => [
    Number(status),
    ajv.compile({
      ...response.content['application/json'].schema,
      components: openApi.components,
    }),
  ]),
)

export function matchesResponse(status: number, body: unknown): boolean {
  return responseValidators.get(status)?.(body) === true
}

// HTTP contract §5.4: structural validity alone does not establish success.
export function matchesPremiumResult(body: unknown): body is PremiumPlane {
  return matchesResponse(200, body) && (body as PremiumPlane).points.length > 0
}

export function validatePremiumPlane(body: unknown): PremiumPlaneResult {
  if (!matchesPremiumResult(body)) throw new Error('Invalid MO Premium Plane result')
  return { plane: body, rawPayload: body }
}
