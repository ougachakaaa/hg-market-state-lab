import { commitDate } from '../../../test/datePicker'
import { captureCsvDownloads } from '../../../test/csvDownload'
import { optionChainCsv } from '../model/csvExport'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import type { OptionChain } from '../api/moOptionChain'
import type { PlotParams } from 'react-plotly.js'
import OptionChainPage from './OptionChainPage'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'

let releaseBoundary: () => void
beforeEach(() => { releaseBoundary = installRequestBoundary(createRequestBoundary(() => {})) })
afterEach(() => releaseBoundary())

vi.mock('react-plotly.js', () => ({
  default: ({ data, layout, config, useResizeHandler, style }: PlotParams) => (
    <div data-testid="plot" data-plot={JSON.stringify({ data, layout, config, useResizeHandler, style })} />
  ),
}))

const chain: OptionChain = {
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
  return screen.getByLabelText('观察日期') as HTMLInputElement
}

function changeSeriesColor(label: string, color: string) {
  fireEvent.click(screen.getByRole('button', { name: label }))
  const inputs = document.querySelectorAll<HTMLInputElement>('.ant-color-picker-hex-input input')
  const input = inputs.item(inputs.length - 1)
  expect(input).not.toBeNull()
  fireEvent.change(input!, { target: { value: color.replace('#', '') } })
}

async function load(body: unknown = chain) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(body)))
  render(<OptionChainPage />)
  commitDate(dateInput(), '2026-09-17')
  return screen.findByRole('region', { name: '期权链结果' })
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  Reflect.deleteProperty(navigator, 'clipboard')
})

describe('MO option chain combined page', () => {
  it('starts idle and does not request a chain until a date is selected', () => {
    const fetch = vi.fn()
    vi.stubGlobal('fetch', fetch)
    render(<OptionChainPage />)
    expect(screen.getByRole('status').textContent).toContain('请选择观察日期')
    expect(fetch).not.toHaveBeenCalled()
    commitDate(dateInput(), '')
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
    expect(screen.getByRole('button', { name: 'Call 颜色' }).textContent).toContain('#2563eb')
    expect(screen.getByRole('button', { name: 'Put 颜色' }).textContent).toContain('#ea580c')
    expect(screen.getByRole('button', { name: 'Futures 颜色' }).textContent).toContain('#7c3aed')
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
    changeSeriesColor('Call 颜色', '#e11d48')
    expect(plot().data[0].line.color).toContain('225, 29, 72')
    expect(plot().data[1].line.color).toBe(before.data[1].line.color)
    expect(plot().layout.shapes[1].line.color).toBe(before.layout.shapes[1].line.color)
    changeSeriesColor('Put 颜色', '#00ff00')
    expect(plot().data[1].line.color).toContain('0, 255, 0')
    expect(plot().data[0].line.color).toContain('225, 29, 72')
    changeSeriesColor('Futures 颜色', '#ff00ff')
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
    commitDate(dateInput(), '2026-09-17')
    await screen.findByRole('region', { name: '期权链结果' })
    fireEvent.click(screen.getByRole('checkbox', { name: '2026-10-23' }))
    changeSeriesColor('Call 颜色', '#e11d48')
    fireEvent.click(screen.getByRole('button', { name: '扩大行权价视窗' }))
    commitDate(dateInput(), '2026-09-18')
    await screen.findByText('2026-09-18 · MO')
    expect(screen.getAllByRole<HTMLInputElement>('checkbox').every((checkbox) => checkbox.checked)).toBe(true)
    expect(screen.getByRole('button', { name: 'Call 颜色' }).textContent).toContain('#e11d48')
    expect(screen.getByText('行权价视窗：±400 点')).toBeTruthy()
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('maps a backend error and removes the previous result', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(response(chain)).mockResolvedValueOnce(response({ error: { kind: 'date_not_available', detail: 'backend detail' } }, 404))
    vi.stubGlobal('fetch', fetch)
    render(<OptionChainPage />)
    commitDate(dateInput(), '2026-09-17')
    await screen.findByRole('region', { name: '期权链结果' })
    commitDate(dateInput(), '2026-09-18')
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
    commitDate(dateInput(), '2026-09-17')
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
    commitDate(dateInput(), '2026-09-17')
    commitDate(dateInput(), '2026-09-18')
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
    commitDate(dateInput(), '2026-09-17')
    await screen.findByRole('region', { name: '期权链结果' })
    commitDate(dateInput(), '2026-09-18')
    expect(screen.queryByRole('region', { name: '期权链结果' })).toBeNull()
    const alert = await screen.findByRole('alert')
    expect(within(alert).getByText('无法连接数据服务')).toBeTruthy()
  })
})

function clipboard(writeText = vi.fn().mockResolvedValue(undefined)) {
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
  return writeText
}
function copyActions() { return within(screen.getByRole('group', { name: 'MO Option Chain copy actions' })) }
async function copied(button: string) {
  fireEvent.click(copyActions().getByRole('button', { name: button }))
  await waitFor(() => expect(copyActions().getAllByRole('status').some((node) => node.textContent === 'Copied')).toBe(true))
}

describe('complete current-result copy', () => {
  it.each(['missing', 'reject', 'resolve'])('reports Clipboard %s without internal errors', async (mode) => {
    const write = clipboard(mode === 'reject' ? vi.fn().mockRejectedValue(new Error('private permission details')) : vi.fn().mockResolvedValue(undefined))
    if (mode === 'missing') Reflect.deleteProperty(navigator, 'clipboard')
    await load()
    fireEvent.click(copyActions().getByRole('button', { name: 'Copy Raw JSON' }))
    await waitFor(() => expect(copyActions().getByRole('status').textContent).toBe(mode === 'resolve' ? 'Copied' : 'Copy failed'))
    expect(screen.queryByText(/private permission details/)).toBeNull()
    if (mode !== 'missing') expect(write).toHaveBeenCalledWith(JSON.stringify(chain, null, 2))
  })
  it.each([[false, false], [false, true], [true, false], [true, true]])('ignores old copy feedback after a new query (reject=%s, whileLoading=%s)', async (rejects, whileLoading) => {
    let finish!: () => void
    let fail!: (error: Error) => void
    const write = clipboard(vi.fn().mockImplementationOnce(() => new Promise<void>((resolve, reject) => { finish = resolve; fail = reject })).mockResolvedValue(undefined))
    await load()
    let finishQuery!: (value: Response) => void
    vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolve) => { finishQuery = resolve }))
    fireEvent.click(copyActions().getByRole('button', { name: 'Copy Raw JSON' }))
    expect(copyActions().queryByRole('status')).toBeNull()
    expect(copyActions().getAllByRole<HTMLButtonElement>('button').every((b) => b.disabled)).toBe(true)
    commitDate(screen.getByLabelText('观察日期'), '2026-09-22')
    expect(screen.queryByRole('group', { name: 'MO Option Chain copy actions' })).toBeNull()
    if (!whileLoading) await act(async () => { finishQuery(response(chain)) })
    await act(async () => { if (rejects) fail(new Error('denied')); else finish() })
    if (whileLoading) await act(async () => { finishQuery(response(chain)) })
    await screen.findByRole('region', { name: '期权链结果' })
    expect(copyActions().queryByRole('status')).toBeNull()
    await copied('Copy Context JSON')
    expect(write).toHaveBeenCalledTimes(2)
    commitDate(screen.getByLabelText('观察日期'), '')
    expect(screen.queryByRole('button', { name: 'Copy Raw JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export Context JSON' })).toBeNull()
  })
  it.each(['invalid', 'network'])('has no copy source in idle/loading/%s states', async (mode) => {
    let finish!: (value: Response) => void
    let fail!: (error: Error) => void
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => new Promise<Response>((resolve, reject) => { finish = resolve; fail = reject })))
    render(<OptionChainPage />)
    expect(screen.queryByRole('button', { name: 'Copy Raw JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export Context JSON' })).toBeNull()
    commitDate(screen.getByLabelText('观察日期'), '2026-09-17')
    expect(screen.queryByRole('button', { name: 'Copy Raw JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export Context JSON' })).toBeNull()
    await act(async () => { if (mode === 'network') fail(new Error('offline')); else finish(response({ invalid: true })) })
    await screen.findByRole('alert')
    expect(screen.queryByRole('button', { name: 'Copy Raw JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export Context JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Copy Context JSON' })).toBeNull()
  })
  it('copies only the newer response even if an older request completes late', async () => {
    const write = clipboard()
    const download = captureCsvDownloads()
    const pending: Array<(value: Response) => void> = []
    const fetch = vi.fn().mockImplementation(() => new Promise<Response>((resolve) => pending.push(resolve)))
    vi.stubGlobal('fetch', fetch)
    render(<OptionChainPage />)
    commitDate(screen.getByLabelText('观察日期'), '2026-09-17')
    commitDate(screen.getByLabelText('观察日期'), '2026-09-22')
    const current = { ...chain, target_trade_date: '2026-09-22' }
    await act(async () => { pending[1](response(current)) })
    await screen.findByRole('region', { name: '期权链结果' })
    await act(async () => { pending[0](response(chain)) })
    await copied('Copy Raw JSON')
    expect(write).toHaveBeenLastCalledWith(JSON.stringify(current, null, 2))
    fireEvent.click(copyActions().getByRole('button', { name: 'Export CSV' }))
    expect(await download.text()).toBe(optionChainCsv(current).csv)
    expect(download.filenames).toEqual([optionChainCsv(current).filename])
    expect(fetch).toHaveBeenCalledTimes(2)
  })
})

it('copies full chain and response context independently of all display controls', async () => {
  const write = clipboard()
  await load()
  const raw = JSON.stringify(chain, null, 2)
  await copied('Copy Raw JSON')
  expect(write).toHaveBeenLastCalledWith(raw)
  const controls = [
    () => fireEvent.click(screen.getByRole('checkbox', { name: '2026-10-23' })),
    () => fireEvent.click(screen.getByRole('button', { name: '扩大行权价视窗' })),
    () => changeSeriesColor('Call 颜色', '#e11d48'),
    () => changeSeriesColor('Put 颜色', '#00ff00'),
    () => changeSeriesColor('Futures 颜色', '#ff00ff'),
  ]
  for (const change of controls) {
    change()
    await copied('Copy Raw JSON')
    expect(write).toHaveBeenLastCalledWith(raw)
  }
  await copied('Copy Context JSON')
  const context = JSON.parse(write.mock.calls.at(-1)![0] as string)
  expect(context.format_version).toBe('daily-data-context-v1')
  expect(context.metadata.product).toBe('MO Option Chain')
  expect(context.metadata.response_identity).toEqual({ target_trade_date: chain.target_trade_date, option_product: chain.option_product, price_type: chain.price_type, underlying_instrument_id: chain.underlying.instrument_id })
  expect(context.data).toEqual(JSON.parse(raw))
  expect(context.metadata.reading_notes.join(' ')).toContain('null price')
  expect(context.metadata.reading_notes.join(' ')).toContain('numeric zero')
  expect(context.metadata.reading_notes.join(' ')).toContain('futures: null')
  expect(context.metadata.reading_notes.join(' ')).toContain('Call/Put grouping')
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('downloads complete CSV across viewport, hidden expiry and every color control without refetching', async () => {
  const write = clipboard()
  const download = captureCsvDownloads()
  await load()
  expect(copyActions().getAllByRole('button').map((b) => b.textContent)).toEqual(['Copy Raw JSON', 'Copy Context JSON', 'Export CSV', 'Export Context JSON'])
  const controls = [
    () => {},
    () => fireEvent.click(screen.getByRole('checkbox', { name: '2026-10-23' })),
    () => fireEvent.click(screen.getByRole('button', { name: '扩大行权价视窗' })),
    () => changeSeriesColor('Call 颜色', '#e11d48'),
    () => changeSeriesColor('Put 颜色', '#00ff00'),
    () => changeSeriesColor('Futures 颜色', '#ff00ff'),
  ]
  for (const change of controls) {
    change()
    fireEvent.click(copyActions().getByRole('button', { name: 'Export CSV' }))
    const csv = await download.text()
    expect(csv).toBe(optionChainCsv(chain).csv)
    expect(csv.split('\r\n').length - 2).toBe(8)
    expect(csv).toContain(',call,A-out,8000,2000\r\n')
    expect(csv).toContain(',put,A-null,7300,null\r\n')
    expect(csv).toContain(',put,A-zero,7100,0\r\n')
    expect(csv).toContain('2026-11-27,false,null,null,call,C-call')
    expect(copyActions().getAllByRole('status').some((node) => node.textContent === 'Download started')).toBe(true)
    await copied('Copy Context JSON')
    const contextText = write.mock.calls.at(-1)![0] as string
    expect(JSON.parse(contextText).data).toEqual(chain)
    fireEvent.click(copyActions().getByRole('button', { name: 'Export Context JSON' }))
    expect(await download.text()).toBe(contextText)
    expect(download.blobs.at(-1)!.type).toBe('application/json;charset=utf-8')
    expect(download.filenames.at(-1)).toBe(`mo-option-chain_${chain.target_trade_date}_${chain.price_type}_context.json`)
  }
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('uses returned chain identity for CSV and filename, including header-only success', async () => {
  const download = captureCsvDownloads()
  const current = { ...chain, target_trade_date: '2026-09-23', price_type: 'high' as const, expiries: [] }
  await load(current)
  fireEvent.click(copyActions().getByRole('button', { name: 'Export CSV' }))
  expect(await download.text()).toBe(optionChainCsv(current).csv)
  expect((await download.text()).split('\r\n')).toHaveLength(2)
  expect(download.filenames).toEqual(['mo-option-chain_2026-09-23_high.csv'])
  expect(fetch).toHaveBeenCalledTimes(1)
})

it.each(['Export CSV', 'Export Context JSON'])('reports failed export without false success or internal detail and allows retry', async (button) => {
  const download = captureCsvDownloads()
  download.create.mockImplementationOnce(() => { throw new Error('private detail') })
  await load()
  fireEvent.click(copyActions().getByRole('button', { name: button }))
  expect(copyActions().getByRole('status').textContent).toBe('Export failed')
  expect(screen.queryByText(/private detail/)).toBeNull()
  fireEvent.click(copyActions().getByRole('button', { name: button }))
  if (button === 'Export CSV') expect(await download.text()).toBe(optionChainCsv(chain).csv)
  else expect(JSON.parse(await download.text()).data).toEqual(chain)
  expect(copyActions().getAllByRole('status').some((node) => node.textContent === 'Download started')).toBe(true)
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('removes CSV actions immediately on a new query and keeps them absent on HTTP failure', async () => {
  await load()
  let finish!: (value: Response) => void
  vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolve) => { finish = resolve }))
  commitDate(dateInput(), '2026-09-18')
  expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Export Context JSON' })).toBeNull()
  await act(async () => finish(response({ error: { kind: 'date_not_available', detail: 'Unavailable', param: 'target_trade_date' } }, 404)))
  await screen.findByRole('alert')
  expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Export Context JSON' })).toBeNull()
})

it('does not request incomplete or invalid calendar input, and supports keyboard commit', async () => {
  const fetch = vi.fn().mockImplementation((_url: string) => new Promise<Response>(() => {}))
  vi.stubGlobal('fetch', fetch)
  render(<OptionChainPage />)
  for (const value of ['2026-09-', '2026-02-30', 'invalid']) {
    commitDate(dateInput(), value)
    expect(fetch).not.toHaveBeenCalled()
    expect(screen.getByRole('status').textContent).toContain('请选择观察日期')
  }
  commitDate(dateInput(), '2026-09-17')
  expect(fetch).toHaveBeenCalledTimes(1)
  expect(String(fetch.mock.calls[0][0])).toContain('target_trade_date=2026-09-17')
  expect(screen.getByRole('status').textContent).toContain('正在加载 2026-09-17')
  commitDate(dateInput(), '')
  expect(screen.getByRole('status').textContent).toContain('请选择观察日期')
})
