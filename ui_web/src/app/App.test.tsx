import canonicalMap from '../../../docs/strategy-research/map.json'
import { commitDate } from '../test/datePicker'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { StrictMode } from 'react'
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import App from './App'
import backtestFixture from '../features/backtesting/api/result.fixture.json'

vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))

const defaultStrategy = canonicalMap.nodes.find(node => node.kind === 'strategy')!
const strategyPath = `/roadmap/${defaultStrategy.id}`
const identity = { id: 'test-user', username: 'alice', status: 'active' }
const response = (body: unknown, status = 200) => new Response(status === 204 ? null : JSON.stringify(body), { status })
function stubAuthenticatedFetch(fetch: (url: string, options?: RequestInit) => Promise<Response>) {
  vi.stubGlobal('fetch', (url: string, options?: RequestInit) =>
    url === '/auth/mode' ? Promise.resolve(response('authenticated')) : fetch(url, options))
}
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
    stubAuthenticatedFetch(fetch)
    render(<App />)
    expect(screen.getByText('正在检查工作区访问状态…')).toBeTruthy()
    expect(screen.queryByRole('menuitem', { name: '数据总览' })).toBeNull()
    pending.resolve(unauthorized())
    await screen.findByRole('button', { name: '登录' })
    expect(window.location.pathname).toBe('/data/mo-option-chain')
    expect(fetch.mock.calls[0][0]).toBe('/auth/me')
  })

  it('logs in at root to the strategy map', async () => {
    stubAuthenticatedFetch(vi.fn().mockResolvedValueOnce(unauthorized()).mockResolvedValueOnce(response(identity)))
    render(<App />)
    await screen.findByRole('button', { name: '登录' })
    await submitLogin()
    await screen.findByRole('heading', { name: '策略研究地图' })
    const navigation = screen.getByRole('menu', { name: '业务导航' })
    expect(within(navigation).getAllByRole('menuitem')[0].textContent).toBe('策略')
    expect(window.location.pathname).toBe(strategyPath)
  })

  it('restores deep route, navigates with history and logs out', async () => {
    window.history.replaceState(null, '', '/backtesting/futures-roll-long')
    stubAuthenticatedFetch(vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity)
      : url === '/api/research/capabilities' ? response([]) : response(null, 204))))
    render(<App />)
    await screen.findByRole('heading', { name: /期货展期做多回测/ })
    expect(window.location.pathname).toBe('/backtesting/futures-roll-long')
    fireEvent.click(screen.getByRole('menuitem', { name: '研究' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '研究总览' }))
    expect(window.location.pathname).toBe('/research')
    await act(async () => { window.history.replaceState(null, '', '/backtesting/futures-roll-long'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await waitFor(() => expect(screen.getByRole('heading', { name: /期货展期做多回测/ })).toBeTruthy())
    fireEvent.click(screen.getByRole('button', { name: '退出登录' }))
    await screen.findByRole('button', { name: '登录' })
    expect(screen.queryByText('alice')).toBeNull()
  })

  it('keeps logout failure explicit and retryable', async () => {
    let logoutAttempts = 0
    stubAuthenticatedFetch(vi.fn((url: string) => {
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

  it('normalizes an unknown history destination to the strategy map', async () => {
    stubAuthenticatedFetch(vi.fn().mockResolvedValue(response(identity)))
    render(<App />)
    await screen.findByRole('button', { name: '退出登录' })
    await act(async () => { window.history.pushState(null, '', '/unknown'); window.dispatchEvent(new PopStateEvent('popstate')) })
    expect(window.location.pathname).toBe(strategyPath)
  })
})

describe('local online access', () => {
  it('retries failed mode discovery without opening the login gate', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(unauthorized()).mockResolvedValueOnce(response('local'))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    expect((await screen.findByRole('alert')).textContent).toContain('无法确认工作区访问模式')
    expect(screen.queryByRole('button', { name: '登录' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: '重试访问检查' }))
    await screen.findByText('本地模式')
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/mode', '/auth/mode'])
  })

  it('waits for mode and opens a deep link without requesting an identity', async () => {
    window.history.replaceState(null, '', '/research/publications')
    const mode = deferred<Response>()
    const fetch = vi.fn((url: string) => url === '/auth/mode' ? mode.promise
      : Promise.resolve(response({ data: [], next_cursor: null })))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    expect(screen.getByText('正在检查工作区访问状态…')).toBeTruthy()
    expect(window.location.pathname).toBe('/research/publications')
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/mode'])
    mode.resolve(response('local'))
    await screen.findByText('Publication Store 为空。')
    expect(screen.getByText('本地模式')).toBeTruthy()
    expect(screen.queryByRole('button', { name: '登录' })).toBeNull()
    expect(screen.queryByRole('button', { name: '退出登录' })).toBeNull()
    await act(async () => {
      window.history.pushState(null, '', '/backtesting')
      window.dispatchEvent(new PopStateEvent('popstate'))
    })
    await screen.findByRole('heading', { name: '回测总览' })
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/mode', '/api/research/publications'])
  })

  it('shows a retryable access failure when a local business request returns 401', async () => {
    window.history.replaceState(null, '', '/research/publications')
    const fetch = vi.fn().mockResolvedValueOnce(response('local')).mockResolvedValueOnce(unauthorized())
      .mockResolvedValueOnce(response('local'))
      .mockResolvedValueOnce(response({ data: [], next_cursor: null }))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    expect((await screen.findByRole('alert')).textContent).toContain('本地模式的业务请求意外返回 401')
    expect(screen.queryByRole('button', { name: '登录' })).toBeNull()
    expect(screen.queryByRole('heading', { name: '研究结果浏览' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: '重试访问检查' }))
    await screen.findByText('Publication Store 为空。')
    expect(window.location.pathname).toBe('/research/publications')
    expect(fetch.mock.calls.map(([url]) => url)).toEqual([
      '/auth/mode', '/api/research/publications', '/auth/mode', '/api/research/publications',
    ])
  })
})

describe('integrated feature routes', () => {
  it('opens all three pages and restores a direct Explorer URL', async () => {
    const fetch = vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity)
      : url === '/api/research/capabilities' ? response([]) : response({ data: [], next_cursor: null })))
    stubAuthenticatedFetch(fetch)
    render(<App />)
    await act(async () => { window.history.pushState(null, '', '/research/publications'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await screen.findByText('Publication Store 为空。')
    expect(window.location.pathname).toBe('/research/publications')
    expect(fetch.mock.calls.some(([url]) => url === '/api/research/publications')).toBe(true)
    fireEvent.click(screen.getByRole('menuitem', { name: '日常数据' }))
    fireEvent.click(screen.getByRole('menuitem', { name: '数据总览' }))
    expect(window.location.pathname).toBe('/data')
    fireEvent.click(screen.getByRole('button', { name: '打开 MO Option Chain' }))
    await screen.findByRole('heading', { name: 'MO 期权链' })
    expect(window.location.pathname).toBe('/data/mo-option-chain')
    fireEvent.click(screen.getByRole('menuitem', { name: 'MO Premium Plane' }))
    await screen.findByRole('heading', { name: 'MO 年化权利金平面' })
    expect(window.location.pathname).toBe('/data/mo-premium-plane')
    await act(async () => { window.history.replaceState(null, '', '/research/publications'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await screen.findByRole('heading', { name: '研究结果浏览' })
  })

  it('returns to the gate on a feature 401 and isolates its result', async () => {
    window.history.replaceState(null, '', '/data/mo-option-chain')
    const fetch = vi.fn().mockResolvedValueOnce(response(identity)).mockResolvedValueOnce(unauthorized())
    stubAuthenticatedFetch(fetch)
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
    stubAuthenticatedFetch(fetch)
    render(<App />)
    await waitFor(() => expect(signal).toBeDefined())
    fireEvent.click(screen.getByRole('button', { name: '退出登录' }))
    expect(signal?.aborted).toBe(true)
    await screen.findByRole('button', { name: '登录' })
    old.resolve(response({ data: [{ publication_id: 'stale', status: 'success' }], next_cursor: null }))
    expect(screen.queryByText('stale')).toBeNull()
  })

  it('closes the workspace on a Catalog 401 and discards a late catalog result', async () => {
    window.history.replaceState(null, '', '/research')
    const old = deferred<Response>()
    const fetch = vi.fn().mockResolvedValueOnce(response(identity)).mockImplementationOnce(() => old.promise)
    stubAuthenticatedFetch(fetch)
    render(<App />)
    await screen.findByRole('heading', { name: '研究总览' })
    old.resolve(unauthorized())
    await screen.findByRole('button', { name: '登录' })
    expect(screen.queryByRole('heading', { name: '价格分段研究' })).toBeNull()
    expect(screen.queryByText('alice')).toBeNull()
  })

  it('restores the Workspace on direct reload and browser history', async () => {
    window.history.replaceState(null, '', '/research')
    stubAuthenticatedFetch(vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity)
      : url === '/api/research/capabilities' ? response([]) : response({ data: [], next_cursor: null }))))
    render(<App />)
    await screen.findByRole('heading', { name: '研究总览' })
    await act(async () => { window.history.pushState(null, '', '/research/publications'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await screen.findByText('Publication Store 为空。')
    await act(async () => { window.history.replaceState(null, '', '/research'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await screen.findByRole('heading', { name: '研究总览' })
    expect(window.location.pathname).toBe('/research')
  })
})

describe('authentication regressions across the workspace', () => {
  it('registers without opening the workspace', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(unauthorized())
      .mockResolvedValueOnce(response({ message: 'Registration request accepted.' }, 202))
    stubAuthenticatedFetch(fetch)
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
    stubAuthenticatedFetch(vi.fn().mockResolvedValueOnce(unauthorized())
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
    stubAuthenticatedFetch(fetch)
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '重试访问检查' }))
    await screen.findByRole('button', { name: '退出登录' })
  })

  it.each([403, 429, 500])('keeps the gate open for business HTTP %i', async (status) => {
    window.history.replaceState(null, '', '/data/mo-option-chain')
    stubAuthenticatedFetch(vi.fn().mockResolvedValueOnce(response(identity))
      .mockResolvedValueOnce(response({ error: { kind: 'internal_error', detail: '', param: null } }, status)))
    render(<App />)
    await screen.findByRole('heading', { name: 'MO 期权链' })
    commitDate(screen.getByLabelText('观察日期'), '2026-09-21')
    await screen.findByRole('alert')
    expect(screen.getByRole('button', { name: '退出登录' })).toBeTruthy()
  })

  it('isolates an obsolete StrictMode mode response', async () => {
    const obsolete = deferred<Response>()
    const latest = deferred<Response>()
    const fetch = vi.fn().mockReturnValueOnce(obsolete.promise).mockReturnValueOnce(latest.promise)
      .mockResolvedValueOnce(response(identity))
    vi.stubGlobal('fetch', fetch)
    render(<StrictMode><App /></StrictMode>)
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
    latest.resolve(response('authenticated'))
    await screen.findByRole('button', { name: '退出登录' })
    await act(async () => { obsolete.resolve(response('local')) })
    expect(screen.getByText('alice')).toBeTruthy()
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/mode', '/auth/mode', '/auth/me'])
  })

  it('isolates an identity response after its application unmounts', async () => {
    const obsolete = deferred<Response>()
    const fetch = vi.fn().mockReturnValueOnce(obsolete.promise).mockResolvedValueOnce(response(identity))
    stubAuthenticatedFetch(fetch)
    const first = render(<App />)
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1))
    first.unmount()
    expect(fetch.mock.calls[0][1].signal.aborted).toBe(true)
    render(<App />)
    await screen.findByRole('button', { name: '退出登录' })
    await act(async () => { obsolete.resolve(unauthorized()) })
    expect(screen.getByText('alice')).toBeTruthy()
  })
})

it('preserves the Futures Basis deep link through login and clears its result on logout', async () => {
  const { readerFixture } = await import('../features/futures_basis_research/report/reader.fixture')
  const id = 'a'.repeat(32)
  window.history.replaceState(null, '', `/research/futures-basis?run_id=${id}`)
  const data = readerFixture()
  const request = { ...data.request.observation, case: 'futures_basis_v1', analysis_profile: 'r01a_standard_v2' }
  let signedIn = false
  stubAuthenticatedFetch(vi.fn((url: string) => {
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
  const protectedReply = deferred<Response>()
  const fetch = vi.fn((url: string) => url === '/auth/me' ? Promise.resolve(response(identity)) : protectedReply.promise)
  stubAuthenticatedFetch(fetch)
  render(<App />)
  await screen.findByRole('heading', { name: 'Futures Basis Research' })
  expect(fetch.mock.calls.some(([url]) => url.includes('/runs/'))).toBe(true)
  await act(async () => { protectedReply.resolve(unauthorized()) })
  await screen.findByRole('button', { name: '登录' })
  expect(screen.queryByRole('heading', { name: 'Futures Basis Research' })).toBeNull()
})

describe('WP1 navigation composition', () => {
  it('shows studies directly and retains the hidden Explorer route', async () => {
    window.history.replaceState(null, '', '/research')
    stubAuthenticatedFetch(vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity)
      : url === '/api/research/capabilities' ? response([]) : response({ data: [], next_cursor: null }))))
    const { container } = render(<App />)
    const navigation = await screen.findByRole('menu', { name: '业务导航' })
    expect(within(navigation).getByRole('menuitem', { name: '研究总览' })).toBeTruthy()
    expect(within(navigation).getByRole('menuitem', { name: '历史基差研究' })).toBeTruthy()
    expect(within(navigation).queryByRole('menuitem', { name: 'Research Explorer' })).toBeNull()
    expect(within(navigation).queryByRole('menuitem', { name: 'DESCRIPTIVE RESEARCH' })).toBeNull()
    expect(window.location.pathname).toBe('/research')
    await act(async () => { window.history.pushState(null, '', '/research/publications'); window.dispatchEvent(new PopStateEvent('popstate')) })
    await screen.findByRole('heading', { name: '研究结果浏览' })
    expect(container.querySelectorAll('.ant-menu-item-selected')).toHaveLength(0)
    expect(screen.getAllByText('Research Explorer')).toHaveLength(1)
  })

  it('keeps group toggles out of history and selects only the destination leaf', async () => {
    window.history.replaceState(null, '', '/research')
    stubAuthenticatedFetch(vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity) : response([]))))
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
    stubAuthenticatedFetch(vi.fn().mockResolvedValue(response(identity)))
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

describe('authenticated Run navigation retention', () => {
  const id = 'a'.repeat(32)
  const base = `/api/backtesting/futures-roll/runs/${id}`
  function installFetch() {
    const fetch = vi.fn((url: string, _init?: RequestInit) => {
      if (url === '/auth/me' || url === '/auth/login') return Promise.resolve(response(identity))
      if (url === '/auth/logout') return Promise.resolve(response(null, 204))
      if (url === base) return Promise.resolve(response({
        run_id: id, request: backtestFixture.request, status: 'COMPLETED',
        created_at: '2026-11-09T00:00:00Z', started_at: '2026-11-09T00:00:01Z',
        finished_at: '2026-11-09T00:00:02Z', result_available: true, failure: null,
      }))
      if (url === `${base}/result`) return Promise.resolve(response({ run_id: id, request: backtestFixture.request, data: backtestFixture }))
      if (url.startsWith('/api/research/futures-basis/')) return Promise.resolve(unauthorized())
      return Promise.resolve(response([]))
    })
    stubAuthenticatedFetch(fetch)
    return fetch
  }
  async function openResearch() {
    fireEvent.click(screen.getByRole('menuitem', { name: '研究' }))
    fireEvent.click(await screen.findByRole('menuitem', { name: '研究总览' }))
    await screen.findByRole('heading', { name: '研究总览' })
  }

  it('retains the real Backtesting page and Result without extra reads or POST', async () => {
    window.history.replaceState(null, '', `/backtesting/futures-roll-long?run_id=${id}`)
    const fetch = installFetch()
    render(<App />)
    await screen.findAllByTestId('plot')
    commitDate(screen.getByLabelText('开始日期'), '2024-10-18')
    fireEvent.click(screen.getByText('Calendar Days'))
    fireEvent.click(screen.getByRole('button', { name: '运行详情' }))
    fireEvent.click(screen.getByRole('button', { name: '策略规则与收益口径' }))
    await openResearch()
    fireEvent.click(screen.getByRole('menuitem', { name: '期货展期做多回测' }))
    await screen.findAllByTestId('plot')
    expect(screen.getByLabelText('开始日期')).toHaveProperty('value', '2024-10-18')
    expect(screen.getByRole('button', { name: '运行详情' }).getAttribute('aria-expanded')).toBe('true')
    expect(screen.getByRole('button', { name: '策略规则与收益口径' }).getAttribute('aria-expanded')).toBe('true')
    expect(screen.getByText('Calendar Days').closest('.ant-segmented-item')?.className).toContain('ant-segmented-item-selected')
    expect(window.location.search).toBe(`?run_id=${id}`)
    expect(fetch.mock.calls.filter(([url]) => url === base)).toHaveLength(1)
    expect(fetch.mock.calls.filter(([url]) => url === `${base}/result`)).toHaveLength(1)
    expect(fetch.mock.calls.some(([, init]) => init?.method === 'POST')).toBe(false)
  })

  it.each(['logout', '401'])('discards retained identity across %s and login', async boundary => {
    window.history.replaceState(null, '', `/backtesting/futures-roll-long?run_id=${id}`)
    const fetch = installFetch()
    render(<App />)
    await screen.findAllByTestId('plot')
    await openResearch()
    if (boundary === 'logout') fireEvent.click(screen.getByRole('button', { name: '退出登录' }))
    else await act(async () => {
      window.history.pushState(null, '', `/research/futures-basis?run_id=${'c'.repeat(32)}`)
      window.dispatchEvent(new PopStateEvent('popstate'))
    })
    await screen.findByRole('button', { name: '登录' })
    // A fresh login without an explicit Run URL cannot inherit the old memory.
    await act(async () => {
      window.history.replaceState(null, '', '/research')
      window.dispatchEvent(new PopStateEvent('popstate'))
    })
    await submitLogin()
    await screen.findByRole('heading', { name: '研究总览' })
    fireEvent.click(screen.getByRole('menuitem', { name: '回测' }))
    fireEvent.click(await screen.findByRole('menuitem', { name: '期货展期做多回测' }))
    await screen.findByRole('heading', { name: /期货展期做多回测/ })
    expect(window.location.search).toBe('')
    expect(screen.queryByTestId('backtest-result')).toBeNull()
    expect(fetch.mock.calls.filter(([url]) => url === base)).toHaveLength(1)
  })
})

it('opens Backtesting Overview without business requests and navigates explicitly to the instance', async () => {
  window.history.replaceState(null, '', '/backtesting')
  const fetch = vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? response(identity) : response(null, 204)))
  stubAuthenticatedFetch(fetch)
  render(<App />)
  await screen.findByRole('heading', { name: '回测总览' })
  expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/me'])
  fireEvent.click(screen.getByRole('button', { name: '查看回测' }))
  await screen.findByRole('heading', { name: /期货展期做多回测/ })
  expect(window.location.pathname).toBe('/backtesting/futures-roll-long')
})

it('preserves an anonymous legacy Run deep link through login', async () => {
  window.history.replaceState(null, '', '/backtesting?run_id=bookmark')
  stubAuthenticatedFetch(vi.fn((url: string) => Promise.resolve(url === '/auth/me' ? unauthorized()
    : url === '/auth/login' ? response(identity) : response({ error: { kind: 'not_found' } }, 404))))
  render(<App />)
  await screen.findByRole('button', { name: '登录' })
  await submitLogin()
  await screen.findByRole('heading', { name: /期货展期做多回测/ })
  expect(window.location.pathname).toBe('/backtesting/futures-roll-long')
  expect(window.location.search).toBe('?run_id=bookmark')
})
