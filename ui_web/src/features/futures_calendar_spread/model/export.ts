import type { Result } from '../api/validateResult'
import { serializeJson } from '../../../shared/clipboard/text'
import { serializeCsv } from '../../../shared/csv/csv'
import { safeDownloadFilename } from '../../../shared/download/download'

export const historicalReferenceNote = '历史数据包未提供指数参考信息'
export const historicalSpotNote = '历史数据包未提供期现比较结果'
export function contextJson(result: Result): string {
  return serializeJson({
    format_version: 'daily-data-context-v1',
    metadata: {
      product: 'Futures Calendar Spread',
      response_identity: { case: result.case, definition_version: result.definition_version, operation: result.request.operation, product_code: result.request.product_code, trade_date: result.request.trade_date },
      reading_notes: [
        '价格使用真实合约的同日收盘价。',
        '跨期价差为近端收盘价减远端收盘价，年化分母为两份合约最后交易日间隔。',
        '期现价差为期货收盘价减同日指数收盘价，年化分母为期货剩余自然日数；到期日仅点差适用。',
        '年化价差是价格关系，不代表实际收益率或交易指令。',
        '期限差及近端剩余到期天数按自然日和实际最后交易日计量。',
        '零值与 null 不同，null 表示未提供，不能补零。',
        '指数收盘价为同日期现比较参考，不回退到其他日期或价格。',
        ...(!Object.hasOwn(result, 'futures_spot_comparisons') ? [historicalSpotNote] : []),
        ...(!Object.hasOwn(result, 'underlying_index') ? [historicalReferenceNote] : []),
      ],
    },
    data: result,
  })
}
export const csvHeader = [
  'case', 'definition_version', 'product_code', 'trade_date', 'day_status', 'day_reason',
  'comparison_type', 'comparison_definition_version', 'slot_a', 'slot_b',
  'instrument_a_type', 'instrument_a_code', 'instrument_a_close', 'instrument_a_delist_date',
  'instrument_b_type', 'instrument_b_code', 'instrument_b_close', 'instrument_b_delist_date',
  'delta_days', 'remaining_days', 'expiry_stage', 'signed_spread', 'annualized_point_spread', 'annualized_spread_ratio',
  'outcome', 'reason', 'failure_category', 'underlying_index_present', 'underlying_index_code',
  'underlying_index_trade_date', 'underlying_index_close', 'underlying_index_availability',
  'underlying_index_reason_code', 'underlying_index_failure_category', 'futures_spot_comparisons_present',
] as const
export function resultCsv(result: Result): string {
  const ref = result.underlying_index
  const prefix = [result.case, result.definition_version, result.request.product_code, result.request.trade_date, result.day.status, result.day.reason]
  const suffix = [Object.hasOwn(result, 'underlying_index'), ref?.index_code ?? null, ref?.trade_date ?? null, ref?.close ?? null,
    ref?.availability ?? null, ref?.reason_code ?? null, ref?.failure_category ?? null, Object.hasOwn(result, 'futures_spot_comparisons')]
  const calendar = result.day.observations.map(o => [
    ...prefix, 'calendar_spread', result.definition_version, o.near_slot, o.far_slot,
    'futures', o.near?.contract_code ?? null, o.near?.close ?? null, o.near?.delist_date ?? null,
    'futures', o.far?.contract_code ?? null, o.far?.close ?? null, o.far?.delist_date ?? null,
    o.delta_days, o.near_dte_days, o.expiry_stage, o.metrics?.signed_spread.value ?? null,
    o.metrics?.annualized_point_spread.value ?? null, o.metrics?.annualized_spread_ratio.value ?? null,
    o.outcome, o.reason, null, ...suffix,
  ])
  const spot = (result.futures_spot_comparisons ?? []).map(o => [
    ...prefix, 'futures_spot', o.definition_version, o.slot, null,
    'futures', o.futures?.contract_code ?? null, o.futures?.close ?? null, o.futures?.delist_date ?? null,
    'index', o.underlying_index.index_code, o.underlying_index.close, null,
    null, o.remaining_days, o.expiry_stage, o.signed_spread, o.annualized_point_spread, o.annualized_spread_ratio,
    o.outcome, o.reason, o.failure_category, ...suffix,
  ])
  return serializeCsv(csvHeader, [...calendar, ...spot])
}
export function exportFilename(result: Result, context = false): string {
  return safeDownloadFilename(`futures-calendar-spread_${result.request.product_code}_${result.request.trade_date}${context ? '_context.json' : '.csv'}`)
}
