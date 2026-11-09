import { afterEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'

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
})
