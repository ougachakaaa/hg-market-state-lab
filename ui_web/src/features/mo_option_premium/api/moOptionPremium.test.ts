import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { loadMoOptionPremiumPlane, PremiumRequestError } from './moOptionPremium'
import type { PremiumPlane } from './moOptionPremium'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'

let releaseBoundary: () => void
beforeEach(() => { releaseBoundary = installRequestBoundary(createRequestBoundary(() => {})) })
afterEach(() => releaseBoundary())

const leaf = (value: number | null) => ({ points: value, yield: value })
const plane = {
  observation: { kind: 'trade_date', value: '2026-09-21' }, option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7300 },
  expiries: [{ expiry_date: '2026-09-25', dte: 5, futures: null }],
  points: [{
    instrument_id: 'MO', expiry_date: '2026-09-25', option_type: 'call', strike: 7000, premium: 0,
    metrics: {
      underlying_spot: { total: { unannualized: leaf(0), annualized: leaf(0) }, time_value: { unannualized: leaf(-1), annualized: leaf(-2) } },
      expiry_futures: { total: { unannualized: leaf(0), annualized: leaf(0) }, time_value: { unannualized: leaf(null), annualized: leaf(null) } },
    },
  }],
} satisfies PremiumPlane

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response
}

afterEach(() => vi.unstubAllGlobals())

describe('loadMoOptionPremiumPlane', () => {
  it('validates and returns the complete structured response unchanged', async () => {
    const fetch = vi.fn().mockResolvedValue(response(plane))
    vi.stubGlobal('fetch', fetch)

    const controller = new AbortController()
    const result = await loadMoOptionPremiumPlane('2026-09-21', 'close', controller.signal)

    expect(result.plane.points[0].metrics.underlying_spot.time_value.unannualized.points).toBe(-1)
    expect(result.plane.points[0].metrics.expiry_futures.time_value.annualized.yield).toBeNull()
    expect(result.rawPayload).toBe(plane)
    const [url, options] = fetch.mock.calls[0] as [string, RequestInit]
    expect([...new URL(url, 'http://localhost').searchParams.entries()]).toEqual([
      ['as_of', '2026-09-21'], ['option_product', 'MO'], ['price_type', 'close'],
    ])
    expect(options.signal).toBeInstanceOf(AbortSignal)
  })

  it('rejects a response missing a structured metric leaf', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ points: [] })))

    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close'))
      .rejects.toMatchObject({ kind: 'invalid_response' satisfies PremiumRequestError['kind'] })
  })

  it('maps declared backend failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      error: { kind: 'premium_plane_unavailable', detail: 'incomplete', param: null },
    }, 503)))

    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close'))
      .rejects.toMatchObject({ kind: 'premium_plane_unavailable' })
  })

  it('classifies malformed JSON, invalid statuses, and network failures', async () => {
    const malformedJson = { ok: true, status: 200, json: async () => { throw new SyntaxError('bad json') } } as unknown as Response
    const fetch = vi.fn()
      .mockResolvedValueOnce(malformedJson)
      .mockResolvedValueOnce(response({ error: { kind: 'date_not_available', detail: 'missing' } }))
      .mockRejectedValueOnce(new TypeError('offline'))
    vi.stubGlobal('fetch', fetch)

    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({ kind: 'invalid_response' })
    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({ kind: 'network' })
  })

  it('does not adapt an aborted request into a transport error', async () => {
    const controller = new AbortController()
    controller.abort()
    const abortError = new DOMException('aborted', 'AbortError')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abortError))

    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close', controller.signal)).rejects.toMatchObject({ name: 'AbortError' })
    expect(abortError).not.toBeInstanceOf(PremiumRequestError)
  })
})


it.each([[401, 'authentication_required'], [403, 'origin_forbidden'], [500, 'internal_error']])(
  'preserves generated access errors for HTTP %s', async (status, kind) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      error: { kind, detail: 'Access failed.', param: null },
    }, status as number)))
    await expect(loadMoOptionPremiumPlane('2026-09-21', 'close')).rejects.toMatchObject({ kind, message: 'Access failed.' })
  },
)
