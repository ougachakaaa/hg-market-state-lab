import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import type { PremiumPlane } from './api/moOptionPremium'
import App from './App'

const plane = {
  observation: { kind: 'trade_date', value: '2026-09-21' }, option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', dte: 5, futures: { instrument_id: 'IM2609.CFE', price: 7301.6 } },
    { expiry_date: '2026-10-23', dte: 33, futures: null },
  ],
  points: [
    { instrument_id: 'A', expiry_date: '2026-09-25', option_type: 'call', strike: 7012.45, premium: 1, annualized_premium_points: 0, annualized_time_value_points: 0, annualized_seller_premium_yield: 0, annualized_time_value_yield: 0 },
    { instrument_id: 'B', expiry_date: '2026-09-25', option_type: 'call', strike: 7200, premium: null, annualized_premium_points: null, annualized_time_value_points: null, annualized_seller_premium_yield: null, annualized_time_value_yield: null },
    { instrument_id: 'C', expiry_date: '2026-10-23', option_type: 'call', strike: 7305, premium: 1, annualized_premium_points: 12.34, annualized_time_value_points: -12.34, annualized_seller_premium_yield: 0.0998, annualized_time_value_yield: -0.0123 },
    { instrument_id: 'D', expiry_date: '2026-10-23', option_type: 'call', strike: 7612.45, premium: 1, annualized_premium_points: 9, annualized_time_value_points: 9, annualized_seller_premium_yield: 0.1, annualized_time_value_yield: 0.01 },
    { instrument_id: 'E', expiry_date: '2026-09-25', option_type: 'put', strike: 7300, premium: 1, annualized_premium_points: 20, annualized_time_value_points: 20, annualized_seller_premium_yield: 0.2, annualized_time_value_yield: 0.02 },
    { instrument_id: 'F', expiry_date: '2026-09-25', option_type: 'call', strike: 7700, premium: 1, annualized_premium_points: 30, annualized_time_value_points: 30, annualized_seller_premium_yield: 0.3, annualized_time_value_yield: 0.03 },
  ],
} satisfies PremiumPlane

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((accept) => { resolve = accept })
  return { promise, resolve }
}

function dateInput(): HTMLInputElement {
  return screen.getByLabelText('Observation 日期') as HTMLInputElement
}

async function load(body: PremiumPlane = plane) {
  const fetch = vi.fn().mockResolvedValue(response(body))
  vi.stubGlobal('fetch', fetch)
  render(<App />)
  fireEvent.change(dateInput(), { target: { value: '2026-09-21' } })
  const results = await screen.findByRole('region', { name: '权利金平面结果' })
  return { fetch, results }
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('MO Premium Plane page', () => {
  it('starts idle, then requests the default query and renders sparse facts', async () => {
    const fetch = vi.fn().mockResolvedValue(response(plane))
    vi.stubGlobal('fetch', fetch)
    render(<App />)

    expect(screen.getByRole('status').textContent).toContain('请选择 Observation 日期')
    expect(fetch).not.toHaveBeenCalled()
    expect((screen.getByLabelText('价格口径') as HTMLSelectElement).value).toBe('close')

    fireEvent.change(dateInput(), { target: { value: '2026-09-21' } })
    const results = await screen.findByRole('region', { name: '权利金平面结果' })
    expect(fetch).toHaveBeenCalledTimes(1)
    expect(fetch.mock.calls[0][0]).toContain('as_of=2026-09-21&option_product=MO&price_type=close')
    expect(within(results).getByText('7312.5')).toBeTruthy()
    expect(within(results).getByText('标的现价 · 7312.5')).toBeTruthy()
    expect(within(results).getByText(/IM2609\.CFE · 7301\.6/)).toBeTruthy()
    expect(within(results).getByText('无合法 futures reference')).toBeTruthy()
    expect(within(results).getAllByRole('cell', { name: '2026-10-23 无 Point' })[0].textContent).toBe('')
    expect(within(results).getByRole('cell', { name: '2026-09-25 metric unavailable' }).textContent).toBe('—')
    expect(within(results).getByText('0.0')).toBeTruthy()
    expect(within(results).getByRole('rowheader', { name: '7700.0' })).toBeTruthy()

    const referenceRow = within(results).getByRole('rowheader', { name: '7305.0' }).closest('tr')!
    expect(within(referenceRow).getByRole('rowheader').classList.contains('below-reference')).toBe(true)
    expect(within(referenceRow).getByRole('cell', { name: '2026-09-25 无 Point' }).classList.contains('above-reference')).toBe(true)
    expect(within(referenceRow).getByText('12.3').classList.contains('neutral')).toBe(true)
  })

  it('maps both metric axes and keeps all presentation interactions local', async () => {
    const { fetch, results } = await load()

    expect(within(results).getByRole<HTMLInputElement>('radio', { name: '总价值' }).checked).toBe(true)
    expect(within(results).getByRole<HTMLInputElement>('radio', { name: '点数' }).checked).toBe(true)

    fireEvent.click(within(results).getByRole('radio', { name: '时间价值' }))
    expect(within(results).getByText('-12.3')).toBeTruthy()
    expect(within(results).getByText('0.0')).toBeTruthy()

    fireEvent.click(within(results).getByRole('radio', { name: '收益率' }))
    expect(within(results).getByText('-1.23%')).toBeTruthy()
    expect(within(results).getByText('0.00%')).toBeTruthy()

    fireEvent.click(within(results).getByRole('radio', { name: '总价值' }))
    expect(within(results).getByText('9.98%')).toBeTruthy()
    expect(within(results).getByText('0.00%')).toBeTruthy()

    fireEvent.click(within(results).getByRole('radio', { name: 'Put' }))
    expect(within(results).getByText('20.00%')).toBeTruthy()
    fireEvent.click(within(results).getByRole('checkbox', { name: '2026-10-23' }))
    const last = within(results).getByRole<HTMLInputElement>('checkbox', { name: '2026-09-25' })
    expect(last.disabled).toBe(true)
    fireEvent.click(last)
    expect(last.checked).toBe(true)

    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('shows and copies the complete raw payload independently of presentation state', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    })
    const { fetch, results } = await load()

    fireEvent.click(within(results).getByText('查看原始响应'))
    const raw = JSON.stringify(plane, null, 2)
    expect(results.querySelector('pre')?.textContent).toBe(raw)
    fireEvent.click(within(results).getByRole('button', { name: '复制 JSON' }))
    expect((await within(results).findByRole('status')).textContent).toContain('已复制')
    expect(writeText).toHaveBeenCalledWith(raw)

    fireEvent.click(within(results).getByRole('radio', { name: '时间价值' }))
    fireEvent.click(within(results).getByRole('radio', { name: '收益率' }))
    fireEvent.click(within(results).getByRole('radio', { name: 'Put' }))
    fireEvent.click(within(results).getByRole('checkbox', { name: '2026-10-23' }))
    expect(results.querySelector('pre')?.textContent).toBe(raw)
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('requests on query changes, clears stale results and resets presentation defaults', async () => {
    const { fetch } = await load()
    fireEvent.click(screen.getByRole('radio', { name: 'Put' }))
    fireEvent.change(screen.getByLabelText('价格口径'), { target: { value: 'high' } })

    expect(screen.queryByRole('region', { name: '权利金平面结果' })).toBeNull()
    expect(screen.queryByText('查看原始响应')).toBeNull()
    expect(screen.getByRole('status').textContent).toContain('2026-09-21 · high')
    await screen.findByRole('region', { name: '权利金平面结果' })
    expect(fetch).toHaveBeenCalledTimes(2)
    expect(fetch.mock.calls[1][0]).toContain('price_type=high')
    expect(screen.getByRole<HTMLInputElement>('radio', { name: 'Call' }).checked).toBe(true)

    fireEvent.change(dateInput(), { target: { value: '' } })
    expect(screen.getByRole('status').textContent).toContain('请选择 Observation 日期')
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('replaces the raw payload only after the new query succeeds', async () => {
    const nextResponse = deferred<Response>()
    const nextPlane = { ...plane, price_type: 'high' as const }
    const fetch = vi.fn()
      .mockResolvedValueOnce(response(plane))
      .mockReturnValueOnce(nextResponse.promise)
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-21' } })
    const firstResults = await screen.findByRole('region', { name: '权利金平面结果' })
    fireEvent.click(within(firstResults).getByText('查看原始响应'))
    expect(firstResults.querySelector('pre')?.textContent).toBe(JSON.stringify(plane, null, 2))

    fireEvent.change(screen.getByLabelText('价格口径'), { target: { value: 'high' } })
    expect(screen.queryByText('查看原始响应')).toBeNull()
    nextResponse.resolve(response(nextPlane))

    const nextResults = await screen.findByRole('region', { name: '权利金平面结果' })
    fireEvent.click(within(nextResults).getByText('查看原始响应'))
    expect(nextResults.querySelector('pre')?.textContent).toBe(JSON.stringify(nextPlane, null, 2))
  })

  it('shows a projection empty state without treating it as a backend failure', async () => {
    const onlyCall = { ...plane, points: plane.points.filter((point) => point.option_type === 'call') }
    const { results } = await load(onlyCall)
    fireEvent.click(within(results).getByRole('radio', { name: 'Put' }))

    expect(within(results).getByText('当前选择下无 analytical observation。')).toBeTruthy()
    expect(within(results).getByText('Observation')).toBeTruthy()
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('maps classified backend failures and never leaves a previous result visible', async () => {
    const fetch = vi.fn()
      .mockResolvedValueOnce(response(plane))
      .mockResolvedValueOnce(response({
        error: { kind: 'premium_plane_unavailable', detail: 'incomplete plane', param: null },
      }, 503))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-21' } })
    await screen.findByRole('region', { name: '权利金平面结果' })

    fireEvent.change(dateInput(), { target: { value: '2026-09-22' } })
    const alert = await screen.findByRole('alert')
    expect(within(alert).getByText('当前无法生成权利金平面')).toBeTruthy()
    expect(within(alert).getByText('incomplete plane')).toBeTruthy()
    expect(screen.queryByRole('region', { name: '权利金平面结果' })).toBeNull()
    expect(screen.queryByText('查看原始响应')).toBeNull()
  })

  it('does not let an older request overwrite a newer query', async () => {
    const first = deferred<Response>()
    const second = deferred<Response>()
    vi.stubGlobal('fetch', vi.fn()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise))
    render(<App />)

    fireEvent.change(dateInput(), { target: { value: '2026-09-20' } })
    fireEvent.change(dateInput(), { target: { value: '2026-09-21' } })
    second.resolve(response(plane))
    expect(await screen.findByText('2026-09-21 · MO')).toBeTruthy()

    first.resolve(response({ ...plane, observation: { kind: 'trade_date', value: '2026-09-20' } }))
    await Promise.resolve()
    expect(screen.queryByText('2026-09-20 · MO')).toBeNull()
    expect(screen.getByText('2026-09-21 · MO')).toBeTruthy()
  })
})
