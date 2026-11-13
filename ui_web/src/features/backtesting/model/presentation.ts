import type { Preflight, Run } from '../api/backtesting'

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

export const dependencyLabels: Record<string, string> = {
 calendar_cffex: 'CFFEX 交易日历', calendar_sse: 'SSE 交易日历', futures: '股指期货日线', index: '指数日线',
}
export const credentialAction = '请在项目根目录的 `.env` 文件中配置 `TUSHARE_TOKEN`。如果进程环境变量中存在同名空值，它会覆盖 `.env`。完成配置后重启后端，再重新提交回测。'
type Failure = NonNullable<Run['failure']>
export function failurePresentation(status: string, failure?: Failure | null) {
 if (status === 'INTERRUPTED') return { title: '回测执行已中断', description: '上一次执行被中断，未生成成功结果。', action: '确认后端服务可用后，重新提交回测。' }
 if (failure?.stage === 'ensure' && failure.category === 'upstream_operation' && failure.reason === 'credential_missing') return { title: '行情数据获取失败', description: `无法获取 ${dependencyLabels[failure.dependency ?? ''] ?? '所需行情数据'}，因为后端未配置 Tushare Token。`, action: credentialAction }
 if (failure?.category === 'upstream_operation') return { title: '行情数据获取失败', description: '行情数据获取失败。请检查后端数据源配置和网络连接，或稍后重试。', action: '确认后端数据源可用后，重新提交回测。' }
 if (failure?.category === 'incomplete_input') return { title: '必要行情尚不完整', description: `所选时间范围内的必要行情仍不完整，暂时无法生成回测结果。${failure.dependency ? `涉及：${dependencyLabels[failure.dependency] ?? '所需行情数据'}。` : ''}`, action: '检查本地缓存和后端数据源配置后，重新提交回测。' }
 return { title: '回测执行失败', description: '回测执行失败。请查看技术详情或联系维护人员。', action: '确认问题解决后，重新提交回测。' }
}
export function readinessPresentation(item: Preflight['calendar_cffex']) {
 const labels = { complete: '数据已就绪', incomplete: '本地缓存不完整', unknown: '暂无法判断', unavailable: '缓存检查不可用' }
 const reasons = { cache_complete: '本地目标缓存完整，不代表行情最新或回测一定成功。', cache_incomplete: '提交回测时将尝试自动获取缺失行情。', calendar_target_unknown: 'CFFEX 交易日历尚不完整或无法读取，暂无法确定下游所需日期。', underlying_unknown: '尚无法确定标的指数，暂无法检查指数缓存。', public_export_unavailable: '暂无法检查本地缓存，请稍后重新检查。' }
 const unit = item.dependency.startsWith('calendar_') ? '个自然日目标' : item.dependency === 'futures' ? '个产品×日期目标' : '个指数×日期目标'
 return { label: labels[item.state], description: reasons[item.reason] ?? '暂无法判断缓存准备情况。', coverage: item.coverage ? `已缓存 ${item.coverage.successful_units} / ${item.coverage.requested_units} ${unit}` : undefined }
}
