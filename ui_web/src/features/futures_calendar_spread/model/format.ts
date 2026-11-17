import { formatDecimal, formatInteger, formatPercent } from '../../../shared/format/number'

export const metricLabels = { signed_spread: '价差（点）', annualized_point_spread: '年化点差（点 / 365 自然日）', annualized_spread_ratio: '年化价差比例（%）' }
export function number(value: number | null | undefined, ratio = false): string {
  if (value === null || value === undefined) return '未提供'
  return ratio ? formatPercent(value, '未提供') : formatDecimal(value, '未提供')
}
export function count(value: number | null | undefined): string {
  return formatInteger(value, '未提供')
}
export const errorMessages: Record<string, string> = {
  invalid_request: '请检查查询参数。', origin_forbidden: '请求来源被拒绝，请检查同源访问配置。', incomplete_inputs: '所需数据仍不完整，请稍后重试或联系维护人员。',
  request_too_large: '请求超出服务限制，请检查查询参数。', response_too_large: '完整结果超出服务限制，请联系维护人员。',
  slot_resolution_error: '合约阶段解析失败。', calculation_failure: '领域计算失败。', statistical_failure: '统计执行失败。',
  input_contract_error: '上游数据不符合服务契约。', upstream_unavailable: '上游服务暂不可用。', transport_busy: '服务处理容量已满，请稍后手动重试。',
  internal_error: '服务发生内部错误。', network: '无法连接数据服务。', invalid_response: '服务返回的数据未通过完整性验证，未展示结果。',
}

const reasonMessages: Record<string, string> = {
  credential_missing: '需要配置数据源凭据，请联系维护人员。',
  cache_incompatible: '数据缓存不兼容，需要维护人员处理缓存。',
  final_export_incomplete: '已尝试自动准备，但所需数据仍有缺失，请稍后重试或联系维护人员。',
  operation_unavailable: '数据准备或读取暂不可用，请稍后重试或联系维护人员。',
  malformed_export: '上游导出数据存在契约问题，请联系维护人员。',
  malformed_ensure_result: '上游数据准备结果存在契约问题，请联系维护人员。',
  upstream_request_rejected: '上游服务拒绝了有效请求，存在契约问题，请联系维护人员。',
}
export function errorMessage(error: { kind: string; reason_code?: string | null }): string {
  return (error.reason_code && reasonMessages[error.reason_code]) || errorMessages[error.kind] || errorMessages.internal_error
}

export const expiryLabels = { '0_7': '0–7 天', '8_21': '8–21 天', '22_plus': '22 天及以上' }
export const indexStatusLabels = {
  available: '已获取', non_trading_day: '当日指数休市', cache_incomplete: '缓存尚不完整',
  final_export_incomplete: '自动准备后数据仍不完整', credential_missing: '数据源凭据未配置',
  cache_incompatible: '缓存不兼容', operation_unavailable: '数据服务不可用', malformed_export: '数据契约异常',
  malformed_ensure_result: '数据准备结果异常', upstream_request_rejected: '数据请求被上游拒绝',
}
const sourceNotes: Record<string, string> = {
  'Daily SSE Calendar and Index exports are independent snapshots; the same-day index Close supplies independent Daily futures–spot comparisons, never calendar-spread or historical calculations. Reference preparation follows the selected read-only or explicit execution permission.': '每日上交所交易日历与指数导出是独立快照；同日指数收盘价用于独立期现比较，不参与跨期或历史研究计算。参考数据准备遵循所选的只读查询或显式执行权限。',
  'Daily SSE Calendar and Index exports are independent snapshots; the same-day index Close is reference-only and never enters futures calculations. Reference preparation follows the selected read-only or explicit execution permission.': '每日上交所交易日历与指数导出是独立快照；同日指数收盘价仅供参考，不参与期货计算。参考数据准备遵循所选的只读查询或显式执行权限。',
  'Calendar and Futures exports are independent snapshots with no common acquisition time or freshness guarantee.': '交易日历和期货导出是独立快照，不保证共同采集时间或数据新鲜度。',
  'Retained futures metadata is not guaranteed to have been known on the historical trade date.': '保留的期货元数据不保证在历史查询日已知。',
  'Read-only queries require separately prepared complete caches; they never ensure or repair missing data.': '只读查询需要预先准备完整缓存，不会自动准备或修复缺失数据。',
  'Explicit execution may prepare incomplete caches through DataLake public services; analysis uses validated complete final exports.': '显式查询可能通过 DataLake 公共服务准备不完整缓存；分析使用已验证的完整最终导出。',
  'Close relationships are descriptive, not executable roll quotes, forecasts or investment recommendations.': '收盘价关系仅作描述，不是可执行的移仓报价、预测或投资建议。',
  'Fees, slippage, margin, financing, dividends, future changes and waiting value are excluded.': '未计入费用、滑点、保证金、融资、股息、未来变化及等待价值。',
}
export function sourceNote(text: string): string { return sourceNotes[text] ?? text }
