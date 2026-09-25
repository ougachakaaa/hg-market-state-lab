import { afterEach, describe, expect, it, vi } from 'vitest'
import { loadMoOptionPremiumPlane, PremiumRequestError } from './moOptionPremium'
import type { PremiumPlane } from './moOptionPremium'

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
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(plane)))

    const result = await loadMoOptionPremiumPlane('2026-09-21', 'close')

    expect(result.plane.points[0].metrics.underlying_spot.time_value.unannualized.points).toBe(-1)
    expect(result.plane.points[0].metrics.expiry_futures.time_value.annualized.yield).toBeNull()
    expect(result.rawPayload).toBe(plane)
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
})
