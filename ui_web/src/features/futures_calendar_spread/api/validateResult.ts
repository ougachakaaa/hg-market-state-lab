import Ajv2020 from 'ajv/dist/2020.js'
import openapi from './calendarSpread.openapi.json'
import type { components } from './calendarSpread.generated'

type S = components['schemas']
export type ErrorResult = S['DailyErrorResponse'] | S['AuthErrorResponse']
export type Result = S['DailyResponse']
export type Query = Pick<S['DailyEcho'], 'product_code' | 'trade_date'>
export const pairs = ['M0/M1', 'M0/Q1', 'M0/Q2', 'M1/Q1', 'M1/Q2', 'Q1/Q2'] as const
export const products = ['IF', 'IH', 'IC', 'IM'] as const
export const units = { signed_spread: 'index_points', annualized_point_spread: 'index_points_per_365_natural_days', annualized_spread_ratio: 'decimal_ratio' } as const
const ajv = new Ajv2020({ strictSchema: false, strictTypes: false, strictNumbers: true, formats: {
  date: (v: string) => /^\d{4}-\d{2}-\d{2}$/.test(v) && v >= '0001-01-01' && Number.isFinite(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v,
} })
const schema = ajv.compile({ ...openapi.components.schemas.DailyResponse, components: openapi.components })
const operation = openapi.paths['/data/futures-calendar-spread/query'].post
const responses = new Map(Object.entries(operation.responses).map(([status, response]) => [Number(status), ajv.compile({ ...response.content['application/json'].schema, components: openapi.components })]))
export const matchesResponse = (status: number, value: unknown) => responses.get(status)?.(value) === true
function check(ok: unknown): asserts ok { if (!ok) throw new Error('Invalid Calendar Spread result association') }
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

export function validateResult(value: unknown, query?: Query): Result {
  check(schema(value)); const r = value as Result
  if (query) check(r.request.product_code === query.product_code && r.request.trade_date === query.trade_date)
  check(r.day.trade_date === r.request.trade_date)
  if (Object.hasOwn(r, 'underlying_index')) {
    const ref = r.underlying_index!
    const indexCodes = { IF: '000300.SH', IH: '000016.SH', IC: '000905.SH', IM: '000852.SH' }
    check(ref.index_code === indexCodes[r.request.product_code] && ref.trade_date === r.request.trade_date)
    const states: Record<string, readonly [string, string | null]> = {
      non_trading_day: ['not_applicable', null], cache_incomplete: ['unavailable', null],
      final_export_incomplete: ['error', 'incomplete_inputs'],
      credential_missing: ['error', 'upstream_unavailable'], cache_incompatible: ['error', 'upstream_unavailable'], operation_unavailable: ['error', 'upstream_unavailable'],
      malformed_export: ['error', 'input_contract_error'], malformed_ensure_result: ['error', 'input_contract_error'], upstream_request_rejected: ['error', 'input_contract_error'],
    }
    if (ref.availability === 'available') check(ref.close !== null && ref.reason_code === null && ref.failure_category === null)
    else {
      const state = ref.reason_code === null ? undefined : states[ref.reason_code]
      check(ref.close === null && state && ref.availability === state[0] && ref.failure_category === state[1])
    }
  }
  if (Object.hasOwn(r, 'futures_spot_comparisons')) {
    check(Object.hasOwn(r, 'underlying_index'))
    const items = r.futures_spot_comparisons!
    const slots = r.day.status === 'open' ? ['M0', 'M1', 'Q1', 'Q2'] : []
    check(items.length === slots.length)
    items.forEach((item, i) => {
      check(item.slot === slots[i] && item.product_code === r.request.product_code && item.trade_date === r.request.trade_date)
      const ref = item.underlying_index
      for (const key of ['index_code', 'trade_date', 'close', 'availability', 'reason_code', 'failure_category'] as const) check(ref[key] === r.underlying_index![key])
      for (const pair of r.day.observations) {
        const contract = pair.near_slot === item.slot ? pair.near : pair.far_slot === item.slot ? pair.far : undefined
        if (contract !== undefined) {
          check((contract === null) === (item.futures === null))
          if (contract && item.futures) for (const key of ['contract_code', 'close', 'delist_date'] as const) check(contract[key] === item.futures[key])
        }
      }
      const metrics = [item.signed_spread, item.annualized_point_spread, item.annualized_spread_ratio]
      if (item.futures === null) {
        check(item.outcome === 'not_applicable' && item.reason === 'no_active_contract' && item.failure_category === null && item.remaining_days === null && item.expiry_stage === null && metrics.every(m => m === null))
        return
      }
      check(Number.isSafeInteger(item.remaining_days) && item.remaining_days! >= 0 && item.futures.delist_date >= item.trade_date && item.expiry_stage !== null)
      if (ref.availability !== 'available') check(item.outcome === 'not_applicable' && item.reason === 'index_reference_unavailable' && item.failure_category === ref.failure_category && metrics.every(m => m === null))
      else if (item.futures.close <= 0 || ref.close! <= 0) check(item.outcome === 'excluded' && item.reason === 'nonpositive_close' && item.failure_category === null && metrics.every(m => m === null))
      else if (item.outcome === 'error') check(item.reason === 'calculation_failure' && item.failure_category === 'calculation_failure' && metrics.every(m => m === null))
      else if (item.remaining_days === 0) check(item.outcome === 'not_applicable' && item.reason === 'expiry_day' && item.failure_category === null && item.signed_spread !== null && item.annualized_point_spread === null && item.annualized_spread_ratio === null)
      else check(item.outcome === 'valid' && item.reason === null && item.failure_category === null && metrics.every(m => m !== null))
    })
  }
  day(r.day, r.request.product_code); accounting(r.accounting, r.day.observations.length)
  for (const outcome of ['valid', 'excluded', 'not_applicable'] as const) check(r.accounting[`${outcome}_count`] === r.day.observations.filter(o => o.outcome === outcome).length)
  return r
}
