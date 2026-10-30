import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { useOptionChain } from './useOptionChain'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'

let releaseBoundary: () => void
beforeEach(() => { releaseBoundary = installRequestBoundary(createRequestBoundary(() => {})) })
afterEach(() => releaseBoundary())

const chain = {
  target_trade_date: '2026-09-18', option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [{
    expiry_date: '2026-09-25', futures: null,
    calls: [{ instrument_id: 'C1', strike: 7300, price: 10 }], puts: [],
  }],
}

function response(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response
}

afterEach(() => vi.unstubAllGlobals())

describe('useOptionChain', () => {
  it('contains stale-query protection while retaining cross-query visualization preferences', async () => {
    const pending: Array<{ signal: AbortSignal; finish: (value: Response) => void }> = []
    vi.stubGlobal('fetch', vi.fn().mockImplementation((_url: string, options: RequestInit) => (
      new Promise<Response>((resolve) => pending.push({ signal: options.signal!, finish: resolve }))
    )))
    const { result } = renderHook(() => useOptionChain())

    act(() => {
      result.current.changeSeriesColor('call', '#e11d48')
      result.current.expandViewport()
      result.current.selectDate('2026-09-17')
      result.current.selectDate('2026-09-18')
    })

    expect(pending[0].signal.aborted).toBe(true)
    await act(async () => pending[1].finish(response(chain)))
    await waitFor(() => expect(result.current.page.status).toBe('success'))
    expect(result.current.selectedExpiries).toEqual(['2026-09-25'])
    expect(result.current.seriesColors.call).toBe('#e11d48')
    expect(result.current.strikeHalfRangePoints).toBe(400)

    await act(async () => pending[0].finish(response({ ...chain, target_trade_date: '2026-09-17' })))
    expect(result.current.page.status === 'success' && result.current.page.chain.target_trade_date).toBe('2026-09-18')
  })
})
