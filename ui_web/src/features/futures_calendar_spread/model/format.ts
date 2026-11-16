import { formatDecimal, formatInteger, formatPercent } from '../../../shared/format/number'

export const metricLabels = { signed_spread: 'Signed Spread（点）', annualized_point_spread: 'Annualized Point Spread（点 / 365 自然日）', annualized_spread_ratio: 'Annualized Spread Ratio（%）' }
export function number(value: number | null | undefined, ratio = false): string {
  if (value === null || value === undefined) return '未提供'
  return ratio ? formatPercent(value, '未提供') : formatDecimal(value, '未提供')
}
export function count(value: number | null | undefined): string {
  return formatInteger(value, '未提供')
}
export const errorMessages: Record<string, string> = {
  invalid_request: '请检查查询参数。', origin_forbidden: '请求来源被拒绝，请检查同源访问配置。', incomplete_inputs: '缓存输入尚未准备完整，请先完成数据准备。',
  request_too_large: '请求超出服务限制，请缩小日期范围或边界数量。', response_too_large: '完整结果超出服务限制，请缩小查询范围。',
  slot_resolution_error: '合约阶段解析失败。', calculation_failure: '领域计算失败。', statistical_failure: '统计执行失败。',
  input_contract_error: '上游数据不符合服务契约。', upstream_unavailable: '上游服务暂不可用。', transport_busy: '服务处理容量已满，请稍后手动重试。',
  internal_error: '服务发生内部错误。', network: '无法连接数据服务。', invalid_response: '服务返回的数据未通过完整性验证，未展示结果。',
}
