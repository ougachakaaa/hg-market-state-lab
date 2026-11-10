import { captureCsvDownloads } from '../../../test/csvDownload'
import { premiumPlaneCsv } from '../model/csvExport'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import type { PremiumPlane } from '../api/moOptionPremium'
import PremiumPlanePage from './PremiumPlanePage'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'

let releaseBoundary: () => void
beforeEach(() => { releaseBoundary = installRequestBoundary(createRequestBoundary(() => {})) })
afterEach(() => releaseBoundary())

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

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
  Reflect.deleteProperty(navigator, 'clipboard')
})

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

function clipboard(writeText = vi.fn().mockResolvedValue(undefined)) {
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
  return writeText
}
function copyActions() { return within(screen.getByRole('group', { name: 'MO Premium Plane copy actions' })) }
async function copied(button: string) {
  fireEvent.click(copyActions().getByRole('button', { name: button }))
  await waitFor(() => expect(copyActions().getByRole('status').textContent).toBe('Copied'))
}

describe('complete current-result copy', () => {
  it.each(['missing', 'reject', 'resolve'])('reports Clipboard %s without internal errors', async (mode) => {
    const write = clipboard(mode === 'reject' ? vi.fn().mockRejectedValue(new Error('private permission details')) : vi.fn().mockResolvedValue(undefined))
    if (mode === 'missing') Reflect.deleteProperty(navigator, 'clipboard')
    await load()
    fireEvent.click(copyActions().getByRole('button', { name: 'Copy JSON' }))
    await waitFor(() => expect(copyActions().getByRole('status').textContent).toBe(mode === 'resolve' ? 'Copied' : 'Copy failed'))
    expect(screen.queryByText(/private permission details/)).toBeNull()
    if (mode !== 'missing') expect(write).toHaveBeenCalledWith(JSON.stringify(plane, null, 2))
  })
  it.each([[false, false], [false, true], [true, false], [true, true]])('ignores old copy feedback after a new query (reject=%s, whileLoading=%s)', async (rejects, whileLoading) => {
    let finish!: () => void
    let fail!: (error: Error) => void
    const write = clipboard(vi.fn().mockImplementationOnce(() => new Promise<void>((resolve, reject) => { finish = resolve; fail = reject })).mockResolvedValue(undefined))
    await load()
    let finishQuery!: (value: Response) => void
    vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolve) => { finishQuery = resolve }))
    fireEvent.click(copyActions().getByRole('button', { name: 'Copy JSON' }))
    expect(copyActions().queryByRole('status')).toBeNull()
    expect(copyActions().getAllByRole<HTMLButtonElement>('button').every((b) => b.disabled)).toBe(true)
    fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-22' } })
    expect(screen.queryByRole('group', { name: 'MO Premium Plane copy actions' })).toBeNull()
    if (!whileLoading) await act(async () => { finishQuery(response(plane)) })
    await act(async () => { if (rejects) fail(new Error('denied')); else finish() })
    if (whileLoading) await act(async () => { finishQuery(response(plane)) })
    await screen.findByRole('region', { name: 'Premium plane results' })
    expect(copyActions().queryByRole('status')).toBeNull()
    await copied('Copy for GPT')
    expect(write).toHaveBeenCalledTimes(2)
    fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '' } })
    expect(screen.queryByRole('button', { name: 'Copy JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
  })
  it.each(['invalid', 'network'])('has no copy source in idle/loading/%s states', async (mode) => {
    let finish!: (value: Response) => void
    let fail!: (error: Error) => void
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() => new Promise<Response>((resolve, reject) => { finish = resolve; fail = reject })))
    render(<PremiumPlanePage />)
    expect(screen.queryByRole('button', { name: 'Copy JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
    fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-21' } })
    expect(screen.queryByRole('button', { name: 'Copy JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
    await act(async () => { if (mode === 'network') fail(new Error('offline')); else finish(response({ invalid: true })) })
    await screen.findByRole('alert')
    expect(screen.queryByRole('button', { name: 'Copy JSON' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Copy for GPT' })).toBeNull()
  })
  it('copies only the newer response even if an older request completes late', async () => {
    const write = clipboard()
    const download = captureCsvDownloads()
    const pending: Array<(value: Response) => void> = []
    const fetch = vi.fn().mockImplementation(() => new Promise<Response>((resolve) => pending.push(resolve)))
    vi.stubGlobal('fetch', fetch)
    render(<PremiumPlanePage />)
    fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-21' } })
    fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-22' } })
    const current: PremiumPlane = { ...plane, observation: { kind: 'trade_date', value: '2026-09-22' } }
    await act(async () => { pending[1](response(current)) })
    await screen.findByRole('region', { name: 'Premium plane results' })
    await act(async () => { pending[0](response(plane)) })
    await copied('Copy JSON')
    expect(write).toHaveBeenLastCalledWith(JSON.stringify(current, null, 2))
    fireEvent.click(copyActions().getByRole('button', { name: 'Export CSV' }))
    expect(await download.text()).toBe(premiumPlaneCsv(current).csv)
    expect(download.filenames).toEqual([premiumPlaneCsv(current).filename])
    expect(fetch).toHaveBeenCalledTimes(2)
  })
})

it('copies complete sparse response, response identity and Inspector JSON across every presentation axis', async () => {
  const write = clipboard()
  const { fetch, results } = await load()
  const raw = JSON.stringify(plane, null, 2)
  await copied('Copy JSON')
  expect(write).toHaveBeenLastCalledWith(raw)
  for (const name of ['Put', 'Same-expiry futures', 'Time value', 'Unannualized', 'Yield']) {
    fireEvent.click(within(results).getByRole('radio', { name }))
    await copied('Copy JSON')
    expect(write).toHaveBeenLastCalledWith(raw)
  }
  fireEvent.click(within(results).getByRole('checkbox', { name: '2026-10-23' }))
  await copied('Copy JSON')
  expect(write).toHaveBeenLastCalledWith(raw)
  await copied('Copy for GPT')
  const markdown = write.mock.calls.at(-1)![0] as string
  expect(markdown.startsWith('# MO Premium Plane\n')).toBe(true)
  for (const identity of ['observation.kind: trade_date', 'observation.value: 2026-09-21', 'option_product: MO', 'price_type: close', 'underlying.instrument_id: 000852.SH']) expect(markdown).toContain(identity)
  expect(markdown).toContain('sparse Points')
  expect(markdown).toContain('absent Point')
  expect(markdown).toContain('null metric')
  expect(markdown).toContain('numeric zero')
  expect(markdown).toContain('futures: null')
  expect(markdown.split('```json\n')[1].split('\n```')[0]).toBe(raw)
  fireEvent.click(within(results).getByRole('button', { name: 'View raw response' }))
  expect(results.querySelector('pre')?.textContent).toBe(raw)
  const inspectorCopy = within(results).getAllByRole('button', { name: 'Copy JSON' }).find((b) => !screen.getByRole('group', { name: 'MO Premium Plane copy actions' }).contains(b))!
  fireEvent.click(inspectorCopy)
  await waitFor(() => expect(write).toHaveBeenLastCalledWith(raw))
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('uses the validated response identity and removes copy actions on a price-type query', async () => {
  const write = clipboard()
  const current = { ...plane, observation: { kind: 'trade_date', value: '2026-09-23' }, price_type: 'high' }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(current)))
  render(<PremiumPlanePage />)
  fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-21' } })
  await screen.findByRole('region', { name: 'Premium plane results' })
  await copied('Copy for GPT')
  expect(write.mock.calls[0][0]).toContain('observation.value: 2026-09-23')
  expect(write.mock.calls[0][0]).toContain('price_type: high')
  expect(write.mock.calls[0][0]).toContain(JSON.stringify(current, null, 2))
  fireEvent.mouseDown(screen.getByRole('combobox', { name: '价格口径' }))
  fireEvent.click(await screen.findByText('open', { selector: '.ant-select-item-option-content' }))
  expect(screen.queryByRole('group', { name: 'MO Premium Plane copy actions' })).toBeNull()
  await screen.findByRole('region', { name: 'Premium plane results' })
  expect(copyActions().queryByRole('status')).toBeNull()
})

it('downloads all real Points and all metrics independently of every presentation selector', async () => {
  const download = captureCsvDownloads()
  const { fetch, results } = await load()
  expect(copyActions().getAllByRole('button').map((b) => b.textContent)).toEqual(['Copy JSON', 'Copy for GPT', 'Export CSV'])
  const controls = [
    () => {},
    ...['Put', 'Same-expiry futures', 'Time value', 'Unannualized', 'Yield'].map((name) =>
      () => fireEvent.click(within(results).getByRole('radio', { name }))),
    () => fireEvent.click(within(results).getByRole('checkbox', { name: '2026-10-23' })),
  ]
  for (const change of controls) {
    change()
    fireEvent.click(copyActions().getByRole('button', { name: 'Export CSV' }))
    const csv = await download.text()
    expect(csv).toBe(premiumPlaneCsv(plane).csv)
    expect(csv.split('\r\n').length - 2).toBe(plane.points.length)
    expect(csv).toContain('2026-10-23,33,false,null,null,B,call,7300,1,')
    expect(csv).toContain(',-3,-0.003,-30,-0.03,')
    expect(csv).not.toContain('%')
    expect(copyActions().getByRole('status').textContent).toBe('Download started')
  }
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('exports a nonempty plane using response identity', async () => {
  const download = captureCsvDownloads()
  const current = { ...plane, price_type: 'high' as const }
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(current)))
  render(<PremiumPlanePage />)
  fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-19' } })
  await screen.findByRole('region', { name: 'Premium plane results' })
  fireEvent.click(copyActions().getByRole('button', { name: 'Export CSV' }))
  expect(await download.text()).toBe(premiumPlaneCsv(current).csv)
  expect((await download.text()).split('\r\n')).toHaveLength(current.points.length + 2)
  expect(download.filenames).toEqual(['mo-premium-plane_2026-09-21_high.csv'])
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('reports download failure with cleanup and safe feedback, then permits retry', async () => {
  const download = captureCsvDownloads()
  vi.mocked(HTMLAnchorElement.prototype.click).mockImplementationOnce(() => { throw new Error('private detail') })
  await load()
  fireEvent.click(copyActions().getByRole('button', { name: 'Export CSV' }))
  expect(copyActions().getByRole('status').textContent).toBe('Export failed')
  expect(download.revoke).toHaveBeenCalledWith('blob:csv-1')
  expect(document.querySelector('a[download]')).toBeNull()
  expect(screen.queryByText(/private detail/)).toBeNull()
  fireEvent.click(copyActions().getByRole('button', { name: 'Export CSV' }))
  expect(await download.text()).toBe(premiumPlaneCsv(plane).csv)
  expect(copyActions().getByRole('status').textContent).toBe('Download started')
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('removes CSV actions on a price-type query and leaves none after HTTP failure', async () => {
  await load()
  let finish!: (value: Response) => void
  vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolve) => { finish = resolve }))
  fireEvent.mouseDown(screen.getByRole('combobox', { name: '价格口径' }))
  fireEvent.click(await screen.findByText('open', { selector: '.ant-select-item-option-content' }))
  expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
  await act(async () => finish({ ok: false, status: 404, json: async () => ({ error: { kind: 'date_not_available', detail: 'Unavailable', param: 'as_of' } }) } as Response))
  await screen.findByRole('alert')
  expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
})

it('offers no copy or export actions for premium_plane_unavailable', async () => {
  await load()
  vi.mocked(fetch).mockResolvedValueOnce({ ok: false, status: 503, json: async () => ({ error: {
    kind: 'premium_plane_unavailable', detail: 'No real analytical Points', param: null,
  } }) } as Response)
  fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-22' } })
  await screen.findByRole('alert')
  expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Copy JSON' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Copy for GPT' })).toBeNull()
})

it('rejects HTTP 200 with no real Points instead of offering copy or export', async () => {
  await load()
  vi.mocked(fetch).mockResolvedValueOnce(response({ ...plane, points: [] }))
  fireEvent.change(screen.getByLabelText('Observation 日期'), { target: { value: '2026-09-22' } })
  await screen.findByRole('alert')
  expect(screen.queryByRole('button', { name: 'Export CSV' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Copy JSON' })).toBeNull()
  expect(screen.queryByRole('button', { name: 'Copy for GPT' })).toBeNull()
})
