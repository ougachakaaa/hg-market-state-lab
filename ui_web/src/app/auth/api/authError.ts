import type { AuthErrorResponse } from './auth'

export class AuthRequestError extends Error {
  readonly status: number | 'network' | 'invalid_response'
  readonly retryAfter: string | null
  readonly response?: AuthErrorResponse

  constructor(
    status: number | 'network' | 'invalid_response',
    retryAfter: string | null = null,
    response?: AuthErrorResponse,
  ) {
    super('Authentication request failed')
    this.status = status
    this.retryAfter = retryAfter
    this.response = response
  }
}

export function authErrorMessage(error: unknown): string {
  if (!(error instanceof AuthRequestError)) return '认证服务暂时不可用，请重试。'
  switch (error.status) {
    case 400: return '输入请求不合法，请检查输入。'
    case 401: return '用户名或密码错误。'
    case 403: return '请求来源被拒绝，请从配置的应用地址访问。'
    case 429: return `请求过于频繁，请稍后重试。${error.retryAfter ? `等待 ${error.retryAfter} 秒后重试。` : ''}`
    case 'network': return '连接认证服务失败，请重试。'
    case 'invalid_response': return '认证服务返回了不符合契约的响应，请重试。'
    default: return '认证服务暂时不可用，请重试。'
  }
}
