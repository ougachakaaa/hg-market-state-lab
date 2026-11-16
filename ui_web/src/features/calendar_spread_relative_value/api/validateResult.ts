import Ajv2020 from 'ajv/dist/2020.js'
import openapi from './relativeValue.openapi.json'
import type { components } from './relativeValue.generated'

type S = components['schemas']
export type ErrorResult = S['HistoricalErrorResponse'] | S['AuthErrorResponse']
export type Result = S['HistoricalResponse']
export type Query = S['HistoricalRequest']
export const pairs = ['M0/M1', 'M0/Q1', 'M0/Q2', 'M1/Q1', 'M1/Q2', 'Q1/Q2'] as const
export const products = ['IF', 'IH', 'IC', 'IM'] as const
export const units = { signed_spread: 'index_points', annualized_point_spread: 'index_points_per_365_natural_days', annualized_spread_ratio: 'decimal_ratio' } as const
const ajv = new Ajv2020({ strictSchema: false, strictTypes: false, strictNumbers: true, formats: {
  date: (v: string) => /^\d{4}-\d{2}-\d{2}$/.test(v) && v >= '0001-01-01' && Number.isFinite(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v,
} })
const schema = ajv.compile({ ...openapi.components.schemas.HistoricalResponse, components: openapi.components })
const operation = openapi.paths['/research/calendar-spread-relative-value/query'].post
const responses = new Map(Object.entries(operation.responses).map(([status, response]) => [Number(status), ajv.compile({ ...response.content['application/json'].schema, components: openapi.components })]))
export const matchesResponse = (status: number, value: unknown) => responses.get(status)?.(value) === true
function check(ok: unknown): asserts ok { if (!ok) throw new Error('Invalid Calendar Spread result association') }
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b)
function accounting(a: S['Accounting'], count?: number) {
  const ns = [a.candidate_count, a.valid_count, a.not_applicable_count, a.excluded_count]
  check(ns.every(n => Number.isSafeInteger(n) && n >= 0))
  check(a.candidate_count === a.valid_count + a.not_applicable_count + a.excluded_count)
  if (count !== undefined) check(a.candidate_count === count)
}
function day(d: S['Day'], product: string) {
  check(d.reason === (d.status === 'closed' ? 'non_trading_day' : null))
  check(d.observations.length === (d.status === 'open' ? 6 : 0))
  d.observations.forEach((o, i) => {
    check(`${o.near_slot}/${o.far_slot}` === pairs[i] && o.product_code === product && o.trade_date === d.trade_date)
    if (o.outcome === 'not_applicable') {
      check(o.reason === 'no_active_contract' && o.near === null && o.far === null && o.metrics === null && o.delta_days === null && o.near_dte_days === null && o.expiry_stage === null)
      return
    }
    check(o.near !== null && o.far !== null && o.near.contract_code.trim() && o.far.contract_code.trim())
    check(o.near.contract_code !== o.far.contract_code && o.near.delist_date >= d.trade_date && o.near.delist_date < o.far.delist_date)
    check(Number.isSafeInteger(o.delta_days) && o.delta_days! > 0 && Number.isSafeInteger(o.near_dte_days) && o.near_dte_days! >= 0 && o.expiry_stage !== null)
    if (o.outcome === 'excluded') {
      check(o.reason === 'nonpositive_close' && (o.near.close <= 0 || o.far.close <= 0) && o.metrics === null)
    } else {
      check(o.reason === null && o.near.close > 0 && o.far.close > 0 && o.metrics !== null && o.metrics.delta_days === o.delta_days)
      for (const metric of Object.keys(units) as (keyof typeof units)[]) check(o.metrics[metric].metric_id === metric && o.metrics[metric].unit === units[metric])
    }
  })
}
const stages = ['0_7', '8_21', '22_plus', 'all_stages'] as const
const probabilities = [0, .05, .25, .5, .75, .95, 1]
function ordered(dates: string[]) { check(dates.every((d, i) => i === 0 || d > dates[i - 1])) }
function count(n: number) { check(Number.isSafeInteger(n) && n >= 0) }
export function validateResult(value: unknown, query?: Query): Result {
  check(schema(value)); const r = value as Result
  const q = r.request
  if (query) check(q.product_code === query.product_code && q.history_start === query.history_start && q.evaluation_date === query.evaluation_date && q.metric === (query.metric ?? 'annualized_spread_ratio') && same(q.histogram_edges, query.histogram_edges ?? null))
  check(q.history_start < q.evaluation_date && r.current_day.trade_date === q.evaluation_date && r.metric === q.metric && r.unit === units[r.metric])
  day(r.current_day, q.product_code)
  ordered(r.historical_days.map(d => d.trade_date))
  check(r.historical_days[0]?.trade_date === q.history_start)
  // Every natural date has an explicit Calendar summary; never infer open sessions.
  let next = q.history_start
  for (const d of r.historical_days) {
    check(d.trade_date === next && d.trade_date < q.evaluation_date && d.reason === (d.status === 'closed' ? 'non_trading_day' : null))
    const date = new Date(`${next}T00:00:00Z`); date.setUTCDate(date.getUTCDate() + 1); next = date.toISOString().slice(0, 10)
  }
  check(next === q.evaluation_date)
  const open = new Set(r.historical_days.filter(d => d.status === 'open').map(d => d.trade_date))
  accounting(r.historical_accounting, open.size * 6)
  check(r.pairs.length === 6)
  const totals = { candidate_count: 0, valid_count: 0, excluded_count: 0, not_applicable_count: 0 }
  r.pairs.forEach((p, index) => {
    check(`${p.near_slot}/${p.far_slot}` === pairs[index])
    ordered(p.samples.map(s => s.trade_date))
    const points = new Map(p.samples.map(s => [s.trade_date, s]))
    for (const s of p.samples) {
      check(open.has(s.trade_date) && s.metric.metric_id === r.metric && s.metric.unit === r.unit)
      check(s.near.contract_code.trim() && s.far.contract_code.trim() && s.near.contract_code !== s.far.contract_code && s.near.close > 0 && s.far.close > 0)
      check(s.near.delist_date >= s.trade_date && s.near.delist_date < s.far.delist_date && Number.isSafeInteger(s.delta_days) && s.delta_days > 0 && Number.isSafeInteger(s.near_dte_days) && s.near_dte_days >= 0)
    }
    check(p.distributions.length === 4)
    p.distributions.forEach((d, i) => {
      check(d.stage === stages[i] && d.metric === r.metric && d.unit === r.unit)
      ordered(d.candidate_dates); ordered(d.sample_dates)
      accounting(d.accounting, d.candidate_dates.length); count(d.sample_count)
      check(d.sample_count === d.sample_dates.length && d.sample_count === d.accounting.valid_count)
      const candidates = new Set(d.candidate_dates)
      check(d.candidate_dates.every(date => open.has(date)))
      check(d.sample_dates.every(date => candidates.has(date) && points.has(date) && (d.stage === 'all_stages' || points.get(date)!.expiry_stage === d.stage)))
      check(same(d.sample_dates, p.samples.filter(s => d.stage === 'all_stages' || s.expiry_stage === d.stage).map(s => s.trade_date)))
      const status = d.sample_count === 0 ? 'empty_sample' : d.sample_count < 30 ? 'small_sample' : 'available'
      check(d.status === status && (status === 'empty_sample' ? d.reason === 'no_valid_historical_observations' : d.reason === null))
      if (status === 'small_sample') check(d.warnings.length > 0)
      if (d.sample_count === 0) check(d.quantile === null)
      else {
        check(d.quantile !== null)
        const { spec, result } = d.quantile
        check(same(spec.points, probabilities) && same(result.points_and_values.map(x => x[0]), probabilities))
        check(result.sample_count === d.sample_count && result.unit === r.unit)
        check(result.points_and_values.every((x, j, xs) => j === 0 || x[1] >= xs[j - 1][1]))
      }
      if (q.histogram_edges === null) check(d.histogram_status === 'not_requested' && d.histogram === null)
      else if (d.sample_count === 0) check(d.histogram_status === 'empty_sample' && d.histogram === null)
      else {
        check(d.histogram_status === 'available' && d.histogram !== null)
        const { spec, result: h } = d.histogram
        check(same(spec.edges, q.histogram_edges) && same(h.edges, spec.edges) && spec.unit === r.unit && h.unit === r.unit && h.sample_count === d.sample_count)
        check(h.edges.length >= 2 && h.edges.every((e, j) => j === 0 || e > h.edges[j - 1]) && h.bins.length === h.edges.length - 1)
        h.bins.forEach((b, j) => { count(b.count); check(b.left === h.edges[j] && b.right === h.edges[j + 1] && b.left_inclusive && b.right_inclusive === (j === h.bins.length - 1) && b.frequency >= 0 && b.frequency <= 1) })
        count(h.underflow_count); count(h.overflow_count)
        check(h.bins.reduce((n, b) => n + b.count, h.underflow_count + h.overflow_count) === d.sample_count)
        check([h.underflow_frequency, h.overflow_frequency].every(n => n >= 0 && n <= 1))
        check(Math.abs(h.bins.reduce((n, b) => n + b.frequency, h.underflow_frequency + h.overflow_frequency) - 1) < 1e-10)
      }
    })
    const all = p.distributions[3]
    check(same(all.candidate_dates, [...open]))
    for (const k of Object.keys(totals) as (keyof typeof totals)[]) totals[k] += all.accounting[k]
    const current = r.current_day.observations[index]
    for (const kind of ['matching_stage', 'all_stages'] as const) {
      const a = p[kind]
      check(a.kind === kind)
      const stage = kind === 'all_stages' ? 'all_stages' : current?.expiry_stage ?? null
      check(a.distribution_stage === stage)
      const d = p.distributions.find(d => d.stage === stage)
      if (!current || current.outcome !== 'valid') {
        check(a.status === 'not_applicable' && a.percentile === null && a.reason === (current?.reason ?? 'non_trading_day'))
      } else {
        check(d && a.status === d.status && a.reason === d.reason && same(a.warnings, d.warnings))
        if (d.sample_count === 0) check(a.percentile === null)
        else {
          check(a.percentile !== null)
          const { spec, result } = a.percentile
          const currentValue = current.metrics![r.metric].value
          check(same(spec.queries, [currentValue]) && spec.unit === r.unit && result.unit === r.unit && result.sample_count === d.sample_count && result.query_results.length === 1)
          const rank = result.query_results[0]
          count(rank.less_count); count(rank.equal_count); count(rank.greater_count)
          check(rank.query === currentValue && rank.less_count + rank.equal_count + rank.greater_count === d.sample_count)
        }
      }
    }
  })
  check(same(totals, { candidate_count: r.historical_accounting.candidate_count, valid_count: r.historical_accounting.valid_count, excluded_count: r.historical_accounting.excluded_count, not_applicable_count: r.historical_accounting.not_applicable_count }))
  return r
}
