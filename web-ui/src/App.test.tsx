import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import type { ReactNode } from 'react'
import App from './App'

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  ScatterChart: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CartesianGrid: () => null,
  XAxis: ({ domain, type }: { domain: number[]; type: string }) => <div data-testid="x-axis" data-domain={JSON.stringify(domain)} data-type={type} />,
  YAxis: ({ domain, type }: { domain: number[]; type: string }) => <div data-testid="y-axis" data-domain={JSON.stringify(domain)} data-type={type} />,
  Tooltip: () => null,
  Legend: () => <div>Calls · Puts</div>,
  ReferenceLine: ({ x }: { x: number }) => <div data-testid="reference-line" data-x={x} />,
  Scatter: ({ name, data }: { name: string; data: unknown[] }) => <div data-testid={`${name}-series`} data-points={JSON.stringify(data)} />,
}))

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
    const details = within(results).getByText('合约明细').closest('details')
    expect(details?.open).toBe(false)
    fireEvent.click(within(results).getByText('合约明细'))
    expect(details?.open).toBe(true)
    expect(within(results).getByText('C1')).toBeTruthy()
    expect(within(results).getByText('P1')).toBeTruthy()
    expect(within(results).getByText('—')).toBeTruthy()
    expect(within(results).getByText('0')).toBeTruthy()

    fireEvent.change(dateInput(), { target: { value: '' } })
    expect(screen.getByRole('status').textContent).toContain('请选择')
    expect(screen.queryByRole('region', { name: '期权链结果' })).toBeNull()
  })

  it('keeps expiry order, separates sides, and uses the response reference in each chart', async () => {
    const twoExpiries = {
      ...chain,
      expiries: [
        {
          expiry_date: '2026-09-25',
          calls: [{ instrument_id: 'arbitrary-a', strike: 7000, price: null }, { instrument_id: 'arbitrary-b', strike: 7100, price: 9 }],
          puts: [{ instrument_id: 'arbitrary-c', strike: 7000, price: 0 }],
        },
        {
          expiry_date: '2026-10-23',
          calls: [{ instrument_id: 'arbitrary-d', strike: 7200, price: 12 }],
          puts: [{ instrument_id: 'arbitrary-e', strike: 7300, price: 5 }],
        },
      ],
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(twoExpiries)))
    render(<App />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })

    const sections = await screen.findAllByRole('region', { name: /到期日$/ })
    expect(sections.map((section) => within(section).getByRole('heading', { level: 3 }).textContent))
      .toEqual(['2026-09-25', '2026-10-23'])
    for (const section of sections) {
      expect(within(section).getByTestId('reference-line').getAttribute('data-x')).toBe('7312.45')
      expect(within(section).getByTestId('x-axis').getAttribute('data-type')).toBe('number')
      expect(within(section).getByTestId('y-axis').getAttribute('data-type')).toBe('number')
      expect(within(section).getByText('Calls · Puts')).toBeTruthy()
    }
    const first = sections[0]
    const calls = JSON.parse(within(first).getByTestId('Calls-series').getAttribute('data-points')!)
    const puts = JSON.parse(within(first).getByTestId('Puts-series').getAttribute('data-points')!)
    expect(calls).toEqual([{ instrument_id: 'arbitrary-b', strike: 7100, price: 9, side: 'Call' }])
    expect(puts).toEqual([{ instrument_id: 'arbitrary-c', strike: 7000, price: 0, side: 'Put' }])
    expect(within(first).getByText(/1 个合约缺少所选价格/)).toBeTruthy()
    const [minimum, maximum] = JSON.parse(within(first).getByTestId('x-axis').getAttribute('data-domain')!)
    expect(minimum).toBeLessThan(7000)
    expect(maximum).toBeGreaterThan(7312.45)
  })

  it('shows an all-null expiry without losing contract facts', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      ...chain,
      expiries: [{
        expiry_date: '2026-09-25',
        calls: [{ instrument_id: 'C1', strike: 7000, price: null }],
        puts: [{ instrument_id: 'P1', strike: 7200, price: null }],
      }],
    })))
    render(<App />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })

    const expiry = await screen.findByRole('region', { name: '2026-09-25 到期日' })
    expect(within(expiry).getByText('Call 1 · Put 1')).toBeTruthy()
    expect(within(expiry).getByText(/2 个合约缺少所选价格/)).toBeTruthy()
    expect(within(expiry).getByText('该到期日没有可绘制的价格。')).toBeTruthy()
    fireEvent.click(within(expiry).getByText('合约明细'))
    expect(within(expiry).getByText('C1')).toBeTruthy()
    expect(within(expiry).getByText('P1')).toBeTruthy()
    expect(within(expiry).getAllByText('—')).toHaveLength(2)
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
