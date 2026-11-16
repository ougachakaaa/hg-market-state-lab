export const metricLabels = { signed_spread: 'Signed Spread（点）', annualized_point_spread: 'Annualized Point Spread（点 / 365 自然日）', annualized_spread_ratio: 'Annualized Spread Ratio（%）' }
export function number(value: number | null | undefined, ratio = false): string {
  if (value === null || value === undefined) return '未提供'
  return ratio ? `${(value * 100).toLocaleString('zh-CN', { maximumFractionDigits: 6 })}%` : value.toLocaleString('zh-CN', { maximumFractionDigits: 6 })
}
export const errorMessages: Record<string, string> = {
  invalid_request: '请检查查询参数。', origin_forbidden: '请求来源被拒绝，请检查同源访问配置。', incomplete_inputs: '所需数据仍不完整，请稍后重试或联系维护人员。',
  request_too_large: '请求超出服务限制，请缩小日期范围或边界数量。', response_too_large: '完整结果超出服务限制，请缩小查询范围。',
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
