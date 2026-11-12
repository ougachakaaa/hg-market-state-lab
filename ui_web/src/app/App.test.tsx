import { commitDate } from '../test/datePicker'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { StrictMode } from 'react'
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
  fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'alice' } })
  fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'synthetic password' } })
  fireEvent.click(screen.getByRole('button', { name: '登录' }))
}

describe('workspace shell and authentication', () => {
  it('shows only the gate while checking and on anonymous deep links', async () => {
    window.history.replaceState(null, '', '/data/mo-option-chain')
    const pending = deferred<Response>()
    const fetch = vi.fn((_url: string) => pending.promise)
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    expect(screen.getByText('正在检查登录状态…')).toBeTruthy()
    expect(screen.queryByRole('menuitem', { name: '数据总览' })).toBeNull()
    pending.resolve(unauthorized())
    await screen.findByRole('button', { name: '登录' })
    expect(window.location.pathname).toBe('/data/mo-option-chain')
    expect(fetch.mock.calls[0][0]).toBe('/auth/me')
  })

  it('logs in at root to Research', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(unauthorized()).mockResolvedValueOnce(response(identity)))
    render(<App />)
    await screen.findByRole('button', { name: '登录' })
    await submitLogin()
    await screen.findByRole('menuitem', { name: '研究总览' })
    expect(window.location.pathname).toBe('/research')
  })

  it('restores deep route, navigates with history and logs out', async () => {
    window.history.replaceState(null, '', '/backtesting')
    vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity)
      : url === '/api/research/capabilities' ? response([]) : response(null, 204))))
    render(<App />)
    await screen.findByText(/期货展期做多回测/)
    expect(window.location.pathname).toBe('/backtesting')
    fireEvent.click(screen.getByRole('menuitem', { name: '研究' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '研究总览' }))
    expect(window.location.pathname).toBe('/research')
    await act(async () => { window.history.replaceState(null, '', '/backtesting'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await waitFor(() => expect(screen.getByText(/期货展期做多回测/)).toBeTruthy())
    fireEvent.click(screen.getByRole('button', { name: '退出登录' }))
    await screen.findByRole('button', { name: '登录' })
    expect(screen.queryByText('alice')).toBeNull()
  })

  it('keeps logout failure explicit and retryable', async () => {
    let logoutAttempts = 0
    vi.stubGlobal('fetch', vi.fn((url: string) => {
      if (url === '/auth/me') return Promise.resolve(unauthorized())
      if (url === '/auth/login') return Promise.resolve(response(identity))
      if (url === '/api/research/capabilities') return Promise.resolve(response([]))
      if (url === '/auth/logout' && logoutAttempts++ === 0) return Promise.reject(new TypeError('offline'))
      return Promise.resolve(response(null, 204))
    }))
    render(<App />)
    await screen.findByRole('button', { name: '登录' })
    await submitLogin()
    fireEvent.click(await screen.findByRole('button', { name: '退出登录' }))
    fireEvent.click(await screen.findByRole('button', { name: '重试退出' }))
    await screen.findByRole('button', { name: '登录' })
  })

  it('normalizes an unknown history destination to Research', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(identity)))
    render(<App />)
    await screen.findByRole('button', { name: '退出登录' })
    await act(async () => { window.history.pushState(null, '', '/unknown'); window.dispatchEvent(new PopStateEvent('popstate')) })
    expect(window.location.pathname).toBe('/research')
  })
})

describe('integrated feature routes', () => {
  it('opens all three pages and restores a direct Explorer URL', async () => {
    const fetch = vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity)
      : url === '/api/research/capabilities' ? response([]) : response({ data: [], next_cursor: null })))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '浏览已发布研究结果' }))
    await screen.findByText('Publication Store 为空。')
    expect(window.location.pathname).toBe('/research/publications')
    expect(fetch.mock.calls.some(([url]) => url === '/api/research/publications')).toBe(true)
    fireEvent.click(screen.getByRole('menuitem', { name: '日常数据' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '数据总览' }))
    expect(window.location.pathname).toBe('/data')
    fireEvent.click(screen.getByRole('button', { name: '打开 MO Option Chain' }))
    await screen.findByRole('heading', { name: 'MO 期权链' })
    expect(window.location.pathname).toBe('/data/mo-option-chain')
    fireEvent.click(screen.getByText('MO Premium Plane', { selector: '.ant-menu-title-content' }))
    await screen.findByRole('heading', { name: 'MO 年化权利金平面' })
    expect(window.location.pathname).toBe('/data/mo-premium-plane')
    await act(async () => { window.history.replaceState(null, '', '/research/publications'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await screen.findByRole('heading', { name: '研究结果浏览' })
  })

  it('returns to the gate on a feature 401 and isolates its result', async () => {
    window.history.replaceState(null, '', '/data/mo-option-chain')
    const fetch = vi.fn().mockResolvedValueOnce(response(identity)).mockResolvedValueOnce(unauthorized())
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await screen.findByRole('heading', { name: 'MO 期权链' })
    commitDate(screen.getByLabelText('观察日期'), '2026-09-21')
    await screen.findByRole('button', { name: '登录' })
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
    fireEvent.click(screen.getByRole('button', { name: '退出登录' }))
    expect(signal?.aborted).toBe(true)
    await screen.findByRole('button', { name: '登录' })
    old.resolve(response({ data: [{ publication_id: 'stale', status: 'success' }], next_cursor: null }))
    expect(screen.queryByText('stale')).toBeNull()
  })

  it('closes the workspace on a Catalog 401 and discards a late catalog result', async () => {
    const old = deferred<Response>()
    const fetch = vi.fn().mockResolvedValueOnce(response(identity)).mockImplementationOnce(() => old.promise)
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    await screen.findByRole('heading', { name: '研究总览' })
    old.resolve(unauthorized())
    await screen.findByRole('button', { name: '登录' })
    expect(screen.queryByText('Price Segmentation')).toBeNull()
    expect(screen.queryByText('alice')).toBeNull()
  })

  it('restores the Workspace on direct reload and browser history', async () => {
    window.history.replaceState(null, '', '/research')
    vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity)
      : url === '/api/research/capabilities' ? response([]) : response({ data: [], next_cursor: null }))))
    render(<App />)
    await screen.findByText('暂无已发布的在线能力。')
    fireEvent.click(screen.getByRole('button', { name: '浏览已发布研究结果' }))
    await screen.findByText('Publication Store 为空。')
    await act(async () => { window.history.replaceState(null, '', '/research'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await screen.findByText('暂无已发布的在线能力。')
    expect(window.location.pathname).toBe('/research')
  })
})

describe('authentication regressions across the workspace', () => {
  it('registers without opening the workspace', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(unauthorized())
      .mockResolvedValueOnce(response({ message: 'Registration request accepted.' }, 202))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '注册' }))
    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'alice' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'synthetic password' } })
    fireEvent.click(screen.getByRole('button', { name: '提交注册申请' }))
    await screen.findByText('注册申请已提交，请等待管理员审批后登录。')
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/me', '/auth/register'])
    expect(screen.queryByText('研究总览')).toBeNull()
  })

  it.each([
    [401, '用户名或密码错误。'], [400, '输入请求不合法，请检查输入。'],
    [403, '请求来源被拒绝，请从配置的应用地址访问。'],
    [429, '请求过于频繁，请稍后重试。'], [500, '认证服务暂时不可用，请重试。'],
  ])('shows login HTTP %i without opening the workspace', async (status, message) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(unauthorized())
      .mockResolvedValueOnce(response({ error: { kind: 'invalid_credentials', detail: '', param: null } }, status)))
    render(<App />)
    await screen.findByRole('button', { name: '登录' })
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
    await screen.findByRole('button', { name: '退出登录' })
  })

  it.each([403, 429, 500])('keeps the gate open for business HTTP %i', async (status) => {
    window.history.replaceState(null, '', '/data/mo-option-chain')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(response(identity))
      .mockResolvedValueOnce(response({ error: { kind: 'internal_error', detail: '', param: null } }, status)))
    render(<App />)
    await screen.findByRole('heading', { name: 'MO 期权链' })
    commitDate(screen.getByLabelText('观察日期'), '2026-09-21')
    await screen.findByRole('alert')
    expect(screen.getByRole('button', { name: '退出登录' })).toBeTruthy()
  })

  it('isolates an obsolete StrictMode identity response', async () => {
    const obsolete = deferred<Response>()
    const latest = deferred<Response>()
    const fetch = vi.fn().mockReturnValueOnce(obsolete.promise).mockReturnValueOnce(latest.promise)
    vi.stubGlobal('fetch', fetch)
    render(<StrictMode><App /></StrictMode>)
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
    latest.resolve(response(identity))
    await screen.findByRole('button', { name: '退出登录' })
    obsolete.resolve(unauthorized())
    expect(screen.getByText('alice')).toBeTruthy()
  })
})

it('preserves the Futures Basis deep link through login and clears its result on logout', async () => {
  const { readerFixture } = await import('../features/futures_basis_research/report/reader.fixture')
  const id = 'a'.repeat(32)
  window.history.replaceState(null, '', `/research/futures-basis?run_id=${id}`)
  const data = readerFixture()
  const request = { ...data.request.observation, case: 'futures_basis_v1', analysis_profile: 'r01a_standard_v1' }
  let signedIn = false
  vi.stubGlobal('fetch', vi.fn((url: string) => {
    if (url === '/auth/me') return Promise.resolve(signedIn ? response(identity) : unauthorized())
    if (url === '/auth/login') { signedIn = true; return Promise.resolve(response(identity)) }
    if (url === '/auth/logout') return Promise.resolve(response(null, 204))
    if (url.endsWith('/report')) return Promise.resolve(response({ run_id: id, request, result_status: 'complete', data }))
    return Promise.resolve(response({ run_id: id, request, status: 'COMPLETED', created_at: '2026-11-09T00:00:00Z', started_at: '2026-11-09T00:00:00Z', finished_at: '2026-11-09T00:00:01Z', result_available: true, result_status: 'complete', failure: null }))
  }))
  render(<App />)
  await screen.findByRole('button', { name: '登录' }); await submitLogin()
  await screen.findByText('Synthetic empty research')
  expect(window.location.search).toBe(`?run_id=${id}`)
  fireEvent.click(screen.getByRole('button', { name: '退出登录' }))
  await screen.findByRole('button', { name: '登录' })
  expect(screen.queryByText('Synthetic empty research')).toBeNull()
})

it('returns a restored Futures Basis run to the authentication gate on a protected 401', async () => {
  window.history.replaceState(null, '', `/research/futures-basis?run_id=${'a'.repeat(32)}`)
  vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity) : unauthorized())))
  render(<App />)
  await screen.findByRole('button', { name: '登录' })
  expect(screen.queryByRole('heading', { name: 'Futures Basis Research' })).toBeNull()
})

describe('WP1 navigation composition', () => {
  it('groups implemented topics and keeps Explorer outside the selected leaves', async () => {
    window.history.replaceState(null, '', '/research')
    vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity)
      : url === '/api/research/capabilities' ? response([]) : response({ data: [], next_cursor: null }))))
    const { container } = render(<App />)
    const navigation = await screen.findByRole('menu', { name: '业务导航' })
    expect(within(navigation).getByRole('menuitem', { name: '研究总览' })).toBeTruthy()
    expect(within(navigation).getByRole('menuitem', { name: '历史基差研究' })).toBeTruthy()
    expect(within(navigation).queryByRole('menuitem', { name: 'Research Explorer' })).toBeNull()
    expect(within(navigation).queryByRole('menuitem', { name: 'DESCRIPTIVE RESEARCH' })).toBeNull()
    fireEvent.click(within(navigation).getByText('DESCRIPTIVE RESEARCH'))
    expect(window.location.pathname).toBe('/research')
    fireEvent.click(screen.getByRole('button', { name: '浏览已发布研究结果' }))
    await screen.findByRole('heading', { name: '研究结果浏览' })
    expect(container.querySelectorAll('.ant-menu-item-selected')).toHaveLength(0)
    expect(container.querySelector('.ant-menu-submenu-selected')).toBeTruthy()
    expect(screen.getByText('Research Explorer')).toBeTruthy()
  })

  it('keeps group toggles out of history and selects only the destination leaf', async () => {
    window.history.replaceState(null, '', '/research')
    vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity) : response([]))))
    const { container } = render(<App />)
    await screen.findByRole('button', { name: '退出登录' })
    const navigation = screen.getByRole('menu', { name: '业务导航' })
    const icons = navigation.querySelectorAll('.anticon')
    expect(icons.length).toBeGreaterThan(0)
    expect([...icons].every(icon => icon.getAttribute('aria-hidden') === 'true')).toBe(true)
    expect(within(navigation).queryByRole('img')).toBeNull()
    expect(screen.getByRole('button', { name: '退出登录' })).toBeTruthy()
    const historyLength = window.history.length
    fireEvent.click(screen.getByRole('menuitem', { name: '日常数据' }))
    expect(window.location.pathname).toBe('/research')
    expect(window.history.length).toBe(historyLength)
    fireEvent.click(screen.getByRole('menuitem', { name: '数据总览' }))
    expect(window.location.pathname).toBe('/data')
    expect([...container.querySelectorAll('.ant-menu-item-selected')].map(item => item.textContent)).toEqual(['数据总览'])
    expect(screen.getAllByRole('heading', { level: 1 }).map(item => item.textContent)).toEqual(['数据总览'])
    expect(screen.getByRole('button', { name: '打开 MO Option Chain' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: '打开 MO Premium Plane' }))
    await screen.findByRole('heading', { name: 'MO 年化权利金平面' })
    expect(window.location.pathname).toBe('/data/mo-premium-plane')
    expect(container.querySelectorAll('.ant-menu-item-selected')).toHaveLength(1)
    expect(container.querySelectorAll('.ant-layout-header h1,.ant-layout-header h2,.ant-layout-header h3')).toHaveLength(0)
    fireEvent.click(screen.getByRole('link', { name: '日常数据' }))
    expect(window.location.pathname).toBe('/data')
  })

  it('defaults to a collapsed narrow workspace and keeps overview navigation accessible', async () => {
    const matchMedia = window.matchMedia.bind(window)
    vi.spyOn(window, 'matchMedia').mockImplementation(query => ({ ...matchMedia(query), matches: query.includes('1199.98px') }))
    window.history.replaceState(null, '', '/data')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(identity)))
    render(<App />)
    await screen.findByRole('button', { name: '展开导航' })
    fireEvent.click(screen.getByRole('menuitem', { name: '日常数据' }))
    expect(window.location.pathname).toBe('/data')
    fireEvent.click(await screen.findByRole('menuitem', { name: '数据总览' }))
    expect(window.location.pathname).toBe('/data')
    fireEvent.click(screen.getByRole('button', { name: '展开导航' }))
    expect(screen.getByRole('button', { name: '折叠导航' }).getAttribute('aria-expanded')).toBe('true')
    fireEvent.click(within(screen.getByRole('menu', { name: '业务导航' })).getByRole('menuitem', { name: 'MO Option Chain' }))
    await screen.findByRole('heading', { name: 'MO 期权链' })
    expect(window.location.pathname).toBe('/data/mo-option-chain')
  })
})
