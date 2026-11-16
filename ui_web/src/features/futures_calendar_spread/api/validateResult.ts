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
const operation = openapi.paths['/data/futures-calendar-spread'].get
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
  day(r.day, r.request.product_code); accounting(r.accounting, r.day.observations.length)
  for (const outcome of ['valid', 'excluded', 'not_applicable'] as const) check(r.accounting[`${outcome}_count`] === r.day.observations.filter(o => o.outcome === outcome).length)
  return r
}
