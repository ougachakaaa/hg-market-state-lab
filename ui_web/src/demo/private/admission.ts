import { validateOptionChain } from '../../features/mo_option_chain/api/validateOptionChain'
import { validatePremiumPlane } from '../../features/mo_option_premium/api/validatePremiumPlane'
import { validateEmbeddedReport } from '../../features/futures_basis_research/api/validateResult'
import { validateEmbeddedBacktestResult } from '../../features/backtesting/api/validateResult'
import { validateEmbeddedCatalog } from '../../features/research_catalog/api/validateCatalog'
import { validateEmbeddedPublicationSet } from '../../features/research_explorer/api/validateEmbeddedPublication'

export const exampleKeys = ['chain', 'premium', 'basis', 'catalog', 'publications', 'expiry_to_M1_v1', 'expiry_to_Q1_v1'] as const
export type ExampleKey = typeof exampleKeys[number]
export interface ExampleIdentity {
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
const producers: Record<ExampleKey, string> = {
  chain: 'data_snapshot.products.mo_option_chain.service.read_chain_with_api',
  premium: 'data_snapshot.products.mo_option_premium.service.read_premium_plane_with_api',
  basis: 'market_research/scripts/futures_basis_report.py',
  catalog: 'market_research.descriptive.capabilities.list_capabilities / get_capability',
  publications: 'market_research.descriptive.execution.execute_batch / market_research.publication.publish',
  expiry_to_M1_v1: 'market_backtesting.cases.futures_roll_long.create_futures_roll_service / build_backtest_result',
  expiry_to_Q1_v1: 'market_backtesting.cases.futures_roll_long.create_futures_roll_service / build_backtest_result',
}
export { producers }
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
const requireFact = (ok: boolean) => { if (!ok) throw new Error('Private Example request or coverage mismatch') }
const windowMatches = (r: { start_date: string; end_date: string; product_code: string }) =>
  r.start_date === '2026-01-01' && r.end_date === '2026-11-11' && r.product_code === 'IM'

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
  const chain = validateOptionChain(payloads.chain)
  requireFact(chain.target_trade_date === '2026-11-11' && chain.price_type === 'close' && chain.option_product === 'MO')
  requireFact(chain.expiries.length === 6 && chain.expiries.reduce((n, e) => n + e.calls.length + e.puts.length, 0) === 312 && chain.expiries.filter(e => e.futures !== null).length === 4)
  const premium = validatePremiumPlane(payloads.premium)
  requireFact(premium.plane.observation.value === '2026-11-11' && premium.plane.price_type === 'close' && premium.plane.option_product === 'MO' && premium.plane.points.length === 312 && premium.plane.expiries.length === 6 && premium.plane.expiries.filter(e => e.futures !== null).length === 4)
  const basis = validateEmbeddedReport(payloads.basis as Parameters<typeof validateEmbeddedReport>[0])
  requireFact(windowMatches(basis.request) && basis.report.candidate_dates.length === 206 && Object.keys(basis.report.views.history).length === 3 && basis.report.persistence.length === 4)
  requireFact(basis.report.fingerprint === envelope.examples.basis.identity.inputFingerprint)
  const m1 = validateEmbeddedBacktestResult(payloads.expiry_to_M1_v1 as Parameters<typeof validateEmbeddedBacktestResult>[0])
  const q1 = validateEmbeddedBacktestResult(payloads.expiry_to_Q1_v1 as Parameters<typeof validateEmbeddedBacktestResult>[0])
  for (const [key, data] of [['expiry_to_M1_v1', m1], ['expiry_to_Q1_v1', q1]] as const) {
    requireFact(windowMatches(data.request) && data.request.strategy_profile === key && data.result.window.cffex_session_count === 206 && data.result.evidence.input_fingerprint === envelope.examples[key].identity.inputFingerprint)
  }
  const catalogPayload = payloads.catalog as Parameters<typeof validateEmbeddedCatalog>[0]
  const catalog = validateEmbeddedCatalog(catalogPayload)
  requireFact(catalog.capabilities.length > 0 && catalog.capabilities.every(c => c.live_readiness === 'not_probed'))
  const publicationPayload = payloads.publications as Parameters<typeof validateEmbeddedPublicationSet>[0]
  const publications = validateEmbeddedPublicationSet(publicationPayload)
  requireFact(publications.publicationIds.size === 1 && publicationPayload.analyses.length === 4 && publicationPayload.views.length === 6)
  for (const manifest of publications.manifests.values()) {
    requireFact(manifest.scope.metric === 'trailing_cumulative_return_v1' && JSON.stringify(manifest.scope.subjects) === JSON.stringify(['000852.SH']) && JSON.stringify(manifest.scope.horizons) === JSON.stringify([20, 60]) && manifest.scope.windows.length === 1)
    requireFact(manifest.source.sha256 === envelope.examples.publications.identity.inputFingerprint)
    requireFact(manifest.scope.windows.every(w => w.start_date === '2026-01-01' && w.end_date === '2026-11-11'))
    requireFact(manifest.analyses.every(a => publications.analyses.get(manifest.publication_id)?.has(a.analysis_id) === true && a.views.every(v => publications.views.get(manifest.publication_id)?.has(v.view_id) === true)))
  }
  return { chain, premium, basis, m1, q1, catalogPayload, publicationPayload, identities: Object.fromEntries(exampleKeys.map(k => [k, envelope.examples[k].identity])) as Record<ExampleKey, ExampleIdentity> }
}
export type PrivateData = Awaited<ReturnType<typeof admitPrivateEnvelope>>
export function sourceDisclosure(identity: ExampleIdentity) {
  validateIdentity(identity, identity.id)
  const scope = identity.id === 'catalog' ? '正式 Capability Catalog · live_readiness=not_probed'
    : identity.id === 'chain' || identity.id === 'premium' ? '观察日期 2026-11-11 · close · 312 合约 / 六个 Expiries'
      : '请求窗口 2026-01-01..2026-11-11 · 实际观测 2026-01-05..2026-11-11 · 206 交易日'
  const copy = identity.id === 'chain' || identity.id === 'premium' ? '复制和导出保留完整已校验结果。' : ''
  return `${identity.id === 'catalog' ? '正式元数据' : 'Historical Real Market Data'} · Source: ${identity.provider} · ${scope} · Formal Producer: ${identity.producer} · Static, read-only, no live server execution · Private；Publication Rights: BLOCKED。研究限制见正式结果；指纹不证明独立市场认证或公开权限。浏览器仅包含正式展示投影，完整原始证据保留在私有包。${copy}`
}
