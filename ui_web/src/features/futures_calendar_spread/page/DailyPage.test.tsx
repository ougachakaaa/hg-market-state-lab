import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import DailyPage from './DailyPage'
import { DailyPresentation } from '../components/DailyPresentation'
import { validateResult } from '../api/validateResult'
import { commitDate } from '../../../test/datePicker'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import fixture from '../testing/daily_spot.json'
import closed from '../testing/closed.json'
import empty from '../testing/empty.json'
import excluded from '../testing/excluded.json'
let dispose: (() => void) | undefined
afterEach(() => { cleanup(); dispose?.(); vi.unstubAllGlobals() })
it('queries explicitly and keeps ten ordered comparisons and complete exports', async () => {
  dispose = installRequestBoundary(createRequestBoundary(vi.fn()))
  let finish!: (r: Response) => void
  const fetch = vi.fn().mockImplementation(() => new Promise(resolve => { finish = resolve })); vi.stubGlobal('fetch', fetch)
  const writeText = vi.fn().mockResolvedValue(undefined)
  vi.stubGlobal('navigator', { clipboard: { writeText } })
  render(<DailyPage />)
  expect(screen.getByRole('heading', { name: '股指期货跨期价差' })).toBeTruthy()
  fireEvent.mouseDown(screen.getByRole('combobox', { name: '品种' }))
  for (const code of ['IF', 'IH', 'IC', 'IM']) expect(screen.getByText(new RegExp(`^${code} ·`), { selector: '.ant-select-item-option-content' })).toBeTruthy()
  fireEvent.click(screen.getByText('IM · 中证1000', { selector: '.ant-select-item-option-content' }))
  commitDate(screen.getByLabelText('查询日期'), fixture.request.trade_date)
  expect(fetch).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: '查询' }))
  await screen.findByText('正在准备所需数据并计算结果，请稍候。')
  await act(async () => finish(new Response(JSON.stringify(fixture))))
  await screen.findByText('已查询数据')
  expect(fetch).toHaveBeenCalledOnce()
  expect(fetch.mock.calls[0][0]).toBe('/api/data/futures-calendar-spread/query')
  expect(fetch.mock.calls[0][1].method).toBe('POST')
  expect(Array.from(document.querySelectorAll('.ant-table-tbody tr.ant-table-row')).map(row => row.querySelector('td')?.textContent)).toEqual(['M0/M1','M0/Q1','M0/Q2','M1/Q1','M1/Q2','Q1/Q2','M0/现货','M1/现货','Q1/现货','Q2/现货'])
  expect(screen.getAllByText('IM2410.CFX').length).toBeGreaterThan(0)
  expect(screen.getAllByRole('columnheader', { name: '价差（点）' })).toHaveLength(2)
  commitDate(screen.getByLabelText('查询日期'), '2024-10-21')
  expect(screen.getByText(/参数已修改/)).toBeTruthy()
  expect(screen.getAllByText('2024-10-18').length).toBeGreaterThan(0)
  expect(fetch).toHaveBeenCalledOnce()
  fireEvent.click(screen.getByRole('button', { name: '复制原始 JSON' }))
  await screen.findByText('复制成功')
  expect(JSON.parse(writeText.mock.calls[0][0])).toEqual(fixture)
  fireEvent.click(screen.getByRole('button', { name: '查询' }))
  await screen.findByText('正在准备所需数据并计算结果，请稍候。')
  expect(screen.queryByRole('button', { name: '导出 CSV' })).toBeNull()
  expect(screen.queryByText('复制成功')).toBeNull()
  await act(async () => finish(new Response('{}')))
  await screen.findByText(/服务返回的数据未通过完整性验证/)
  expect(screen.queryByRole('button', { name: '复制原始 JSON' })).toBeNull()
  expect(fetch).toHaveBeenCalledTimes(2)
})
it.each([[closed, '休市日'], [empty, '部分比较指标不适用或不可用'], [excluded, '部分比较指标不适用或不可用']] as const)('presents unavailable outcomes independently', (r, label) => {
  render(<DailyPresentation result={validateResult(r)} />)
  expect(screen.getByText(new RegExp(label))).toBeTruthy()
})
