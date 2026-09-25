import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import type { PlotParams } from 'react-plotly.js'
import OptionChainPage from './OptionChainPage'

vi.mock('react-plotly.js', () => ({
  default: ({ data, layout, config, useResizeHandler, style }: PlotParams) => (
    <div data-testid="plot" data-plot={JSON.stringify({ data, layout, config, useResizeHandler, style })} />
  ),
}))

const chain = {
  target_trade_date: '2026-09-17', option_product: 'MO', price_type: 'close',
  underlying: { instrument_id: '000852.SH', price: 7312.45 },
  expiries: [
    { expiry_date: '2026-09-25', futures: { instrument_id: 'IM2609.CFE', price: 7487.6 },
      calls: [{ instrument_id: 'A-call', strike: 7200, price: 200 }, { instrument_id: 'A-out', strike: 8000, price: 2000 }],
      puts: [{ instrument_id: 'A-zero', strike: 7100, price: 0 }, { instrument_id: 'A-null', strike: 7300, price: null }] },
    { expiry_date: '2026-10-23', futures: { instrument_id: 'IM2610.CFE', price: 7560.25 },
      calls: [{ instrument_id: 'B-call', strike: 7200, price: 450 }],
      puts: [{ instrument_id: 'B-put', strike: 7300, price: 10 }] },
    { expiry_date: '2026-11-27', futures: null,
      calls: [{ instrument_id: 'C-call', strike: 7200, price: 50 }],
      puts: [{ instrument_id: 'C-put', strike: 7300, price: 5 }] },
  ],
}

function response(body: unknown, status = 200): Response {
  return { ok: status >= 200 && status < 300, status, json: async () => body } as Response
}

function plot() {
  return JSON.parse(screen.getByTestId('plot').getAttribute('data-plot')!)
}

function dateInput(): HTMLInputElement {
  return screen.getByLabelText('目标交易日') as HTMLInputElement
}

async function load(body: unknown = chain) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(body)))
  render(<OptionChainPage />)
  fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
  return screen.findByRole('region', { name: '期权链结果' })
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('MO option chain combined page', () => {
  it('starts idle and does not request a chain until a date is selected', () => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    render(<OptionChainPage />)
    expect(screen.getByRole('status').textContent).toContain('请选择目标交易日')
    expect(fetch).not.toHaveBeenCalled()
    fireEvent.change(dateInput(), { target: { value: '' } })
    expect(screen.queryByRole('region', { name: '期权链结果' })).toBeNull()
  })

  it('starts idle and loads one chart with every expiry selected and ordered details', async () => {
    const results = await load()
    expect(within(results).getAllByTestId('plot')).toHaveLength(1)
    expect(screen.getAllByRole('checkbox')).toHaveLength(3)
    expect(screen.getAllByRole<HTMLInputElement>('checkbox').every((input) => input.checked)).toBe(true)
    expect(plot().data.map((trace: { name: string }) => trace.name)).toEqual([
      '2026-09-25 Call', '2026-09-25 Put',
      '2026-10-23 Call', '2026-10-23 Put',
      '2026-11-27 Call', '2026-11-27 Put',
    ])
    expect(screen.getAllByRole('region', { name: /到期日$/ }).map((section) => within(section).getByRole('heading', { level: 3 }).textContent))
      .toEqual(['2026-09-25', '2026-10-23', '2026-11-27'])
    expect(plot().layout.shapes.map((shape: { x0: number }) => shape.x0)).toEqual([7312.45, 7487.6, 7560.25])
    expect(plot().layout.xaxis.range).toEqual([7000.45, 7624.45])
    expect(plot().layout.yaxis.range[1]).toBe(600)
    expect(plot().layout.showlegend).toBe(false)
    expect(plot().useResizeHandler).toBe(true)
    const optionLegend = screen.getByRole('region', { name: 'Call 与 Put 图例' })
    expect(within(optionLegend).getAllByRole('listitem').map((item) => item.textContent)).toEqual([
      '2026-09-25 Call', '2026-09-25 Put',
      '2026-10-23 Call', '2026-10-23 Put',
      '2026-11-27 Call', '2026-11-27 Put',
    ])
    const futuresLegend = screen.getByRole('region', { name: 'Futures 图例' })
    expect(within(futuresLegend).getAllByRole('listitem').map((item) => item.textContent)).toEqual([
      'IM2609.CFE · 7487.6', 'IM2610.CFE · 7560.3',
    ])
    expect((within(optionLegend).getAllByRole('listitem')[0].querySelector('.chart-legend-symbol') as HTMLElement).style.color)
      .toBe('rgb(37, 99, 235)')
    expect((within(futuresLegend).getAllByRole('listitem')[1].querySelector('.chart-legend-symbol') as HTMLElement).style.color)
      .toBe('rgba(124, 58, 237, 0.575)')
    expect(within(futuresLegend).queryByText(/2026-11-27/)).toBeNull()
    expect((screen.getByLabelText('Call 颜色') as HTMLInputElement).value).toBe('#2563eb')
    expect((screen.getByLabelText('Put 颜色') as HTMLInputElement).value).toBe('#ea580c')
    expect((screen.getByLabelText('Futures 颜色') as HTMLInputElement).value).toBe('#7c3aed')
    expect(screen.getByRole('checkbox', { name: '2026-09-25' }).closest('label')?.querySelectorAll('.expiry-swatch')).toHaveLength(3)
    expect(screen.getByRole('checkbox', { name: '2026-11-27' }).closest('label')?.querySelectorAll('.expiry-swatch')).toHaveLength(2)
  })

  it('hides the whole expiry group, keeps Spot and opacity identity, and blocks the last deselect', async () => {
    await load()
    const before = plot()
    const colorC = before.data.find((trace: { name: string }) => trace.name === '2026-11-27 Call').line.color
    fireEvent.click(screen.getByRole('checkbox', { name: '2026-10-23' }))
    expect(screen.getByRole<HTMLInputElement>('checkbox', { name: '2026-10-23' }).checked).toBe(false)
    expect(plot().data.map((trace: { name: string }) => trace.name)).toEqual([
      '2026-09-25 Call', '2026-09-25 Put', '2026-11-27 Call', '2026-11-27 Put',
    ])
    expect(plot().data.find((trace: { name: string }) => trace.name === '2026-11-27 Call').line.color).toBe(colorC)
    expect(plot().layout.shapes.map((shape: { x0: number }) => shape.x0)).toEqual([7312.45, 7487.6])
    expect(within(screen.getByRole('region', { name: 'Call 与 Put 图例' })).queryByText(/2026-10-23/)).toBeNull()
    expect(within(screen.getByRole('region', { name: 'Futures 图例' })).queryByText('IM2610.CFE · 7560.3')).toBeNull()
    expect(screen.queryByRole('region', { name: '2026-10-23 到期日' })).toBeNull()
    expect(plot().layout.yaxis.range[1]).toBe(300)
    expect(plot().layout.xaxis.range).toEqual(before.layout.xaxis.range)
    fireEvent.click(screen.getByRole('checkbox', { name: '2026-11-27' }))
    const last = screen.getByRole<HTMLInputElement>('checkbox', { name: '2026-09-25' })
    expect(last.disabled).toBe(true)
    fireEvent.click(last)
    expect(last.checked).toBe(true)
    expect(screen.getAllByRole('checkbox').filter((input: HTMLInputElement) => input.checked)).toHaveLength(1)
    fireEvent.click(screen.getByRole('checkbox', { name: '2026-10-23' }))
    expect(screen.getByRole('region', { name: '2026-10-23 到期日' })).toBeTruthy()
  })

  it('changes three series colors independently without changing selection, opacity or X viewport', async () => {
    await load()
    const before = plot()
    fireEvent.change(screen.getByLabelText('Call 颜色'), { target: { value: '#e11d48' } })
    expect(plot().data[0].line.color).toContain('225, 29, 72')
    expect(plot().data[1].line.color).toBe(before.data[1].line.color)
    expect(plot().layout.shapes[1].line.color).toBe(before.layout.shapes[1].line.color)
    fireEvent.change(screen.getByLabelText('Put 颜色'), { target: { value: '#00ff00' } })
    expect(plot().data[1].line.color).toContain('0, 255, 0')
    expect(plot().data[0].line.color).toContain('225, 29, 72')
    fireEvent.change(screen.getByLabelText('Futures 颜色'), { target: { value: '#ff00ff' } })
    expect(plot().layout.shapes[1].line.color).toContain('255, 0, 255')
    const futuresItem = within(screen.getByRole('region', { name: 'Futures 图例' })).getByText('IM2609.CFE · 7487.6').closest('li')!
    expect((futuresItem.querySelector('.chart-legend-symbol') as HTMLElement).style.color).toBe('rgb(255, 0, 255)')
    expect(plot().data[2].line.color).toContain('0.575')
    expect(plot().data[0].line.dash).not.toBe(plot().data[1].line.dash)
    expect(plot().data[0].marker.symbol).not.toBe(plot().data[1].marker.symbol)
    expect(plot().layout.xaxis.range).toEqual(before.layout.xaxis.range)
    expect(screen.getAllByRole<HTMLInputElement>('checkbox').every((checkbox) => checkbox.checked)).toBe(true)
  })

  it('keeps viewport-outside contracts, null and zero facts, and per-expiry missing counts', async () => {
    await load()
    expect(plot().data[0].x).toEqual([7200, 8000])
    expect(plot().data[0].y).toEqual([200, 2000])
    expect(plot().data[1].y).toEqual([0, null])
    expect(plot().layout.yaxis.range[1]).toBe(600)
    const first = screen.getByRole('region', { name: '2026-09-25 到期日' })
    expect(within(first).getByText(/1 个合约缺少所选价格/)).toBeTruthy()
    fireEvent.click(within(first).getByText('合约明细'))
    expect(within(first).getByText('A-out')).toBeTruthy()
    expect(within(first).getByText('A-null')).toBeTruthy()
    expect(within(first).getByText('—')).toBeTruthy()
    expect(within(first).getByText('0.0')).toBeTruthy()
    const third = screen.getByRole('region', { name: '2026-11-27 到期日' })
    expect(within(third).getByText('无同到期 IM 合约')).toBeTruthy()
  })

  it('updates the combined Y-domain with the shared strike viewport', async () => {
    await load()
    const xBefore = plot().layout.xaxis.range
    for (let i = 0; i < 4; i += 1) {
      fireEvent.click(screen.getByRole('button', { name: '扩大行权价视窗' }))
    }
    expect(plot().layout.xaxis.range).not.toEqual(xBefore)
    expect(plot().layout.yaxis.range[1]).toBe(2400)
    expect(screen.getByText('行权价视窗：±700 点')).toBeTruthy()
  })

  it('keeps references, facts and details if every selected price is null', async () => {
    const allNull = { ...chain, expiries: [{ ...chain.expiries[0], calls: [{ instrument_id: 'C-null', strike: 7000, price: null }], puts: [] }] }
    await load(allNull)
    expect(screen.getByText('选中的到期日没有可绘制的价格。')).toBeTruthy()
    expect(plot().data).toHaveLength(0)
    expect(plot().layout.shapes).toHaveLength(2)
    expect(plot().layout.yaxis.range).toEqual([-2, 100])
    const details = screen.getByRole('region', { name: '2026-09-25 到期日' })
    expect(within(details).getByText('该到期日没有可绘制的价格。')).toBeTruthy()
    fireEvent.click(within(details).getByText('合约明细'))
    expect(within(details).getByText('C-null')).toBeTruthy()
  })

  it('omits the Futures legend when the selected expiry has no matching contract', async () => {
    await load({ ...chain, expiries: [chain.expiries[2]] })
    expect(screen.queryByRole('region', { name: 'Futures 图例' })).toBeNull()
    expect(screen.getByRole('region', { name: 'Call 与 Put 图例' })).toBeTruthy()
    expect(plot().layout.shapes).toHaveLength(1)
  })

  it('shows an explicit state for a valid response with no expiries', async () => {
    await load({ ...chain, expiries: [] })
    expect(screen.getByText('该期权链没有到期日。')).toBeTruthy()
    expect(screen.queryByTestId('plot')).toBeNull()
    expect(screen.queryByRole('checkbox')).toBeNull()
  })

  it('resets expiry selection on a new successful chain while keeping series colors and strike width', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response(chain)).mockResolvedValueOnce(response({ ...chain, target_trade_date: '2026-09-18' }))
    vi.stubGlobal('fetch', fetch)
    render(<OptionChainPage />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
    await screen.findByRole('region', { name: '期权链结果' })
    fireEvent.click(screen.getByRole('checkbox', { name: '2026-10-23' }))
    fireEvent.change(screen.getByLabelText('Call 颜色'), { target: { value: '#e11d48' } })
    fireEvent.click(screen.getByRole('button', { name: '扩大行权价视窗' }))
    fireEvent.change(dateInput(), { target: { value: '2026-09-18' } })
    await screen.findByText('2026-09-18 · MO')
    expect(screen.getAllByRole<HTMLInputElement>('checkbox').every((checkbox) => checkbox.checked)).toBe(true)
    expect((screen.getByLabelText('Call 颜色') as HTMLInputElement).value).toBe('#e11d48')
    expect(screen.getByText('行权价视窗：±400 点')).toBeTruthy()
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('maps a backend error and removes the previous result', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response(chain)).mockResolvedValueOnce(response({ error: { kind: 'date_not_available', detail: 'backend detail' } }, 404))
    vi.stubGlobal('fetch', fetch)
    render(<OptionChainPage />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
    await screen.findByRole('region', { name: '期权链结果' })
    fireEvent.change(dateInput(), { target: { value: '2026-09-18' } })
    expect(screen.queryByRole('region', { name: '期权链结果' })).toBeNull()
    expect(within(await screen.findByRole('alert')).getByText('该日期无可用数据')).toBeTruthy()
  })

  it.each([
    ['invalid_request', '请求日期或参数无效'],
    ['unsupported_query', '当前不支持此查询'],
    ['date_not_available', '该日期无可用数据'],
    ['option_chain_unavailable', '当前无法生成完整期权链'],
    ['service_not_wired', '数据服务尚未接线'],
  ])('maps %s without interpreting backend detail', async (kind, title) => {
    const status = kind === 'date_not_available' ? 404 : kind === 'invalid_request' || kind === 'unsupported_query' ? 400 : 503
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response({ error: { kind, detail: 'backend detail' } }, status)))
    render(<OptionChainPage />)
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
    render(<OptionChainPage />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
    fireEvent.change(dateInput(), { target: { value: '2026-09-18' } })
    expect(pending[0].signal.aborted).toBe(true)
    pending[1].finish(response({ ...chain, target_trade_date: '2026-09-18' }))
    await screen.findByText('2026-09-18 · MO')
    pending[0].finish(response(chain))
    await Promise.resolve()
    expect(screen.getByRole('region', { name: '期权链结果' }).textContent).not.toContain('2026-09-17')
    expect(screen.getAllByRole<HTMLInputElement>('checkbox').every((checkbox) => checkbox.checked)).toBe(true)
  })

  it('shows a transport failure without a stale result', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response(chain)).mockRejectedValueOnce(new TypeError('offline'))
    vi.stubGlobal('fetch', fetch)
    render(<OptionChainPage />)
    fireEvent.change(dateInput(), { target: { value: '2026-09-17' } })
    await screen.findByRole('region', { name: '期权链结果' })
    fireEvent.change(dateInput(), { target: { value: '2026-09-18' } })
    expect(screen.queryByRole('region', { name: '期权链结果' })).toBeNull()
    const alert = await screen.findByRole('alert')
    expect(within(alert).getByText('无法连接数据服务')).toBeTruthy()
  })
})
