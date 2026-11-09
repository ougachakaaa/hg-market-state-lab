import { afterEach, expect, it, vi } from 'vitest'
import { createRequestBoundary, installRequestBoundary, protectedRequest } from './protectedRequest'

let release: (() => void) | undefined
afterEach(() => { release?.(); vi.unstubAllGlobals() })
function deferred() {
  let resolve!: (value: Response) => void
  const promise = new Promise<Response>((done) => { resolve = done })
  return { promise, resolve }
}

it('refuses a request without an installed boundary', async () => {
  const fetch = vi.fn()
  vi.stubGlobal('fetch', fetch)
  await expect(protectedRequest('/business')).rejects.toMatchObject({ name: 'AbortError' })
  expect(fetch).not.toHaveBeenCalled()
})

it('propagates caller cancellation to an in-flight request', async () => {
  release = installRequestBoundary(createRequestBoundary(vi.fn()))
  const pending = deferred()
  const fetch = vi.fn().mockReturnValue(pending.promise)
  vi.stubGlobal('fetch', fetch)
  const caller = new AbortController()
  const request = protectedRequest('/business', caller.signal)
  caller.abort()
  expect(fetch.mock.calls[0][1].signal.aborted).toBe(true)
  pending.resolve(new Response('{}'))
  await expect(request).rejects.toMatchObject({ name: 'AbortError' })
})

it('replacing a boundary closes its pending requests', async () => {
  const pending = deferred()
  const oldCallback = vi.fn()
  const old = createRequestBoundary(oldCallback)
  const releaseOld = installRequestBoundary(old)
  const fetch = vi.fn().mockReturnValueOnce(pending.promise).mockResolvedValueOnce(new Response('{}'))
  vi.stubGlobal('fetch', fetch)
  const request = protectedRequest('/old')
  const nextCallback = vi.fn()
  const next = createRequestBoundary(nextCallback)
  release = installRequestBoundary(next)
  releaseOld()
  pending.resolve(new Response('', { status: 401 }))
  await expect(request).rejects.toMatchObject({ name: 'AbortError' })
  expect(old.closed).toBe(true)
  expect(next.closed).toBe(false)
  expect(oldCallback).not.toHaveBeenCalled()
  expect(nextCallback).not.toHaveBeenCalled()
  expect((await protectedRequest('/new')).status).toBe(200)
})

it('401 immediately closes the boundary, aborts concurrent requests and blocks new ones', async () => {
  const first = deferred()
  const unauthorized = vi.fn()
  const boundary = createRequestBoundary(unauthorized)
  release = installRequestBoundary(boundary)
  const fetch = vi.fn().mockReturnValueOnce(first.promise).mockResolvedValueOnce(new Response('', { status: 401 }))
  vi.stubGlobal('fetch', fetch)
  const a = protectedRequest('/a')
  await protectedRequest('/b')
  expect(unauthorized).toHaveBeenCalledTimes(1)
  expect(fetch.mock.calls[0][1].signal.aborted).toBe(true)
  await expect(protectedRequest('/c')).rejects.toMatchObject({ name: 'AbortError' })
  expect(fetch).toHaveBeenCalledTimes(2)
  first.resolve(new Response('{}'))
  await expect(a).rejects.toMatchObject({ name: 'AbortError' })
})

it('a late old-session 401 cannot close a new session', async () => {
  const late = deferred()
  const oldCallback = vi.fn()
  release = installRequestBoundary(createRequestBoundary(oldCallback))
  vi.stubGlobal('fetch', vi.fn().mockReturnValueOnce(late.promise).mockResolvedValueOnce(new Response('{}')))
  const a = protectedRequest('/old')
  release()
  const currentCallback = vi.fn()
  const current = createRequestBoundary(currentCallback)
  release = installRequestBoundary(current)
  late.resolve(new Response('', { status: 401 }))
  await expect(a).rejects.toMatchObject({ name: 'AbortError' })
  expect(current.closed).toBe(false)
  expect(currentCallback).not.toHaveBeenCalled()
  expect(oldCallback).not.toHaveBeenCalled()
  expect((await protectedRequest('/new')).status).toBe(200)
})

it.each([403, 429, 500])('does not close the request boundary for HTTP %i', async (status) => {
  const callback = vi.fn()
  release = installRequestBoundary(createRequestBoundary(callback))
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status })))
  expect((await protectedRequest('/business')).status).toBe(status)
  expect(callback).not.toHaveBeenCalled()
})

it('a cancelled feature request returning 401 still closes its current auth lifetime', async () => {
  const late = deferred()
  const unauthorized = vi.fn()
  release = installRequestBoundary(createRequestBoundary(unauthorized))
  vi.stubGlobal('fetch', vi.fn().mockReturnValue(late.promise))
  const caller = new AbortController()
  const request = protectedRequest('/cancelled-feature', caller.signal, { method: 'POST', body: '{}' })
  caller.abort()
  late.resolve(new Response('', { status: 401 }))
  expect((await request).status).toBe(401)
  expect(unauthorized).toHaveBeenCalledOnce()
})
