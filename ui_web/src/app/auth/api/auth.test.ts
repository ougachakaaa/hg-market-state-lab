import { afterEach, expect, it, vi } from 'vitest'
import { login, logout, me, register } from './auth'
import { authErrorMessage, AuthRequestError } from './authError'

afterEach(() => vi.unstubAllGlobals())
const identity = { id: 'id', username: 'alice', status: 'active' }
it('adapts all four generated operations with relative URLs and same-origin credentials', async () => {
  const fetch = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ message: 'Registration request accepted.' }), { status: 202 }))
    .mockResolvedValueOnce(new Response(JSON.stringify(identity)))
    .mockResolvedValueOnce(new Response(JSON.stringify(identity)))
    .mockResolvedValueOnce(new Response(null, { status: 204 }))
  vi.stubGlobal('fetch', fetch)
  const credentials = { username: 'alice', password: 'synthetic password' }
  await register(credentials)
  expect(await login(credentials)).toEqual(identity)
  expect(await me()).toEqual(identity)
  expect(await logout()).toBeUndefined()
  expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/auth/register', '/auth/login', '/auth/me', '/auth/logout'])
  for (const [, init] of fetch.mock.calls) expect(init.credentials).toBe('same-origin')
  expect(fetch.mock.calls[0][1].body).toBe(JSON.stringify(credentials))
  expect(fetch.mock.calls[2][1].body).toBeUndefined()
  expect(fetch.mock.calls[3][1].body).toBeUndefined()
})
it('preserves the typed error and Retry-After without exposing server detail as UI truth', async () => {
  const payload = { error: { kind: 'rate_limited', detail: 'Too many requests.', param: null } }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), {
    status: 429, headers: { 'Retry-After': '12' },
  })))
  await expect(login({ username: 'alice', password: 'synthetic password' })).rejects.toMatchObject({
    status: 429, retryAfter: '12', response: payload,
  })
})
it.each([{ ...identity, status: 'pending' }, { username: 'alice' }, { token: 'unexpected' }])(
  'rejects an invalid identity response', async (body) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(body))))
    await expect(me()).rejects.toMatchObject({ status: 'invalid_response' })
  },
)
it('keeps network and unknown HTTP failures distinct from credentials errors', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValueOnce(new TypeError('offline'))
    .mockResolvedValueOnce(new Response('unexpected', { status: 502 })))
  await expect(me()).rejects.toMatchObject({ status: 'network' })
  await expect(me()).rejects.toMatchObject({ status: 502 })
  expect(authErrorMessage(new AuthRequestError(502))).not.toContain('密码')
})

it('requires the exact logout 204 contract instead of accepting an identity body', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(identity))))
  await expect(logout()).rejects.toMatchObject({ status: 'invalid_response' })
})
