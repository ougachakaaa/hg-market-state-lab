import { exampleKeys, producers, validateExampleResults, type ExampleKey, type ResultIdentity } from '../static/results'

export const gates = ['realSource', 'formalProducer', 'contractIdentity', 'coverage', 'publicationRights', 'publicDataSafety'] as const
export const categories = ['source_facts', 'identity_metadata', 'derived_statistics', 'backtesting_results', 'visualization_views', 'embedded_json', 'copy_json_csv'] as const
interface GateReview {
  status: 'PASS' | 'USER_DIRECTED'
  reviewer: string
  reviewedAt: string
  reason: string
  evidence: string
  evidenceDigest: string
}
export interface PublicIdentity extends ResultIdentity {
  rights: 'user_directed_public'
  publicRights: 'USER_DIRECTED'
  disclosure: string
}
export interface PublicReview {
  resultDigest: string
  gates: Record<typeof gates[number], GateReview>
  channels: string[]
  categories: string[]
  licenseBasis: string
  conditions: string
  expiresAt: string | null
}
export interface PublicEnvelope {
  profile: 'portfolio-public-v2-v1'
  examples: Record<ExampleKey, { identity: PublicIdentity; json: string; review: PublicReview }>
}
const hex = (s: unknown, length: number) => typeof s === 'string' && new RegExp(`^[a-f0-9]{${length}}$`).test(s)
const text = (s: unknown) => typeof s === 'string' && s.trim().length > 0
export function validatePublicRecord(identity: PublicIdentity, review: PublicReview, key: ExampleKey, now = Date.now()) {
  if (!identity || identity.id !== key || identity.revision !== 1 || identity.delivery !== 'static' ||
    identity.origin !== 'real_market' || identity.execution !== 'historical_embedded_result' ||
    identity.rights !== 'user_directed_public' || identity.publicRights !== 'USER_DIRECTED' || !text(identity.provider) ||
    identity.producer !== producers[key] || !hex(identity.sourceRevision, 40) || !hex(identity.resultDigest, 64) ||
    !hex(identity.evidenceDigest, 64) || !text(identity.disclosure) ||
    (['chain', 'premium', 'catalog'].includes(key) ? identity.inputFingerprint !== null : !hex(identity.inputFingerprint, 64))) throw new Error('Invalid public Example identity')
  if (!review || review.resultDigest !== identity.resultDigest || !text(review.licenseBasis) || !text(review.conditions) ||
    !Array.isArray(review.channels) || !['github_repository', 'github_pages'].every(c => review.channels.includes(c)) ||
    !Array.isArray(review.categories) || !categories.every(c => review.categories.includes(c)) ||
    !(review.expiresAt === null || (Number.isFinite(Date.parse(review.expiresAt)) && Date.parse(review.expiresAt) > now))) throw new Error('Missing or expired publication decision')
  for (const gate of gates) {
    const r = review.gates?.[gate]
    if (!r || r.status !== (gate === 'publicationRights' ? 'USER_DIRECTED' : 'PASS') || !text(r.reviewer) || !text(r.reason) || !Number.isFinite(Date.parse(r.reviewedAt)) ||
      Date.parse(r.reviewedAt) > now || !/^evidence\/[a-zA-Z0-9_/-]+\.md$/.test(r.evidence) || r.evidence.includes('..') ||
      !hex(r.evidenceDigest, 64)) throw new Error(`Public admission gate: ${gate}`)
  }
}
export async function admitPublicEnvelope(envelope: PublicEnvelope) {
  if (envelope?.profile !== 'portfolio-public-v2-v1' || !envelope.examples ||
    Object.keys(envelope.examples).sort().join() !== [...exampleKeys].sort().join()) throw new Error('No complete reviewed public V2 package')
  const payloads: Partial<Record<ExampleKey, unknown>> = {}
  for (const key of exampleKeys) {
    const item = envelope.examples[key]
    validatePublicRecord(item?.identity, item?.review, key)
    if (typeof item.json !== 'string') throw new Error('Missing public Result')
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(item.json))), b => b.toString(16).padStart(2, '0')).join('')
    if (digest !== item.identity.resultDigest) throw new Error('Public Result digest mismatch')
    payloads[key] = JSON.parse(item.json)
  }
  return validateExampleResults(payloads, Object.fromEntries(exampleKeys.map(k => [k, envelope.examples[k].identity])) as Record<ExampleKey, PublicIdentity>)
}
