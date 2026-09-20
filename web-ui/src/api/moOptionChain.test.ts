import { afterEach, describe, expect, it, vi } from 'vitest'
import { ChainRequestError, loadMoOptionChain } from './moOptionChain'

const chain = {
  target_trade_date: '2026-09-17',
  option_product: 'MO',
  price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [{
    expiry_date: '2026-09-25',
    calls: [{ instrument_id: 'C1', strike: 7000, price: null }],
    puts: [{ instrument_id: 'P1', strike: 7000, price: 0 }],
  }],
}

function response(body: unknown, ok = true): Response {
  return { ok, json: async () => body } as Response
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
    expect(options.signal).toBe(controller.signal)
    expect(result.expiries[0].calls[0].price).toBeNull()
    expect(result.expiries[0].puts[0].price).toBe(0)
  })

  it('returns the contract error kind and detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      error: { kind: 'date_not_available', detail: 'no data', param: 'target_trade_date' },
    }, false)))

    await expect(loadMoOptionChain('2026-09-18')).rejects.toMatchObject({
      kind: 'date_not_available',
      message: 'no data',
      param: 'target_trade_date',
    })
  })

  it('classifies malformed success, malformed errors, and transport failures', async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce(response({ ...chain, expiries: [{ ...chain.expiries[0], calls: [{ instrument_id: 'C1', strike: 7000, price: '0' }] }] }))
      .mockResolvedValueOnce(response({ error: { kind: 'unexpected', detail: 'no data' } }, false))
      .mockRejectedValueOnce(new TypeError('connection failed'))
    vi.stubGlobal('fetch', fetch)

    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionChain('2026-09-17')).rejects.toMatchObject({ kind: 'network' })
  })

  it('does not turn an aborted request into a network error', async () => {
    const controller = new AbortController()
    controller.abort()
    const abortError = new DOMException('aborted', 'AbortError')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abortError))

    await expect(loadMoOptionChain('2026-09-17', controller.signal)).rejects.toBe(abortError)
    expect(abortError).not.toBeInstanceOf(ChainRequestError)
  })
})
