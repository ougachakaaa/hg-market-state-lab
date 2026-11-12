import Ajv2020 from 'ajv/dist/2020.js'
import openApi from './moOptionChain.openapi.json'
import type { components, paths } from './moOptionChain.generated'

const path = '/mo-option-chain' satisfies keyof paths
type Operation = paths[typeof path]['get']
// Public client types are projections of the generated HTTP contract.
export type OptionChain = Operation['responses'][200]['content']['application/json']
export type ExpiryGroup = OptionChain['expiries'][number]
export type OptionPoint = ExpiryGroup['calls'][number]
export type ChainError = components['schemas']['ChainErrorBody']
export type ChainErrorKind = ChainError['kind']
type ErrorStatus = Exclude<keyof Operation['responses'], 200>
export type ChainErrorResponse = Operation['responses'][ErrorStatus]['content']['application/json']

// Validate against the response schemas exported by FastAPI. The front end has
// no separately maintained field rules or enum lists.
// "components" is an OpenAPI reference container, not a JSON Schema keyword.
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

export function validateOptionChain(body: unknown): OptionChain {
  if (!matchesResponse(200, body)) throw new Error('Invalid MO Option Chain result')
  return body as OptionChain
}
