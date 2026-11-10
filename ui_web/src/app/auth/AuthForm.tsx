import { Alert, Button, Card, Flex, Form, Input, Typography, theme } from 'antd'
import { useEffect, useRef, useState } from 'react'
import { register } from './api/auth'
import type { LoginRequest } from './api/auth'
import { authErrorMessage } from './api/authError'

export default function AuthForm({ signIn }: { signIn: (credentials: LoginRequest) => Promise<void> }) {
  const { token } = theme.useToken()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string>()
  const [accepted, setAccepted] = useState(false)
  const request = useRef<AbortController | null>(null)
  const alive = useRef(true)
  useEffect(() => {
    alive.current = true
    return () => { alive.current = false; request.current?.abort() }
  }, [])
  const submit = async (values: LoginRequest) => {
    setPending(true)
    setError(undefined)
    const controller = new AbortController()
    request.current = controller
    try {
      if (mode === 'login') await signIn(values)
      else {
        await register(values, controller.signal)
        if (alive.current) setAccepted(true)
      }
    } catch (error) {
      if (alive.current && !controller.signal.aborted) setError(authErrorMessage(error))
    } finally {
      if (alive.current) setPending(false)
    }
  }
  return <Flex justify="center" align="center" style={{ minHeight: '100vh', padding: 24,
    boxSizing: 'border-box', background: token.colorBgLayout }}>
    <Card style={{ width: '100%', maxWidth: 420 }}>
      <Typography.Title level={1} style={{ fontSize: 24, marginTop: 0 }}>{mode === 'login' ? '登录' : '注册'}</Typography.Title>
      <Typography.Paragraph>Market State Lab</Typography.Paragraph>
      {error && <Alert type="error" title={error} showIcon />}
      {accepted ? <Alert type="success" title="注册申请已提交，请等待管理员审批后登录。" showIcon /> :
        <Form key={mode} layout="vertical" size="middle" onFinish={submit} disabled={pending}>
          <Form.Item name="username" label="用户名" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
          </Form.Item>
          {mode === 'register' && <Typography.Paragraph>用户名为 3–64 个 ASCII 字符；密码为 12–128 个字符。</Typography.Paragraph>}
          <Button type="primary" htmlType="submit" loading={pending} block>{mode === 'login' ? '登录' : '提交注册申请'}</Button>
        </Form>}
      <Button type="link" disabled={pending} onClick={() => {
        setMode(mode === 'login' ? 'register' : 'login'); setError(undefined); setAccepted(false)
      }}>{mode === 'login' ? '注册' : '返回登录'}</Button>
    </Card>
  </Flex>
}
