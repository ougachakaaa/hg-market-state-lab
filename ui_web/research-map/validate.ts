import { readFileSync, realpathSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import { fileURLToPath, URL } from 'node:url'
import { Ajv } from 'ajv'
import { isStaticWorkspacePath } from '../src/app/routeInventory.ts'
import { edgeId, isEvidenceReference, type ResearchMap, type ResearchReference } from './definition.ts'

const root = fileURLToPath(new URL('../../', import.meta.url))
export const mapLocation = 'docs/strategy-research/map.json'
export const mapPath = resolve(root, mapLocation)
export const schemaPath = resolve(root, 'docs/strategy-research/schema.json')
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

  const nodes = new Map<string, ResearchMap['nodes'][number]>()
  for (const node of input.nodes) {
    if (nodes.has(node.id)) fail(`duplicate node ${node.id}`)
    nodes.set(node.id, node)
  }
  if (!input.nodes.some(node => node.kind === 'strategy')) fail('expected at least one Strategy')

  for (const node of input.nodes) {
    const { id, kind, evidence, conclusion, references } = node
    if (!id.startsWith(`${kind}-`)) fail(`${id} must start with ${kind}-`)
    for (const reference of references) validateReference(id, reference)
    if (kind === 'finding') {
      if (evidence !== 'accepted') fail(`${id} must be accepted`)
      if (references.some(isEvidenceReference)) fail(`${id} takes result and report references from its Studies`)
    } else if (evidence !== 'pending' && !references.some(isEvidenceReference)) {
      fail(`${id} needs a concrete result or report`)
    }
    if (evidence === 'accepted') {
      if (conclusion.status === 'pending' || !conclusion.review) fail(`${id} needs a conclusion and review for accepted evidence`)
    } else if (conclusion.status !== 'pending' || conclusion.review) {
      fail(`${id} can only record a reviewed conclusion with accepted evidence`)
    }
  }

  const edges = new Set<string>()
  const branchChildren = new Set<string>()
  const sourcedFindings = new Set<string>()
  for (const edge of input.edges) {
    const { from, to, kind } = edge
    const id = edgeId(edge)
    const source = nodes.get(from)
    const target = nodes.get(to)
    if (!source || !target) fail(`dangling edge ${id}`)
    if (from === to) fail(`self edge ${id}`)
    if (edges.has(id)) fail(`duplicate edge ${id}`)
    edges.add(id)

    if (kind === 'branch') {
      // Strictly increasing structural ranks also rule out cycles.
      if (!((source.kind === 'strategy' && target.kind === 'baseline') ||
        (source.kind === 'baseline' && target.kind === 'dimension'))) fail(`invalid branch direction ${id}`)
      if (branchChildren.has(to)) fail(`${to} has multiple branch parents`)
      branchChildren.add(to)
    } else if (kind === 'attach') {
      if (source.kind !== 'dimension' || target.kind !== 'study') fail(`invalid attach direction ${id}`)
    } else {
      if (source.kind !== 'study' || target.kind !== 'finding') fail(`invalid derived_from direction ${id}`)
      if (source.evidence !== 'accepted') fail(`${to} needs accepted evidence from ${from}`)
      sourcedFindings.add(to)
    }
  }

  for (const { id, kind } of input.nodes) {
    if ((kind === 'baseline' || kind === 'dimension') && !branchChildren.has(id)) fail(`${id} needs a branch parent`)
    if (kind === 'finding' && !sourcedFindings.has(id)) fail(`${id} needs an accepted source Study`)
  }
  return input
}
