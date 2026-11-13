import { exampleKeys, producers, validateExampleResults, type ExampleKey, type ResultIdentity } from '../static/results'
export { exampleKeys, producers }
export type { ExampleKey }
export interface ExampleIdentity extends ResultIdentity {
  id: ExampleKey
  revision: 1
  delivery: 'static'
  origin: 'real_market'
  execution: 'historical_embedded_result'
  rights: 'private'
  publicRights: 'BLOCKED'
  provider: 'Tushare' | 'formal_capability_facade'
  producer: string
  sourceRevision: string
  inputFingerprint: string | null
  evidenceDigest: string
  resultDigest: string
}
export interface PrivateEnvelope {
  profile: 'wp-b-private-static-v1'
  examples: Record<ExampleKey, { identity: ExampleIdentity; json: string }>
}
export function validateIdentity(identity: ExampleIdentity, key: ExampleKey) {
  if (!identity || identity.id !== key || identity.revision !== 1 || identity.delivery !== 'static' ||
    identity.origin !== 'real_market' || identity.execution !== 'historical_embedded_result' ||
    identity.rights !== 'private' || identity.publicRights !== 'BLOCKED' ||
    identity.provider !== (key === 'catalog' ? 'formal_capability_facade' : 'Tushare') ||
    identity.producer !== producers[key] ||
    (['basis', 'publications', 'expiry_to_M1_v1', 'expiry_to_Q1_v1'].includes(key) ? !/^[a-f0-9]{64}$/.test(identity.inputFingerprint ?? '') : identity.inputFingerprint !== null) || !/^[a-f0-9]{40}$/.test(identity.sourceRevision) ||
    !/^[a-f0-9]{64}$/.test(identity.evidenceDigest) || !/^[a-f0-9]{64}$/.test(identity.resultDigest)) {
    throw new Error('Incomplete or unsupported private Example identity')
  }
}
/** One admission path for Node pre-build checks and browser startup. No financial computation. */
export async function admitPrivateEnvelope(envelope: PrivateEnvelope) {
  if (envelope?.profile !== 'wp-b-private-static-v1' || !envelope.examples ||
    Object.keys(envelope.examples).sort().join() !== [...exampleKeys].sort().join()) throw new Error('Invalid private static package')
  const payloads: Partial<Record<ExampleKey, unknown>> = {}
  for (const key of exampleKeys) {
    const item = envelope.examples[key]
    validateIdentity(item?.identity, key)
    if (typeof item.json !== 'string') throw new Error('Missing private Result')
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(item.json))), b => b.toString(16).padStart(2, '0')).join('')
    if (digest !== item.identity.resultDigest) throw new Error('Private Result digest mismatch')
    payloads[key] = JSON.parse(item.json)
  }
  return validateExampleResults(payloads, Object.fromEntries(exampleKeys.map(k => [k, envelope.examples[k].identity])) as Record<ExampleKey, ExampleIdentity>)
}
export type PrivateData = Awaited<ReturnType<typeof admitPrivateEnvelope>>
export function sourceDisclosure(identity: ResultIdentity) {
  validateIdentity(identity as ExampleIdentity, identity.id)
  const scope = identity.id === 'catalog' ? '正式 Capability Catalog · live_readiness=not_probed'
    : identity.id === 'chain' || identity.id === 'premium' ? '观察日期 2026-11-11 · close · 312 合约 / 六个 Expiries'
      : '请求窗口 2026-01-01..2026-11-11 · 实际观测 2026-01-05..2026-11-11 · 206 交易日'
  const copy = identity.id === 'chain' || identity.id === 'premium' ? '复制和导出保留完整已校验结果。' : ''
  return `${identity.id === 'catalog' ? '正式元数据' : 'Historical Real Market Data'} · Source: ${identity.provider} · ${scope} · Formal Producer: ${identity.producer} · Static, read-only, no live server execution · Private；Publication Rights: BLOCKED。研究限制见正式结果；指纹不证明独立市场认证或公开权限。浏览器仅包含正式展示投影，完整原始证据保留在私有包。${copy}`
}
