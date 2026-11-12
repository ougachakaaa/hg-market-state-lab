export const percent = (value: number) => new Intl.NumberFormat('zh-CN', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(Object.is(value, -0) ? 0 : value)
export const money = (value: number) => new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY', maximumFractionDigits: 2 }).format(value)
const messages: Record<string, string> = {
  network: '网络响应丢失。提交结果可能已被服务器接受，请勿自动重发；读取操作可手动重试。',
  invalid_response: '服务器响应无效，无法安全展示。', invalid_request: '参数未通过服务器验证，请检查日期范围与策略。',
  request_too_large: '请求超过大小限制。', run_not_found: '回测不存在或无权访问。', run_busy: 'RUN_BUSY：已有回测正在执行，请稍后明确提交。',
  result_not_ready: '回测尚未完成，无法读取结果。', corrupt: '回测记录或结果损坏，无法展示。',
  result_too_large: '回测结果超过大小限制。', response_too_large: '结果响应超过大小限制。',
  unavailable: '回测服务暂不可用，请稍后重试。', read_busy: '结果读取繁忙，请手动重试。',
  internal_error: '服务器未能完成操作，请稍后重试。', origin_forbidden: '请求来源被拒绝，请从应用同源页面操作。',
}
export const errorMessage = (kind: string, submission = false) => kind === 'network' && !submission ? '网络读取失败，请手动重试。' : messages[kind] ?? '操作失败，请稍后重试。'
