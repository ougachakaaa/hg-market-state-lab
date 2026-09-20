import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import App from './App'

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

function dateInput(): HTMLInputElement {
  return screen.getByLabelText('目标交易日') as HTMLInputElement
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('MO option chain page', () => {
  it('starts idle, loads on date selection, and shows expandable null and zero prices', async () => {
    let finish!: (value: Response) => void
    const fetch = vi.fn().mockImplementation(() => new Promise<Response>((resolve) => { finish = resolve }))
    vi.stubGlobal('fetch', fetch)
    render(<App />)

    expect(screen.getByRole('status').textContent).toContain('请选择')
    expect(fetch).not.toHaveBeenCalled()
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
    expect(screen.getByRole('status').textContent).toContain('正在加载 2026-09-17')
    finish(response(chain))

    const results = await screen.findByRole('region', { name: '期权链结果' })
    expect(within(results).getByText('000852.SH')).toBeTruthy()
    expect(within(results).getByText('7312.45')).toBeTruthy()
    expect(within(results).getByText('Call 1 · Put 1')).toBeTruthy()
    expect(within(results).getByText('1')).toBeTruthy()
    const summary = within(results).getByText('2026-09-25')
    expect(summary.closest('details')?.open).toBe(false)
    fireEvent.click(summary)
    expect(summary.closest('details')?.open).toBe(true)
    expect(within(results).getByText('C1')).toBeTruthy()
    expect(within(results).getByText('P1')).toBeTruthy()
    expect(within(results).getByText('—')).toBeTruthy()
    expect(within(results).getByText('0')).toBeTruthy()

    fireEvent.change(dateInput(), { target: { value: '' } })
    expect(screen.getByRole('status').textContent).toContain('请选择')
    expect(screen.queryByRole('region', { name: '期权链结果' })).toBeNull()
  })

  it.each([
    ['invalid_request', '请求日期或参数无效'],
    ['unsupported_query', '当前不支持此查询'],
    ['date_not_available', '该日期无可用数据'],
    ['option_chain_unavailable', '当前无法生成完整期权链'],
    ['service_not_wired', '数据服务尚未接线'],
  ])('maps %s without interpreting detail', async (kind, title) => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { kind, detail: 'backend detail' } }, false)))
    render(<App />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })

    const alert = await screen.findByRole('alert')
    expect(within(alert).getByText(title)).toBeTruthy()
    expect(within(alert).getByText('backend detail')).toBeTruthy()
  })

  it('does not let an older response overwrite a newer date', async () => {
    const pending: Array<{ signal: AbortSignal; finish: (value: Response) => void }> = []
    vi.stubGlobal('fetch', vi.fn().mockImplementation((_url: string, options: RequestInit) => (
      new Promise<Response>((resolve) => pending.push({ signal: options.signal!, finish: resolve }))
    )))
    render(<App />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
    fireEvent.change(dateInput(), { target: { value: '2026-09-18' } })

    expect(pending[0].signal.aborted).toBe(true)
    pending[1].finish(response({ ...chain, target_trade_date: '2026-09-18' }))
    expect((await screen.findByRole('region', { name: '期权链结果' })).textContent).toContain('2026-09-18')
    pending[0].finish(response(chain))
    await Promise.resolve()
    expect(screen.getByRole('region', { name: '期权链结果' }).textContent).not.toContain('2026-09-17')
  })

  it('shows a transport failure without a stale result', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response(chain)).mockRejectedValueOnce(new TypeError('offline'))
    vi.stubGlobal('fetch', fetch)
    render(<App />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
    await screen.findByRole('region', { name: '期权链结果' })
    fireEvent.change(dateInput(), { target: { value: '2026-09-18' } })

    expect(screen.queryByRole('region', { name: '期权链结果' })).toBeNull()
    const alert = await screen.findByRole('alert')
    expect(within(alert).getByText('无法连接数据服务')).toBeTruthy()
  })
})
