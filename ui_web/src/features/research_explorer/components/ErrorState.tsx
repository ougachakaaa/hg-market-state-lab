import { ReloadOutlined } from '@ant-design/icons'
import { Alert, Button } from 'antd'
import type { ResearchExplorerMode } from '../model/explorerPresentation'
import { ResearchError, type FailureKind } from '../model/failures'

const messages: Record<FailureKind, string> = {
  invalid_request: '请求无效或游标已失效。', not_found: '未找到所选 Publication、Analysis 或 View。',
  corrupt: '已存储的内容无效或损坏。', inconsistent: 'Publication 的证据关联不一致。',
  unsupported_version: '不支持此存储版本。', response_too_large: '响应超过大小限制。',
  verification_budget_exceeded: '来源验证容量不足，请稍后手动重试。', unavailable: 'Publication 存储或来源不可用。',
  internal_error: '服务内部错误。', authentication_required: '需要登录。', invalid_credentials: '认证失败。',
  origin_forbidden: '访问被拒绝。', rate_limited: '请求过于频繁。', network: '无法连接服务。',
  invalid_response: '服务返回了无法识别的响应。', invalid_view: 'ChartView 格式无效或不兼容。',
}

export function ErrorState({ error, retry, context, mode }: {
  error: unknown
  retry?: () => void
  context: string
  mode: ResearchExplorerMode
}) {
  return <Alert type="error" showIcon
    title={error instanceof ResearchError && error.kind === 'not_found'
      ? `未找到所选 ${context}。`
      : error instanceof ResearchError ? messages[error.kind] : '请求失败。'}
    action={mode === 'production' && retry
      ? <Button icon={<ReloadOutlined aria-hidden="true" />} onClick={retry}>重试</Button>
      : undefined} />
}
