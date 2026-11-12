import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { PremiumPlanePresentation, usePremiumPresentation, validatePremiumPlane } from '../presentation'
import type { PremiumPlaneResult } from '../presentation'
import { matchesResponse } from '../api/validatePremiumPlane'
import { plane } from '../testing/planeFixture'
import { captureCsvDownloads } from '../../../test/csvDownload'
import { premiumPlaneCsv } from '../model/csvExport'
import { premiumPlaneContextJson } from '../model/copyText'

const result = validatePremiumPlane(plane)
function Static({ data = result }: { data?: PremiumPlaneResult }) {
  const state = usePremiumPresentation(data.plane)
  return <PremiumPlanePresentation state={{ ...state, page: { status: 'ready', ...data } }}
    query={{ mode: 'static', selectedDate: data.plane.observation.value, priceType: data.plane.price_type,
      sourceDisclosure: '静态 Synthetic 测试 payload，不是后端响应或正式 Example' }} />
}
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); Reflect.deleteProperty(navigator, 'clipboard') })
function clipboard(write = vi.fn().mockResolvedValue(undefined)) {
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: write } })
  return write
}

it('uses generated schema plus the existing nonempty analytical Points invariant, preserving raw identity', () => {
  expect(result.plane).toBe(plane)
  expect(result.rawPayload).toBe(plane)
  expect(() => validatePremiumPlane({ ...plane, underlying: null })).toThrow()
  const incomplete = structuredClone(plane)
  Reflect.deleteProperty(incomplete.points[0].metrics.underlying_spot.total.annualized, 'yield')
  expect(() => validatePremiumPlane(incomplete)).toThrow()
  const empty = { ...plane, points: [] }
  expect(matchesResponse(200, empty)).toBe(true)
  expect(() => validatePremiumPlane(empty)).toThrow()
})

it('fixes query while preserving defaults, sparse blank/null/zero cells, four-axis controls and full Raw/Export', async () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  const write = clipboard()
  const downloads = captureCsvDownloads()
  render(<Static />)
  expect((screen.getByLabelText('观察日期') as HTMLInputElement).disabled).toBe(true)
  expect((screen.getByRole('combobox', { name: '价格口径' }) as HTMLInputElement).disabled).toBe(true)
  fireEvent.submit(screen.getByRole('form', { name: '权利金平面查询' }))
  for (const name of ['Call', 'Underlying spot', 'Total value', 'Annualized', 'Points']) {
    expect((screen.getByRole('radio', { name }) as HTMLInputElement).checked).toBe(true)
  }
  expect(screen.getByText('0.0')).toBeTruthy()
  expect(screen.getByRole('cell', { name: '2026-09-25 no Point' }).textContent).toBe('')
  fireEvent.click(screen.getByRole('radio', { name: 'Same-expiry futures' }))
  fireEvent.click(screen.getByRole('radio', { name: 'Time value' }))
  fireEvent.click(screen.getByRole('radio', { name: 'Unannualized' }))
  fireEvent.click(screen.getByRole('radio', { name: 'Yield' }))
  expect(screen.getByText('-0.20%')).toBeTruthy()
  expect(screen.getByRole('cell', { name: '2026-10-23 metric unavailable' }).textContent).toBe('—')
  expect(screen.getByRole('cell', { name: '2026-10-23 metric unavailable' }).classList.contains('neutral')).toBe(true)
  fireEvent.click(screen.getByRole('radio', { name: 'Put' }))
  fireEvent.click(screen.getByRole('checkbox', { name: '2026-10-23' }))
  expect((screen.getByRole('checkbox', { name: '2026-09-25' }) as HTMLInputElement).disabled).toBe(true)
  fireEvent.click(screen.getByText('View embedded payload'))
  expect(screen.getByText('Validated embedded Example payload')).toBeTruthy()
  expect(screen.getAllByRole('note')).toHaveLength(2)
  expect(document.querySelector('pre')?.textContent).toBe(JSON.stringify(plane, null, 2))
  for (const [name, text] of [['Copy Raw JSON', JSON.stringify(plane, null, 2)],
    ['Copy Context JSON', premiumPlaneContextJson(plane, plane)], ['Copy JSON', JSON.stringify(plane, null, 2)]]) {
    fireEvent.click(screen.getByRole('button', { name }))
    await waitFor(() => expect(write).toHaveBeenLastCalledWith(text))
    await act(async () => {})
  }
  fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))
  expect(await downloads.text()).toBe(premiumPlaneCsv(plane).csv)
  fireEvent.click(screen.getByRole('button', { name: 'Export Context JSON' }))
  expect(await downloads.text()).toBe(premiumPlaneContextJson(plane, plane))
  expect(fetch).not.toHaveBeenCalled()
})

it.each(['Copy Raw JSON', 'Copy JSON'])('resets replacement results and isolates pending %s feedback for the same observation', async name => {
  let finish!: () => void
  const write = clipboard(vi.fn(() => new Promise<void>(resolve => { finish = resolve })))
  const { rerender } = render(<Static />)
  fireEvent.click(screen.getByRole('radio', { name: 'Put' }))
  fireEvent.click(screen.getByText('View embedded payload'))
  fireEvent.click(screen.getByRole('button', { name }))
  expect(write).toHaveBeenCalledTimes(1)
  expect((screen.getByRole('button', { name }) as HTMLButtonElement).disabled).toBe(true)
  rerender(<Static data={validatePremiumPlane(structuredClone(plane))} />)
  expect((screen.getByRole('radio', { name: 'Call' }) as HTMLInputElement).checked).toBe(true)
  expect(screen.queryByText('Copied')).toBeNull()
  await act(async () => finish())
  expect(screen.queryByText('Copied')).toBeNull()
  expect((screen.getByRole('button', { name: 'Copy Raw JSON' }) as HTMLButtonElement).disabled).toBe(false)
  fireEvent.click(screen.getByText('View embedded payload'))
  expect(within(screen.getByRole('region', { name: 'Premium plane results' })).queryByText('Copied')).toBeNull()
})
