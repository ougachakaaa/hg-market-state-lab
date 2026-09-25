import { afterEach, describe, expect, it, vi } from 'vitest'
import { loadMoOptionPremiumPlane, PremiumRequestError } from './moOptionPremium'
import type { PremiumPlane } from './moOptionPremium'

const plane = {
  observation: { kind: 'trade_date', value: '2026-09-21' },
  option_product: 'MO',
  price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', dte: 5, futures: { instrument_id: 'IM2609.CFE', price: 7301.6 } },
  ],
  points: [
    {
      instrument_id: 'MO2609-C-7000.CFE', expiry_date: '2026-09-25', option_type: 'call', strike: 7000,
      premium: 0, annualized_premium_points: 0, annualized_time_value_points: -1,
      annualized_seller_premium_yield: null,
    },
  ],
} satisfies PremiumPlane

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response
}

afterEach(() => vi.unstubAllGlobals())

describe('loadMoOptionPremiumPlane', () => {
  it('requests the complete fixed query and preserves null and zero facts', async () => {
    const fetch = vi.fn().mockResolvedValue(response(plane))
    vi.stubGlobal('fetch', fetch)
    const controller = new AbortController()

    const result = await loadMoOptionPremiumPlane('2026-09-21', 'high', controller.signal)

    const [url, options] = fetch.mock.calls[0] as [string, RequestInit]
    expect(new URL(url, 'http://localhost').pathname).toBe('/mo-option-premium-plane')
    expect([...new URL(url, 'http://localhost').searchParams.entries()]).toEqual([
      ['as_of', '2026-09-21'],
      ['option_product', 'MO'],
      ['price_type', 'high'],
    ])
    expect(options.signal).toBe(controller.signal)
    expect(result.points[0].annualized_premium_points).toBe(0)
    expect(result.points[0].annualized_time_value_points).toBe(-1)
    expect(result.points[0].annualized_seller_premium_yield).toBeNull()
  })

  it.each([
    { ...plane, option_product: 'IO' },
    { ...plane, observation: { kind: 'timestamp', value: '2026-09-21' } },
    { ...plane, underlying: { instrument_id: '000852.SH', price: null } },
    { ...plane, points: [{ ...plane.points[0], annualized_premium_points: '0' }] },
  ])('rejects a success body outside the generated contract', async (body) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(body)))
    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close'))
      .rejects.toMatchObject({ kind: 'invalid_response' })
  })

  it.each([
    [400, 'invalid_request'],
    [400, 'unsupported_query'],
    [404, 'date_not_available'],
    [503, 'premium_plane_unavailable'],
  ] as const)('returns the classified %s error response', async (status, kind) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      error: { kind, detail: 'backend detail', param: kind === 'date_not_available' ? 'as_of' : null },
    }, status)))

    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({
      kind,
      message: 'backend detail',
    })
  })

  it('rejects malformed errors, undeclared statuses, unreadable bodies and network failures', async () => {
    const unreadable = { ok: true, status: 200, json: async () => { throw new SyntaxError('bad json') } } as unknown as Response
    const fetch = vi.fn()
      .mockResolvedValueOnce(response({ error: { kind: 'unexpected', detail: 'bad', param: null } }, 400))
      .mockResolvedValueOnce(response({ error: { kind: 'date_not_available', detail: 'bad', param: null } }, 500))
      .mockResolvedValueOnce(unreadable)
      .mockRejectedValueOnce(new TypeError('offline'))
    vi.stubGlobal('fetch', fetch)

    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({ kind: 'network' })
  })

  it('does not turn an aborted request into a network error', async () => {
    const controller = new AbortController()
    controller.abort()
    const abortError = new DOMException('aborted', 'AbortError')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abortError))

    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close', controller.signal)).rejects.toBe(abortError)
    expect(abortError).not.toBeInstanceOf(PremiumRequestError)
  })
})
