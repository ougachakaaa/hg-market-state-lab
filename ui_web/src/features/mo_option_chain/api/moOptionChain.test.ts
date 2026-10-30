import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ChainRequestError, loadMoOptionChain } from './moOptionChain'
import type { OptionChain } from './moOptionChain'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'

let releaseBoundary: () => void
beforeEach(() => { releaseBoundary = installRequestBoundary(createRequestBoundary(() => {})) })
afterEach(() => releaseBoundary())

const chain = {
  target_trade_date: '2026-09-17',
  option_product: 'MO',
  price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [{
    expiry_date: '2026-09-25',
    futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
    calls: [{ instrument_id: 'C1', strike: 7000, price: null }],
    puts: [{ instrument_id: 'P1', strike: 7000, price: 0 }],
  }],
} satisfies OptionChain

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response
}

afterEach(() => vi.unstubAllGlobals())

describe('loadMoOptionChain', () => {
  it('uses the fixed query and retains null and zero prices', async () => {
    const fetch = vi.fn().mockResolvedValue(response(chain))
    vi.stubGlobal('fetch', fetch)
    const controller = new AbortController()

    const result = await loadMoOptionChain('2026-09-17', controller.signal)

    const [url, options] = fetch.mock.calls[0] as [string, RequestInit]
    const query = new URL(url, 'http://localhost').searchParams
    expect(new URL(url, 'http://localhost').pathname).toBe('/mo-option-chain')
    expect([...query.entries()]).toEqual([
      ['target_trade_date', '2026-09-17'],
      ['option_product', 'MO'],
      ['price_type', 'close'],
    ])
    expect(options.signal).toBeInstanceOf(AbortSignal)
    expect(result.expiries[0].calls[0].price).toBeNull()
    expect(result.expiries[0].puts[0].price).toBe(0)
    expect(result.expiries[0].futures).toEqual({ instrument_id: 'IM2609.CFE', price: 7487.6 })
  })

  it.each([
    undefined,
    { instrument_id: 'IM2609.CFE', price: null },
    { instrument_id: 'IM2609.CFE', price: '7487.6' },
    { instrument_id: 2609, price: 7487.6 },
  ])('rejects an expiry with invalid futures %j', async (futures) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      ...chain,
      expiries: [{ ...chain.expiries[0], futures }],
    })))
    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'invalid_response' })
  })

  it('accepts an explicit null futures reference', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      ...chain,
      expiries: [{ ...chain.expiries[0], futures: null }],
    })))
    const result = await loadMoOptionChain('2026-09-17')
    expect(result.expiries[0].futures).toBeNull()
  })

  it.each([
    { ...chain, price_type: 'settle' },
    { ...chain, expiries: [{ ...chain.expiries[0], calls: [{ instrument_id: 'C1', strike: 7000 }] }] },
    { ...chain, underlying: { instrument_id: '000852.SH', price: null } },
  ])('rejects a success body outside the generated contract', async (body) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(body)))
    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'invalid_response' })
  })

  it('returns the contract error kind and detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      error: { kind: 'date_not_available', detail: 'no data', param: 'target_trade_date' },
    }, 404)))

    await expect(loadMoOptionChain('2026-09-18')).rejects.toMatchObject({
      kind: 'date_not_available',
      message: 'no data',
      param: 'target_trade_date',
    })
  })

  it('classifies malformed success, malformed errors, and transport failures', async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce(response({ ...chain, expiries: [{ ...chain.expiries[0], calls: [{ instrument_id: 'C1', strike: 7000, price: '0' }] }] }))
      .mockResolvedValueOnce(response({ error: { kind: 'unexpected', detail: 'no data' } }, 400))
      .mockRejectedValueOnce(new TypeError('connection failed'))
    vi.stubGlobal('fetch', fetch)

    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'network' })
  })

  it('rejects an invalid error parameter and an undeclared response status', async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce(response({ error: { kind: 'invalid_request', detail: 'bad', param: 'unknown' } }, 400))
      .mockResolvedValueOnce(response({ error: { kind: 'date_not_available', detail: 'missing' } }, 500))
    vi.stubGlobal('fetch', fetch)

    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'invalid_response' })
  })

  it('does not turn an aborted request into a network error', async () => {
    const controller = new AbortController()
    controller.abort()
    const abortError = new DOMException('aborted', 'AbortError')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abortError))

    await expect(loadMoOptionChain('2026-09-17', controller.signal)).rejects.toMatchObject({ name: 'AbortError' })
    expect(abortError).not.toBeInstanceOf(ChainRequestError)
  })
})


it.each([[401, 'authentication_required'], [403, 'origin_forbidden'], [500, 'internal_error']])(
  'preserves generated access errors for HTTP %s', async (status, kind) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      error: { kind, detail: 'Access failed.', param: null },
    }, status as number)))
    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind, message: 'Access failed.' })
  },
)
