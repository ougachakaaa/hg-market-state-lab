import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import DailyPage from './DailyPage'
import { DailyPresentation } from '../components/DailyPresentation'
import { validateResult } from '../api/validateResult'
import { commitDate } from '../../../test/datePicker'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import fixture from '../testing/daily.json'
import closed from '../testing/closed.json'
import empty from '../testing/empty.json'
import excluded from '../testing/excluded.json'
let dispose: (() => void) | undefined
afterEach(() => { cleanup(); dispose?.(); vi.unstubAllGlobals() })
it('queries explicitly and keeps six ordered pairs / real contracts / raw zero', async () => {
  dispose = installRequestBoundary(createRequestBoundary(vi.fn()))
  let finish!: (r: Response) => void
  const fetch = vi.fn().mockImplementation(() => new Promise(resolve => { finish = resolve })); vi.stubGlobal('fetch', fetch)
  render(<DailyPage />)
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Product' }))
  fireEvent.click(screen.getByText('IM', { selector: '.ant-select-item-option-content' }))
  commitDate(screen.getByLabelText('Trade Date'), fixture.request.trade_date)
  expect(fetch).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: '查询' }))
  await screen.findByText('正在准备所需数据并计算结果，请稍候。')
  await act(async () => finish(new Response(JSON.stringify(fixture))))
  await screen.findByText('已查询数据')
  expect(fetch).toHaveBeenCalledOnce()
  expect(fetch.mock.calls[0][0]).toBe('/api/data/futures-calendar-spread/query')
  expect(fetch.mock.calls[0][1].method).toBe('POST')
  expect(Array.from(document.querySelectorAll('.ant-table-tbody tr.ant-table-row')).map(row => row.querySelector('td')?.textContent)).toEqual(['M0/M1','M0/Q1','M0/Q2','M1/Q1','M1/Q2','Q1/Q2'])
  expect(screen.getAllByText('IM2410.CFX').length).toBeGreaterThan(0)
  expect(screen.getByRole('columnheader', { name: 'Signed Spread（点）' })).toBeTruthy()
  commitDate(screen.getByLabelText('Trade Date'), '2024-10-21')
  expect(screen.getByText(/参数已修改/)).toBeTruthy()
  expect(screen.getAllByText('2024-10-18').length).toBeGreaterThan(0)
  expect(fetch).toHaveBeenCalledOnce()
})
it.each([[closed, '休市日'], [empty, '已证明没有活跃合约'], [excluded, '非正价格观察已排除']] as const)('presents unavailable outcomes independently', (r, label) => {
  render(<DailyPresentation result={validateResult(r)} />)
  expect(screen.getByText(new RegExp(label))).toBeTruthy()
})
