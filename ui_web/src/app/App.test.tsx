import { afterEach, describe, expect, it, vi } from 'vitest'
import { StrictMode } from 'react'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'

vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))

const identity = { id: 'test-user', username: 'alice', status: 'active' }
const response = (body: unknown, status = 200) => new Response(status === 204 ? null : JSON.stringify(body), { status })
const unauthorized = () => response({ error: { kind: 'authentication_required', detail: 'Error', param: null } }, 401)
function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => { resolve = done })
  return { promise, resolve }
}
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); window.history.replaceState(null, '', '/') })

async function submitLogin() {
  fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'synthetic password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Login' }))
}

describe('workspace shell and authentication', () => {
  it('shows only the gate while checking and on anonymous deep links', async () => {
    window.history.replaceState(null, '', '/data/mo-option-chain')
    const pending = deferred<Response>()
    const fetch = vi.fn((_url: string) => pending.promise)
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    expect(screen.getByText('正在检查登录状态…')).toBeTruthy()
    expect(screen.queryByText('Daily Data overview')).toBeNull()
    pending.resolve(unauthorized())
    await screen.findByRole('button', { name: 'Login' })
    expect(window.location.pathname).toBe('/data/mo-option-chain')
    expect(fetch.mock.calls[0][0]).toBe('/auth/me')
  })

  it('logs in at root to Research', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(unauthorized()).mockResolvedValueOnce(response(identity)))
    render(<App />)
    await screen.findByRole('button', { name: 'Login' })
    await submitLogin()
    await screen.findByRole('button', { name: 'Research Workspace' })
    expect(window.location.pathname).toBe('/research')
  })

  it('restores deep route, navigates with history and logs out', async () => {
    window.history.replaceState(null, '', '/backtesting')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(identity)).mockResolvedValueOnce(response(null, 204)))
    render(<App />)
    await screen.findByText(/策略模拟与历史验证尚未实现/)
    expect(window.location.pathname).toBe('/backtesting')
    fireEvent.click(screen.getByRole('button', { name: 'Research Workspace' }))
    expect(window.location.pathname).toBe('/research')
    await act(async () => { window.history.replaceState(null, '', '/backtesting'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await waitFor(() => expect(screen.getByText(/策略模拟与历史验证尚未实现/)).toBeTruthy())
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }))
    await screen.findByRole('button', { name: 'Login' })
    expect(screen.queryByText('alice')).toBeNull()
  })

  it('keeps logout failure explicit and retryable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(unauthorized()).mockResolvedValueOnce(response(identity))
      .mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(response(null, 204)))
    render(<App />)
    await screen.findByRole('button', { name: 'Login' })
    await submitLogin()
    fireEvent.click(await screen.findByRole('button', { name: 'Logout' }))
    fireEvent.click(await screen.findByRole('button', { name: '重试退出' }))
    await screen.findByRole('button', { name: 'Login' })
  })

  it('normalizes an unknown history destination to Research', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(identity)))
    render(<App />)
    await screen.findByRole('button', { name: 'Logout' })
    await act(async () => { window.history.pushState(null, '', '/unknown'); window.dispatchEvent(new PopStateEvent('popstate')) })
    expect(window.location.pathname).toBe('/research')
  })
})

describe('integrated feature routes', () => {
  it('opens all three pages and restores a direct Explorer URL', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response(identity)).mockResolvedValueOnce(response({ data: [], next_cursor: null }))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Research Explorer →' }))
    await screen.findByText('Publication Store 为空。')
    expect(window.location.pathname).toBe('/research/publications')
    expect(fetch.mock.calls[1][0]).toBe('/api/research/publications')
    fireEvent.click(screen.getByRole('button', { name: 'Daily Data overview' }))
    expect(window.location.pathname).toBe('/data')
    fireEvent.click(screen.getByRole('button', { name: 'MO Option Chain →' }))
    await screen.findByRole('heading', { name: 'MO 期权链' })
    expect(window.location.pathname).toBe('/data/mo-option-chain')
    fireEvent.click(screen.getByText('MO Premium Plane', { selector: '.ant-menu-title-content' }))
    await screen.findByRole('heading', { name: 'MO 年化权利金平面' })
    expect(window.location.pathname).toBe('/data/mo-premium-plane')
    await act(async () => { window.history.replaceState(null, '', '/research/publications'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await screen.findByRole('heading', { name: 'Research Explorer' })
  })

  it('returns to the gate on a feature 401 and isolates its result', async () => {
    window.history.replaceState(null, '', '/data/mo-option-chain')
    const fetch = vi.fn().mockResolvedValueOnce(response(identity)).mockResolvedValueOnce(unauthorized())
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await screen.findByRole('heading', { name: 'MO 期权链' })
    fireEvent.change(screen.getByLabelText('目标交易日'), { target: { value: '2026-09-21' } })
    await screen.findByRole('button', { name: 'Login' })
    expect(screen.queryByRole('heading', { name: 'MO 期权链' })).toBeNull()
    expect(screen.queryByText('alice')).toBeNull()
  })

  it('aborts a pending Explorer request on logout', async () => {
    window.history.replaceState(null, '', '/research/publications')
    const old = deferred<Response>()
    let signal: AbortSignal | undefined
    const fetch = vi.fn().mockResolvedValueOnce(response(identity))
      .mockImplementationOnce((_url, init) => { signal = init.signal; return old.promise })
      .mockResolvedValueOnce(response(null, 204))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await waitFor(() => expect(signal).toBeDefined())
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }))
    expect(signal?.aborted).toBe(true)
    await screen.findByRole('button', { name: 'Login' })
    old.resolve(response({ data: [{ publication_id: 'stale', status: 'success' }], next_cursor: null }))
    expect(screen.queryByText('stale')).toBeNull()
  })
})

describe('authentication regressions across the workspace', () => {
  it('registers without opening the workspace', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(unauthorized())
      .mockResolvedValueOnce(response({ message: 'Registration request accepted.' }, 202))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Register' }))
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'synthetic password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Submit Registration' }))
    await screen.findByText('注册申请已提交，请等待管理员审批后登录。')
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/me', '/auth/register'])
    expect(screen.queryByText('Research Workspace')).toBeNull()
  })

  it.each([
    [401, '用户名或密码错误。'], [400, '输入请求不合法，请检查输入。'],
    [403, '请求来源被拒绝，请从配置的应用地址访问。'],
    [429, '请求过于频繁，请稍后重试。'], [500, '认证服务暂时不可用，请重试。'],
  ])('shows login HTTP %i without opening the workspace', async (status, message) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(unauthorized())
      .mockResolvedValueOnce(response({ error: { kind: 'invalid_credentials', detail: '', param: null } }, status)))
    render(<App />)
    await screen.findByRole('button', { name: 'Login' })
    await submitLogin()
    await screen.findByText(message)
    expect(screen.queryByText('alice')).toBeNull()
  })

  it.each(['network', 'server'])('retries a startup %s failure', async (kind) => {
    const fetch = vi.fn()
    if (kind === 'network') fetch.mockRejectedValueOnce(new TypeError('offline'))
    else fetch.mockResolvedValueOnce(response({ error: { kind: 'internal_error', detail: '', param: null } }, 500))
    fetch.mockResolvedValueOnce(response(identity))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '重试登录状态检查' }))
    await screen.findByRole('button', { name: 'Logout' })
  })

  it.each([403, 429, 500])('keeps the gate open for business HTTP %i', async (status) => {
    window.history.replaceState(null, '', '/data/mo-option-chain')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(identity))
      .mockResolvedValueOnce(response({ error: { kind: 'internal_error', detail: '', param: null } }, status)))
    render(<App />)
    await screen.findByRole('heading', { name: 'MO 期权链' })
    fireEvent.change(screen.getByLabelText('目标交易日'), { target: { value: '2026-09-21' } })
    await screen.findByRole('alert')
    expect(screen.getByRole('button', { name: 'Logout' })).toBeTruthy()
  })

  it('isolates an obsolete StrictMode identity response', async () => {
    const obsolete = deferred<Response>()
    const latest = deferred<Response>()
    const fetch = vi.fn().mockReturnValueOnce(obsolete.promise).mockReturnValueOnce(latest.promise)
    vi.stubGlobal('fetch', fetch)
    render(<StrictMode><App /></StrictMode>)
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
    latest.resolve(response(identity))
    await screen.findByRole('button', { name: 'Logout' })
    obsolete.resolve(unauthorized())
    expect(screen.getByText('alice')).toBeTruthy()
  })
})
