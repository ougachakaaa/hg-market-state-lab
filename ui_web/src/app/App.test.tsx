import { StrictMode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'

vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))
const identity = { id: 'test-user', username: 'alice', status: 'active' }
const response = (body: unknown, status = 200, headers = {}) => new Response(
  status === 204 ? null : JSON.stringify(body), { status, headers },
)
const authError = (status: number) => response({ error: {
  kind: status === 401 ? 'authentication_required' : 'internal_error', detail: 'Error', param: null,
} }, status)
function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => { resolve = done })
  return { promise, resolve }
}
async function loggedIn() {
  await screen.findByRole('heading', { name: 'MO 期权链' })
}
async function loginForm() { await screen.findByRole('button', { name: 'Login' }) }
async function submit(button = 'Login') {
  fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'alice' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'synthetic password' } })
  fireEvent.click(screen.getByRole('button', { name: button }))
}
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('application authentication lifecycle', () => {
  it('gates business surfaces until me finishes, then shows Login for 401', async () => {
    const initial = deferred<Response>()
    const fetch = vi.fn((_url: string) => initial.promise)
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    expect(screen.getByText('正在检查登录状态…')).toBeTruthy()
    expect(screen.queryByLabelText('目标交易日')).toBeNull()
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch.mock.calls[0][0]).toBe('/auth/me')
    initial.resolve(authError(401))
    await loginForm()
    expect(screen.queryByRole('button', { name: 'Logout' })).toBeNull()
  })

  it('restores Cookie identity on mount and refresh; preserves sibling navigation/state boundaries', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve(response(identity))))
    const first = render(<App />)
    await loggedIn()
    expect(screen.getByText('alice')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'MO Premium Plane' }))
    expect(screen.getByRole('heading', { name: 'MO 年化权利金平面' })).toBeTruthy()
    fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-21' } })
    fireEvent.click(screen.getByRole('button', { name: 'MO Option Chain' }))
    fireEvent.click(screen.getByRole('button', { name: 'MO Premium Plane' }))
    expect((screen.getByLabelText('Observation 日期') as HTMLInputElement).value).toBe('')
    first.unmount()
    render(<App />)
    await loggedIn()
  })

  it('navigates to Research Explorer and isolates its 401 at the application gate', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response(identity)).mockResolvedValueOnce(authError(401))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await loggedIn()
    fireEvent.click(screen.getByRole('button', { name: 'Research Explorer' }))
    await loginForm()
    expect(fetch.mock.calls[1][0]).toBe('/research/publications')
    expect(screen.queryByRole('heading', { name: 'Research Explorer' })).toBeNull()
  })

  it('logs in to default Option Chain without persisting tokens', async () => {
    const local = vi.spyOn(Storage.prototype, 'setItem')
    const fetch = vi.fn().mockResolvedValueOnce(authError(401)).mockResolvedValueOnce(response(identity))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await loginForm()
    await submit()
    await loggedIn()
    expect(fetch.mock.calls[1][0]).toBe('/auth/login')
    expect(fetch.mock.calls[1][1].credentials).toBe('same-origin')
    expect(local).not.toHaveBeenCalled()
  })

  it('registers with 202 and waits for approval without logging in', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(authError(401))
      .mockResolvedValueOnce(response({ message: 'Registration request accepted.' }, 202))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await loginForm()
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))
    await submit('Submit Registration')
    await screen.findByText('注册申请已提交，请等待管理员审批后登录。')
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/me', '/auth/register'])
    expect(screen.queryByRole('button', { name: 'MO Option Chain' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: '返回 Login' }))
    await loginForm()
  })

  it.each([
    [401, '用户名或密码错误。'], [400, '输入请求不合法，请检查输入。'],
    [403, '请求来源被拒绝，请从配置的应用地址访问。'],
    [429, '请求过于频繁，请稍后重试。等待 42 秒后重试。'],
    [500, '认证服务暂时不可用，请重试。'], [418, '认证服务暂时不可用，请重试。'],
  ])('presents login HTTP %i without inferring account status', async (status, message) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(authError(401))
      .mockResolvedValueOnce(response({}, status, { 'Retry-After': '42' })))
    render(<App />)
    await loginForm()
    await submit()
    await screen.findByText(message)
    expect(screen.queryByText('alice')).toBeNull()
  })

  it.each(['network', 'server'])('offers retry for startup %s failure', async (kind) => {
    const fetch = vi.fn()
    if (kind === 'network') fetch.mockRejectedValueOnce(new TypeError('offline'))
    else fetch.mockResolvedValueOnce(authError(500))
    fetch.mockResolvedValueOnce(response(identity))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '重试登录状态检查' }))
    await loggedIn()
  })

  it.each(['chain', 'premium'])('closes the gate on %s 401 and permits a fresh login', async (feature) => {
    const fetch = vi.fn().mockResolvedValueOnce(response(identity)).mockResolvedValueOnce(authError(401))
      .mockResolvedValueOnce(response(identity))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await loggedIn()
    if (feature === 'premium') fireEvent.click(screen.getByRole('button', { name: 'MO Premium Plane' }))
    fireEvent.change(screen.getByLabelText(feature === 'chain' ? '目标交易日' : 'Observation 日期'),
      { target: { value: '2026-09-21' } })
    await loginForm()
    expect(screen.queryByText('alice')).toBeNull()
    await submit()
    await loggedIn()
  })

  it.each([403, 429, 500])('keeps the gate open for business HTTP %i', async (status) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(identity)).mockResolvedValueOnce(authError(status)))
    render(<App />)
    await loggedIn()
    fireEvent.change(screen.getByLabelText('目标交易日'), { target: { value: '2026-09-21' } })
    await screen.findByRole('alert')
    expect(screen.getByRole('button', { name: 'Logout' })).toBeTruthy()
  })

  it('isolates stale business success after a sibling 401 and a new login', async () => {
    const old = deferred<Response>()
    let signal: AbortSignal | undefined
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(identity))
      .mockImplementationOnce((_url, init) => { signal = init.signal; return old.promise })
      .mockResolvedValueOnce(authError(401)).mockResolvedValueOnce(response(identity)))
    render(<App />)
    await loggedIn()
    fireEvent.change(screen.getByLabelText('目标交易日'), { target: { value: '2026-09-21' } })
    fireEvent.click(screen.getByRole('button', { name: 'MO Premium Plane' }))
    fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-21' } })
    await loginForm()
    expect(signal?.aborted).toBe(true)
    await submit()
    await loggedIn()
    await act(async () => old.resolve(response({ stale: true })))
    expect(screen.getByRole('heading', { name: 'MO 期权链' })).toBeTruthy()
    expect(screen.queryByTestId('plot')).toBeNull()
  })

  it('logout isolates pending business results and clears identity only after 204', async () => {
    const old = deferred<Response>()
    const exiting = deferred<Response>()
    let signal: AbortSignal | undefined
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(identity))
      .mockImplementationOnce((_url, init) => { signal = init.signal; return old.promise })
      .mockReturnValueOnce(exiting.promise))
    render(<App />)
    await loggedIn()
    fireEvent.change(screen.getByLabelText('目标交易日'), { target: { value: '2026-09-21' } })
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }))
    expect(signal?.aborted).toBe(true)
    expect(screen.getByText('正在退出…')).toBeTruthy()
    await act(async () => old.resolve(response({ stale: true })))
    exiting.resolve(response(null, 204))
    await loginForm()
    expect(screen.queryByText('alice')).toBeNull()
  })

  it('aborts and isolates an in-flight Explorer list on logout', async () => {
    const old = deferred<Response>()
    let signal: AbortSignal | undefined
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(identity))
      .mockImplementationOnce((_url, init) => { signal = init.signal; return old.promise })
      .mockResolvedValueOnce(response(null, 204)))
    render(<App />)
    await loggedIn()
    fireEvent.click(screen.getByRole('button', { name: 'Research Explorer' }))
    await waitFor(() => expect(signal).toBeDefined())
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }))
    expect(signal?.aborted).toBe(true)
    await loginForm()
    await act(async () => old.resolve(response({ data: [{ publication_id: 'stale', status: 'success' }], next_cursor: null })))
    expect(screen.queryByText('stale')).toBeNull()
    expect(screen.queryByRole('heading', { name: 'Research Explorer' })).toBeNull()
  })

  it('keeps logout failure explicit and retryable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(identity))
      .mockRejectedValueOnce(new TypeError('offline')).mockResolvedValueOnce(response(null, 204)))
    render(<App />)
    await loggedIn()
    fireEvent.click(screen.getByRole('button', { name: 'Logout' }))
    fireEvent.click(await screen.findByRole('button', { name: '重试退出' }))
    await loginForm()
  })

  it('ignores the obsolete StrictMode me response', async () => {
    const obsolete = deferred<Response>()
    const latest = deferred<Response>()
    const fetch = vi.fn().mockReturnValueOnce(obsolete.promise).mockReturnValueOnce(latest.promise)
    vi.stubGlobal('fetch', fetch)
    render(<StrictMode><App /></StrictMode>)
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
    latest.resolve(response(identity))
    await loggedIn()
    await act(async () => obsolete.resolve(authError(401)))
    expect(screen.getByText('alice')).toBeTruthy()
    expect(fetch.mock.calls[0][1].signal.aborted).toBe(true)
  })
})
