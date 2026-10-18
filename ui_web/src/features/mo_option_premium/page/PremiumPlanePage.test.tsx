import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import type { PremiumPlane } from '../api/moOptionPremium'
import PremiumPlanePage from './PremiumPlanePage'

function leaf(points: number | null, yieldValue: number | null) {
  return { points, yield: yieldValue }
}

const plane = {
  observation: { kind: 'trade_date', value: '2026-09-21' }, option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', dte: 5, futures: { instrument_id: 'IM2609.CFE', price: 7301.6 } },
    { expiry_date: '2026-10-23', dte: 33, futures: null },
  ],
  points: [
    { instrument_id: 'A', expiry_date: '2026-09-25', option_type: 'call', strike: 7000, premium: 0, metrics: {
      underlying_spot: { total: { unannualized: leaf(0, 0), annualized: leaf(0, 0) }, time_value: { unannualized: leaf(-3, -0.003), annualized: leaf(-30, -0.03) } },
      expiry_futures: { total: { unannualized: leaf(0, 0), annualized: leaf(0, 0) }, time_value: { unannualized: leaf(-2, -0.002), annualized: leaf(-20, -0.02) } },
    } },
    { instrument_id: 'B', expiry_date: '2026-10-23', option_type: 'call', strike: 7300, premium: 1, metrics: {
      underlying_spot: { total: { unannualized: leaf(1, 0.001), annualized: leaf(10, 0.01) }, time_value: { unannualized: leaf(-1, -0.001), annualized: leaf(-10, -0.01) } },
      expiry_futures: { total: { unannualized: leaf(1, null), annualized: leaf(10, null) }, time_value: { unannualized: leaf(null, null), annualized: leaf(null, null) } },
    } },
    { instrument_id: 'P', expiry_date: '2026-09-25', option_type: 'put', strike: 7300, premium: 1, metrics: {
      underlying_spot: { total: { unannualized: leaf(20, 0.02), annualized: leaf(200, 0.2) }, time_value: { unannualized: leaf(20, 0.02), annualized: leaf(200, 0.2) } },
      expiry_futures: { total: { unannualized: leaf(20, 0.02), annualized: leaf(200, 0.2) }, time_value: { unannualized: leaf(20, 0.02), annualized: leaf(200, 0.2) } },
    } },
  ],
} satisfies PremiumPlane

function response(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response
}

async function load() {
  const fetch = vi.fn().mockResolvedValue(response(plane))
  vi.stubGlobal('fetch', fetch)
  render(<PremiumPlanePage />)
  fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-21' } })
  const results = await screen.findByRole('region', { name: 'Premium plane results' })
  return { fetch, results }
}

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('MO Premium Plane page', () => {
  it('defaults to the authority-defined four-axis presentation', async () => {
    const { fetch, results } = await load()

    expect(fetch).toHaveBeenCalledTimes(1)
    expect(within(results).getByRole<HTMLInputElement>('radio', { name: 'Underlying spot' }).checked).toBe(true)
    expect(within(results).getByRole<HTMLInputElement>('radio', { name: 'Total value' }).checked).toBe(true)
    expect(within(results).getByRole<HTMLInputElement>('radio', { name: 'Annualized' }).checked).toBe(true)
    expect(within(results).getByRole<HTMLInputElement>('radio', { name: 'Points' }).checked).toBe(true)
    expect(within(results).getByText('10.0')).toBeTruthy()
  })

  it('selects structured coordinates locally and shows unavailable futures facts without fallback', async () => {
    const { fetch, results } = await load()

    fireEvent.click(within(results).getByRole('radio', { name: 'Same-expiry futures' }))
    fireEvent.click(within(results).getByRole('radio', { name: 'Time value' }))
    fireEvent.click(within(results).getByRole('radio', { name: 'Unannualized' }))
    expect(within(results).getByText('-2.0')).toBeTruthy()
    expect(within(results).getByRole('cell', { name: '2026-10-23 metric unavailable' }).textContent).toBe('—')
    fireEvent.click(within(results).getByRole('radio', { name: 'Yield' }))
    expect(within(results).getByText('-0.20%')).toBeTruthy()
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('keeps the complete raw payload independent of presentation switches', async () => {
    const { fetch, results } = await load()
    fireEvent.click(within(results).getByText('View raw response'))
    const raw = JSON.stringify(plane, null, 2)
    expect(results.querySelector('pre')?.textContent).toBe(raw)
    fireEvent.click(within(results).getByRole('radio', { name: 'Same-expiry futures' }))
    fireEvent.click(within(results).getByRole('radio', { name: 'Yield' }))
    expect(results.querySelector('pre')?.textContent).toBe(raw)
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})
