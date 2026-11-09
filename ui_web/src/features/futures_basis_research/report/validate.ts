import { validateVisualizationView } from '../../../shared/visualization/contractV2'
import type { ReportData } from './types'

// Reader-shape validation only. Research remains the owner of numerical legality.
function object(value: unknown): Record<string, any> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid reader object')
  return value as Record<string, any>
}
function list(value: unknown): any[] {
  if (!Array.isArray(value)) throw new Error('Invalid reader list')
  return value
}
function strings(value: unknown) { list(value).forEach(string) }
function string(value: unknown) { if (typeof value !== 'string') throw new Error('Invalid reader text') }
function number(value: unknown) { if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('Invalid reader number') }
function nullableText(value: unknown) { if (value !== null) string(value) }
function methods(value: unknown) {
  list(value).forEach(raw => {
    const m = object(raw); string(object(m.spec).method); nullableText(m.failure_category); nullableText(m.reason)
    if (m.result === null) return
    const r = object(m.result); string(r.method); string(r.unit); number(r.sample_count)
    if (r.estimator !== undefined) string(r.estimator)
    for (const key of ['value', 'underflow_count', 'overflow_count', 'underflow_frequency', 'overflow_frequency']) if (r[key] !== undefined) number(r[key])
    if (r.edges !== undefined) list(r.edges).forEach(number)
    if (r.points_and_values !== undefined) list(r.points_and_values).forEach(pair => { if (list(pair).length !== 2) throw new Error('Invalid quantile'); pair.forEach(number) })
    if (r.bins !== undefined) list(r.bins).forEach(rawBin => {
      const b = object(rawBin)
      for (const k of ['left', 'right', 'count', 'frequency']) number(b[k])
      if (typeof b.left_inclusive !== 'boolean' || typeof b.right_inclusive !== 'boolean') throw new Error('Invalid interval')
    })
  })
}
function request(value: unknown) { const r = object(value); string(r.analysis_id); string(r.metric); if (r.slot !== undefined) string(r.slot); if (r.slots !== undefined) strings(r.slots); if (r.histogram !== undefined) string(object(r.histogram).unit) }
export function validateReportData(input: unknown): asserts input is ReportData {
  const d = object(input)
  if (d.profile !== 'futures_basis_report_evidence_v1' || !['complete', 'partial'].includes(d.status)) throw new Error('Unsupported reader')
  for (const key of ['fingerprint', 'definition_version', 'summary', 'sources']) string(d[key])
  const formal = object(d.request)
  const quantile = object(formal.quantile); string(quantile.method); list(quantile.points).forEach(number)
  list(formal.histograms).forEach(raw => { const h = object(raw); string(h.method); string(h.unit); list(h.edges).forEach(number) })
  if (!d.fingerprint.length) throw new Error('Missing fingerprint')
  const obs = object(formal.observation)
  if (obs.case !== 'futures_basis_v1') throw new Error('Unsupported case')
  for (const key of ['product_code', 'start_date', 'end_date']) string(obs[key])
  strings(d.formulas); strings(d.limitations); strings(d.candidate_dates)
  Object.values(object(d.coverage)).forEach(raw => {
    const c = object(raw)
    for (const k of ['requested_units', 'successful_units', 'missing_units', 'pending_units', 'failed_units']) number(c[k])
    if (typeof c.complete !== 'boolean') throw new Error('Invalid coverage')
  })
  list(d.accounting).forEach(raw => { const a = object(raw); string(a.slot); string(a.metric); number(a.candidate_count); list(a.outcomes).forEach(rawOutcome => { const o = object(rawOutcome); string(o.status); list(o.identities); if (o.candidate_ratio !== null) number(o.candidate_ratio) }) })
  list(d.distributions).forEach(raw => { const x = object(raw); request(x.request); list(x.candidates); list(x.binding); if (!list(x.methods).length) throw new Error('Missing methods'); methods(x.methods) })
  list(d.comparisons).forEach(raw => {
    const x = object(raw); request(x.request); strings(x.common_dates); list(x.dropped); methods(x.left_methods); methods(x.right_methods)
    list(x.dropped_details).forEach(rawDetail => { const detail = object(rawDetail); string(detail.date); for (const side of ['left', 'right']) { const s = object(detail[side]); string(s.slot); string(object(s.outcome).status); nullableText(s.outcome.reason) } })
  })
  list(d.persistence).forEach(raw => { const p = object(raw); string(p.slot); for (const kind of ['complete', 'censored']) list(p[kind]).forEach(rawRun => { const r = object(rawRun); for (const k of ['slot', 'start', 'end', 'left_boundary', 'right_boundary']) string(r[k]); number(r.observed_trading_sessions); list(r.transitions) }) })
  const views = object(d.views); const history = object(views.history)
  for (const metric of ['basis_value', 'basis_ratio', 'annualized_basis_ratio']) validateVisualizationView(history[metric])
  Object.values(history).forEach(validateVisualizationView)
  Object.values(object(views.histograms)).forEach(validateVisualizationView)
  if (d.runtime !== undefined) { const r = object(d.runtime); for (const k of ['revision', 'python', 'node']) string(r[k]); if (typeof r.dirty !== 'boolean') throw new Error('Invalid runtime'); Object.values(object(r.packages)).forEach(string); Object.values(object(r.frontend_packages)).forEach(string) }
}
