import Ajv from 'ajv'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { registry } from '../build/registry'
import presets from '../build/presets.json'
import { parseStrict } from '../build/json'
import { validateDirectory } from '../build/validate'
import schema from './requirements.schema.json'

type Rule = { request: Record<string, unknown>; content: string; coverage?: { first: string; last: string } }
type Requirements = { format: string; bundles: Record<string, Rule> }
// Formal DTO validation is performed by Admission, before these content predicates.
type Value = any // eslint-disable-line @typescript-eslint/no-explicit-any
function check(ok: unknown, id: string, requirement: string): asserts ok {
  if (!ok) throw new Error(`FAIL ${id} release ${requirement}`)
}
const equal = (a: unknown, b: unknown): boolean => JSON.stringify(a) === JSON.stringify(b)
function match(actual: Value, expected: Record<string, unknown>, id: string) {
  for (const [key, value] of Object.entries(expected)) check(actual?.[key] === value, id, `request.${key}`)
}
function views(value: Value): Value[] {
  if (!value || typeof value !== 'object') return []
  if (Array.isArray(value.layers)) return [value]
  return Object.values(value).flatMap(views)
}
function dates(values: string[], rule: Rule, id: string) {
  check(values.length && values[0] === rule.coverage!.first && values.at(-1) === rule.coverage!.last, id, 'actual_coverage')
  check(values.every((date, i) => date >= String(rule.request.start_date) && date <= String(rule.request.end_date) && (!i || date > values[i - 1])), id, 'ordered_actual_dates')
}
export async function validateRelease(web: string, directory = resolve(web, 'demo/bundles'), requirements = resolve(web, 'demo/release/requirements.json')) {
  const read = async (path: string) => parseStrict(await readFile(path, 'utf8'))
  const raw = await read(requirements)
  check(new Ajv({ strict: true }).compile(schema)(raw), 'dataset', 'requirements_schema')
  const rules = (raw as unknown as Requirements).bundles
  check(equal(Object.keys(rules).sort(), registry.map(r => r.bundle_id).sort()), 'dataset', 'registry_membership')
  for (const entry of registry) {
    const rule = rules[entry.bundle_id]
    match(presets[entry.preset_id].request, rule.request, entry.bundle_id)
    check(Object.keys(presets[entry.preset_id].request).length === Object.keys(rule.request).length, entry.bundle_id, 'preset_fields')
  }
  await validateDirectory(directory)
  const bundles: Record<string, Value> = {}
  for (const entry of registry) bundles[entry.bundle_id] = await read(resolve(directory, entry.path))
  for (const entry of registry) {
    const id = entry.bundle_id, rule = rules[id], bundle = bundles[id], result = bundle.result
    match(bundle.request, rule.request, id)
    if (rule.content === 'basis' || rule.content === 'backtest') {
      check(result.status === 'complete', id, 'complete_result')
      const domain = rule.content === 'basis' ? result.candidate_dates : result.daily.map((row: Value) => row.trade_date)
      dates(domain, rule, id)
      const coverage = rule.content === 'basis' ? Object.values(result.coverage) : result.evidence.coverage
      check(coverage.length && coverage.every((item: Value) => item.complete === true && item.missing_units === 0 && item.failed_units === 0 && item.pending_units === 0), id, 'complete_source_coverage')
      if (rule.content === 'backtest') {
        match(result.request, rule.request, id)
        check(equal(domain, bundles.basis.result.candidate_dates), id, 'daily_candidate_domain')
        check(result.window.first_session === domain[0] && result.window.last_session === domain.at(-1) && result.window.cffex_session_count === domain.length, id, 'window_domain')
      }
      const charts = views(result.views)
      check(charts.length && charts.some(view => view.layers.some((layer: Value) => layer.layer.data.some((point: Value) => typeof point.y === 'number' && Number.isFinite(point.y)))), id, 'meaningful_visualization')
      for (const view of charts) for (const layer of view.layers) {
        if (layer.layer.x.kind === 'date') check(layer.layer.data.every((point: Value) => domain.includes(point.x)), id, 'visualization_date_domain')
      }
    } else if (rule.content === 'calendar_spread_daily') {
      check(result.day.status === 'open' && result.day.trade_date === rule.request.trade_date, id, 'actual_daily_date')
      check(result.day.observations.length === 6 && result.day.observations.every((row: Value) => row.outcome === 'valid' && row.near && row.far && row.metrics), id, 'six_valid_market_pairs')
    } else if (rule.content === 'calendar_spread_relative_value') {
      check(result.current_day.status === 'open' && result.current_day.observations.every((row: Value) => row.outcome === 'valid'), id, 'valid_current_observations')
      for (const pair of result.pairs) {
        const all = pair.distributions.find((d: Value) => d.stage === 'all_stages')
        check(pair.samples.length >= 30 && all.sample_count === pair.samples.length && all.quantile !== null, id, 'meaningful_historical_series')
        check(pair.samples.every((row: Value) => row.trade_date >= result.request.history_start && row.trade_date < result.request.evaluation_date), id, 'historical_cutoff')
        check(pair.all_stages.percentile !== null && pair.matching_stage.percentile !== null, id, 'current_comparisons')
      }
    } else if (rule.content === 'chain') {
      check(result.expiries.length && result.expiries.some((expiry: Value) => expiry.calls.length || expiry.puts.length), id, 'nonempty_market_results')
    } else if (rule.content === 'premium') check(result.expiries.length && result.points.length, id, 'nonempty_market_results')
    else if (rule.content === 'catalog') check(result.list.length > 0, id, 'nonempty_capabilities')
  }
  console.log(`PASS Release Requirements ${registry.length} Bundles`)
}
export async function main(args: string[], web: string) {
  if (args.length) throw new Error('FAIL dataset release invalid_arguments')
  await validateRelease(web)
  return 0
}
