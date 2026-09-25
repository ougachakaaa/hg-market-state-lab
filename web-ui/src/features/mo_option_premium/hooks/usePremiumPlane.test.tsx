import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { PremiumPlane } from '../api/moOptionPremium'
import { usePremiumPlane } from './usePremiumPlane'

const leaf = (value: number | null) => ({ points: value, yield: value })
const plane = {
  observation: { kind: 'trade_date', value: '2026-09-18' }, option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7300 },
  expiries: [{ expiry_date: '2026-09-25', dte: 7, futures: null }],
  points: [{
    instrument_id: 'MO', expiry_date: '2026-09-25', option_type: 'call', strike: 7300, premium: 0,
    metrics: {
      underlying_spot: { total: { unannualized: leaf(0), annualized: leaf(0) }, time_value: { unannualized: leaf(0), annualized: leaf(0) } },
      expiry_futures: { total: { unannualized: leaf(null), annualized: leaf(null) }, time_value: { unannualized: leaf(null), annualized: leaf(null) } },
    },
  }],
} satisfies PremiumPlane

function response(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response
}

afterEach(() => vi.unstubAllGlobals())

describe('usePremiumPlane', () => {
  it('clears current results, resets presentation state, and rejects stale completion', async () => {
    const pending: Array<{ signal: AbortSignal; finish: (value: Response) => void }> = []
    vi.stubGlobal('fetch', vi.fn().mockImplementation((_url: string, options: RequestInit) => (
      new Promise<Response>((resolve) => pending.push({ signal: options.signal!, finish: resolve }))
    )))
    const { result } = renderHook(() => usePremiumPlane())

    act(() => result.current.selectDate('2026-09-17'))
    act(() => result.current.setSelectedRepresentation('yield'))
    act(() => result.current.selectDate('2026-09-18'))

    expect(pending[0].signal.aborted).toBe(true)
    expect(result.current.page.status).toBe('loading')
    expect(result.current.projection).toBeNull()
    expect(result.current.selectedRepresentation).toBe('points')
    await act(async () => pending[1].finish(response(plane)))
    await waitFor(() => expect(result.current.page.status).toBe('success'))
    expect(result.current.selectedExpiries).toEqual(['2026-09-25'])
    act(() => result.current.toggleExpiry('2026-09-25'))
    expect(result.current.selectedExpiries).toEqual(['2026-09-25'])

    await act(async () => pending[0].finish(response({ ...plane, observation: { kind: 'trade_date', value: '2026-09-17' } })))
    expect(result.current.page.status === 'success' && result.current.page.plane.observation.value).toBe('2026-09-18')
    expect(result.current.page.status === 'success' && result.current.page.rawPayload).toBe(plane)
  })

  it('removes a successful plane and raw payload before exposing a later failure', async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce(response(plane))
      .mockRejectedValueOnce(new TypeError('offline'))
    vi.stubGlobal('fetch', fetch)
    const { result } = renderHook(() => usePremiumPlane())

    act(() => result.current.selectDate('2026-09-18'))
    await waitFor(() => expect(result.current.page.status).toBe('success'))
    act(() => result.current.selectPriceType('high'))
    expect(result.current.page.status).toBe('loading')
    expect(result.current.projection).toBeNull()
    await waitFor(() => expect(result.current.page.status).toBe('error'))
    expect(result.current.page.status === 'error' && result.current.page.error.kind).toBe('network')
  })
})
