import { readFileSync, realpathSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath, URL } from 'node:url'
import { Ajv } from 'ajv'
import { isStaticWorkspacePath } from '../src/app/routeInventory.ts'
import { edgeId, type ResearchMap, type ResearchReference } from './definition.ts'

const root = fileURLToPath(new URL('../../', import.meta.url))
export const mapPath = fileURLToPath(new URL('./map.json', import.meta.url))
export const schemaPath = fileURLToPath(new URL('./schema.json', import.meta.url))
const researchDirectory = /^(?:market_research|market_backtesting|docs\/strategy-research)\//
const sourceDirectory = /^(?:docs\/strategy-research|market_research|market_backtesting|market_statistics|data_lake|data_snapshot)\//

function fail(message: string): never {
  throw new Error(`Strategy Research Map: ${message}`)
}

function validateReference(nodeId: string, reference: ResearchReference) {
  const { kind, value } = reference
  if (reference.target === 'workspace') {
    if (!isStaticWorkspacePath(value)) fail(`${nodeId} references unknown shared workspace path ${value}`)
    return
  }
  const evidencePath = researchDirectory.test(value) && /\/(evidence|reports)\//.test(value)
  const bundlePath = kind === 'result' && /^ui_web\/demo\/bundles\/[a-zA-Z0-9_-]+\.json$/.test(value)
  const allowed = kind === 'source'
    ? sourceDirectory.test(value) && value.endsWith('.md')
    : (kind === 'report' && evidencePath) || (kind === 'result' && evidencePath && value.endsWith('.json')) || bundlePath
  if (!allowed) fail(`${nodeId} has invalid ${kind} reference ${value}`)

  const path = resolve(root, value)
  if (!statSync(path, { throwIfNoEntry: false })?.isFile() || realpathSync(path) !== path) {
    fail(`${nodeId} references a missing or linked file ${value}`)
  }
  if (bundlePath) {
    const manifest: { bundles: { path: string }[] } = JSON.parse(readFileSync(resolve(root, 'ui_web/demo/bundles/manifest.json'), 'utf8'))
    if (!manifest.bundles.some(entry => value === `ui_web/demo/bundles/${entry.path}`)) {
      fail(`${nodeId} references an unregistered Demo Bundle ${value}`)
    }
  }
}

export function validateResearchMap(input: unknown): ResearchMap {
  const ajv = new Ajv({ allErrors: true })
  const valid = ajv.compile<ResearchMap>(JSON.parse(readFileSync(schemaPath, 'utf8')))
  if (!valid(input)) fail(ajv.errorsText(valid.errors, { separator: '\n' }))

  const dependencies = new Map<string, string[]>()
  for (const node of input.nodes) {
    const { id, evidence, conclusion, references } = node
    if (dependencies.has(id)) fail(`duplicate node ${id}`)
    dependencies.set(id, [])
    for (const reference of references) validateReference(id, reference)
    const hasEvidence = references.some(({ kind }) => kind === 'result' || kind === 'report')
    if (evidence !== 'pending' && !hasEvidence) fail(`${id} needs a concrete result or report`)
    if (evidence === 'accepted') {
      if (conclusion.status === 'pending' || !conclusion.review) fail(`${id} needs a conclusion and review for accepted evidence`)
    } else if (conclusion.status !== 'pending' || conclusion.review) {
      fail(`${id} can only record a reviewed conclusion with accepted evidence`)
    }
  }

  const edges = new Set<string>()
  for (const edge of input.edges) {
    const { from, to, kind } = edge
    const id = edgeId(edge)
    const targets = dependencies.get(from)
    if (!targets || !dependencies.has(to)) fail(`dangling edge ${id}`)
    if (from === to) fail(`self edge ${id}`)
    if (edges.has(id)) fail(`duplicate edge ${id}`)
    edges.add(id)
    if (kind === 'dependency') targets.push(to)
  }

  const visiting = new Set<string>()
  const visited = new Set<string>()
  function visit(id: string) {
    if (visiting.has(id)) fail(`dependency cycle at ${id}`)
    if (visited.has(id)) return
    visiting.add(id)
    for (const target of dependencies.get(id)!) visit(target)
    visiting.delete(id)
    visited.add(id)
  }
  for (const id of dependencies.keys()) visit(id)
  return input
}
