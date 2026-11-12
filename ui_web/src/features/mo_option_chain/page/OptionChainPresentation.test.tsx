import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { OptionChainPresentation, useOptionChainPresentation, validateOptionChain } from '../presentation'
import { chain as fixture } from '../testing/chainFixture'
import { captureCsvDownloads } from '../../../test/csvDownload'
import { optionChainCsv } from '../model/csvExport'
import { optionChainContextJson } from '../model/copyText'

vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); Reflect.deleteProperty(navigator, 'clipboard') })

function Static({ chain = validateOptionChain(fixture) }) {
  const state = useOptionChainPresentation(chain)
  return <OptionChainPresentation state={{ ...state, page: { status: 'ready', chain } }}
    query={{ mode: 'static', selectedDate: chain.target_trade_date, sourceDisclosure: '静态测试数据，不是正式 Example' }} />
}

it('validates full results with the formal schema and rejects malformed data', () => {
  expect(validateOptionChain(fixture)).toBe(fixture)
  expect(() => validateOptionChain({ ...fixture, underlying: null })).toThrow()
  expect(() => validateOptionChain({ ...fixture, expiries: [{ ...fixture.expiries[0], calls: [{ instrument_id: 'bad', strike: 1 }] }] })).toThrow()
})

it('renders without Auth/controller, fixes query, preserves local controls and complete copy/export', async () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  const copy = vi.fn().mockResolvedValue(undefined)
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: copy } })
  const downloads = captureCsvDownloads()
  render(<Static />)
  expect((screen.getByLabelText('观察日期') as HTMLInputElement).disabled).toBe(true)
  expect(screen.getByRole('note').textContent).toContain('静态测试数据')
  expect(screen.getByText(/固定观察日期 · MO · close/)).toBeTruthy()
  expect(screen.getByTestId('plot')).toBeTruthy()
  fireEvent.submit(screen.getByRole('form', { name: '期权链查询' }))
  fireEvent.click(screen.getByRole('checkbox', { name: '2026-10-23' }))
  fireEvent.click(screen.getByRole('checkbox', { name: '2026-11-27' }))
  expect((screen.getByRole('checkbox', { name: '2026-09-25' }) as HTMLInputElement).disabled).toBe(true)
  expect(screen.queryByRole('region', { name: '2026-10-23 到期日' })).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: '扩大行权价视窗' }))
  expect(screen.getByText('行权价视窗：±400 点')).toBeTruthy()
  fireEvent.click(screen.getByText('高级设置 · 图表颜色'))
  fireEvent.click(screen.getByRole('button', { name: 'Call 颜色' }))
  const input = document.querySelector<HTMLInputElement>('.ant-color-picker-hex-input input')!
  fireEvent.change(input, { target: { value: 'e11d48' } })
  expect(screen.getByRole('button', { name: 'Call 颜色' }).textContent).toContain('#e11d48')
  for (const [name, expected] of [['Copy Raw JSON', JSON.stringify(fixture, null, 2)], ['Copy Context JSON', optionChainContextJson(fixture)]]) {
    fireEvent.click(screen.getByRole('button', { name }))
    await waitFor(() => expect(copy).toHaveBeenLastCalledWith(expected))
    await act(async () => {})
  }
  fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))
  expect(await downloads.text()).toBe(optionChainCsv(fixture).csv)
  fireEvent.click(screen.getByRole('button', { name: 'Export Context JSON' }))
  expect(await downloads.text()).toBe(optionChainContextJson(fixture))
  expect(fetch).not.toHaveBeenCalled()
})
