import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import type { ReactNode } from 'react'
import App from './App'

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  ScatterChart: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  CartesianGrid: () => null,
  XAxis: ({ domain, type, tickFormatter }: { domain: number[]; type: string; tickFormatter: (value: number) => string }) => <div data-testid="x-axis" data-domain={JSON.stringify(domain)} data-type={type} data-tick={tickFormatter(7000)} />,
  YAxis: ({ domain, type, tickFormatter }: { domain: number[]; type: string; tickFormatter: (value: number) => string }) => <div data-testid="y-axis" data-domain={JSON.stringify(domain)} data-type={type} data-tick={tickFormatter(0)} />,
  Tooltip: () => null,
  Legend: () => <div>Calls · Puts</div>,
  ReferenceLine: ({ x, stroke, label }: { x: number; stroke: string; label: { value: string } }) => <div data-testid="reference-line" data-x={x} data-stroke={stroke} data-label={label.value} />,
  Scatter: ({ name, data }: { name: string; data: unknown[] }) => <div data-testid={`${name}-series`} data-points={JSON.stringify(data)} />,
}))

const chain = {
  target_trade_date: '2026-09-17',
  option_product: 'MO',
  price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [{
    expiry_date: '2026-09-25',
    futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
    calls: [{ instrument_id: 'C1', strike: 7000, price: null }],
    puts: [{ instrument_id: 'P1', strike: 7000, price: 0 }],
  }],
}

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response
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
    expect(within(results).getByText('7312.5')).toBeTruthy()
    expect(within(results).getByText('Call 1 · Put 1')).toBeTruthy()
    expect(within(results).getByText('1')).toBeTruthy()
    const details = within(results).getByText('合约明细').closest('details')
    expect(details?.open).toBe(false)
    fireEvent.click(within(results).getByText('合约明细'))
    expect(details?.open).toBe(true)
    expect(within(results).getByText('C1')).toBeTruthy()
    expect(within(results).getByText('P1')).toBeTruthy()
    expect(within(results).getByText('—')).toBeTruthy()
    expect(within(results).getByText('0.0')).toBeTruthy()
    expect(within(results).getAllByText('7000.0')).toHaveLength(2)

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
          futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
          calls: [{ instrument_id: 'arbitrary-a', strike: 7000, price: null }, { instrument_id: 'arbitrary-b', strike: 8000, price: 9 }],
          puts: [{ instrument_id: 'arbitrary-c', strike: 7000, price: 0 }],
        },
        {
          expiry_date: '2026-10-23',
          futures: { instrument_id: 'IM2610.CFE', price: 7560.25 },
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
      expect(within(section).getAllByTestId('reference-line').map((line) => line.getAttribute('data-x'))[0]).toBe('7312.45')
      expect(within(section).getByTestId('x-axis').getAttribute('data-type')).toBe('number')
      expect(within(section).getByTestId('x-axis').getAttribute('data-domain')).toBe('[7000,7700]')
      expect(within(section).getByTestId('x-axis').getAttribute('data-tick')).toBe('7000.0')
      expect(within(section).getByTestId('y-axis').getAttribute('data-type')).toBe('number')
      expect(within(section).getByTestId('y-axis').getAttribute('data-tick')).toBe('0.0')
      expect(within(section).getByText('Calls · Puts')).toBeTruthy()
    }
    const first = sections[0]
    const second = sections[1]
    expect(within(first).getAllByTestId('reference-line').map((line) => line.getAttribute('data-x'))).toEqual(['7312.45', '7487.6'])
    expect(within(second).getAllByTestId('reference-line').map((line) => line.getAttribute('data-x'))).toEqual(['7312.45', '7560.25'])
    expect(within(first).getByText('Futures：IM2609.CFE · 7487.6')).toBeTruthy()
    expect(within(second).getByText('Futures：IM2610.CFE · 7560.3')).toBeTruthy()
    expect(within(first).getAllByTestId('reference-line')[0].getAttribute('data-label')).toBe('Spot 7312.5')
    expect(within(second).getAllByTestId('reference-line')[1].getAttribute('data-label')).toBe('IM 7560.3')
    const calls = JSON.parse(within(first).getByTestId('Calls-series').getAttribute('data-points')!)
    const puts = JSON.parse(within(first).getByTestId('Puts-series').getAttribute('data-points')!)
    expect(calls).toEqual([{ instrument_id: 'arbitrary-b', strike: 8000, price: 9, side: 'Call' }])
    expect(puts).toEqual([{ instrument_id: 'arbitrary-c', strike: 7000, price: 0, side: 'Put' }])
    expect(within(first).getByText(/1 个合约缺少所选价格/)).toBeTruthy()
    fireEvent.click(within(first).getByText('合约明细'))
    expect(within(first).getByText('arbitrary-b')).toBeTruthy()
    expect(within(first).getByText('Call 2 · Put 1')).toBeTruthy()

    const shrink = screen.getByRole('button', { name: '缩小行权价视窗' })
    expect(shrink.hasAttribute('disabled')).toBe(true)
    fireEvent.click(screen.getByRole('button', { name: '扩大行权价视窗' }))
    expect(screen.getByText('行权价视窗：±400 点')).toBeTruthy()
    for (const section of sections) {
      expect(within(section).getByTestId('x-axis').getAttribute('data-domain')).toBe('[6900,7800]')
    }
    fireEvent.click(shrink)
    expect(shrink.hasAttribute('disabled')).toBe(true)
    expect(screen.getByText('行权价视窗：±300 点')).toBeTruthy()
  })

  it('shows an all-null expiry without losing contract facts', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({
      ...chain,
      expiries: [{
        expiry_date: '2026-09-25',
        futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
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

  it('keeps the shared strike half range when the selected date changes', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(chain)))
    render(<App />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
    await screen.findByRole('region', { name: '期权链结果' })
    fireEvent.click(screen.getByRole('button', { name: '扩大行权价视窗' }))
    fireEvent.change(dateInput(), { target: { value: '2026-09-18' } })

    const results = await screen.findByRole('region', { name: '期权链结果' })
    expect(within(results).getByText('行权价视窗：±400 点')).toBeTruthy()
    expect(within(results).getByTestId('x-axis').getAttribute('data-domain')).toBe('[6900,7800]')
  })

  it.each([
    ['invalid_request', '请求日期或参数无效'],
    ['unsupported_query', '当前不支持此查询'],
    ['date_not_available', '该日期无可用数据'],
    ['option_chain_unavailable', '当前无法生成完整期权链'],
    ['service_not_wired', '数据服务尚未接线'],
  ])('maps %s without interpreting detail', async (kind, title) => {
    const status = kind === 'date_not_available' ? 404 : kind === 'invalid_request' || kind === 'unsupported_query' ? 400 : 503
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { kind, detail: 'backend detail' } }, status)))
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
