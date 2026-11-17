import { useEffect, useState, type ReactNode } from 'react'
import { Alert, Button, Spin } from 'antd'
import { InvalidBundleError } from './dataAdapter'
import type { Resource } from './resources'

type LoadState<T> = { status: 'loading' } | { status: 'ready'; data: T } | { status: 'error'; error: unknown }
export function AsyncContent<T>({ resource, children }: { resource: Resource<T>; children: (data: T) => ReactNode }) {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState<{ resource: Resource<T>; attempt: number; value: LoadState<T> }>({ resource, attempt, value: { status: 'loading' } })
  useEffect(() => {
    let active = true
    resource.load().then(data => {
      if (active) setState({ resource, attempt, value: { status: 'ready', data } })
    }, error => {
      if (active) setState({ resource, attempt, value: { status: 'error', error } })
    })
    return () => { active = false }
  }, [resource, attempt])
  const value = state.resource === resource && state.attempt === attempt ? state.value : { status: 'loading' as const }
  if (value.status === 'loading') return <Spin tip="正在加载静态展示资源…"><div style={{ minHeight: 80 }} /></Spin>
  if (value.status === 'error') return <Alert showIcon type="error"
    title={value.error instanceof InvalidBundleError ? '静态结果未通过校验，已停止展示。' : '静态资源加载失败，请重试。'}
    description="可重试或切换页面；不会调用在线服务或重新执行研究。"
    action={<Button onClick={() => setAttempt(n => n + 1)}>重试静态资源</Button>} />
  return children(value.data)
}
