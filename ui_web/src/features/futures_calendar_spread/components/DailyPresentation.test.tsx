import spot from '../testing/daily_spot.json'
import { cleanup, fireEvent, render, screen, act, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { DailyPresentation } from './DailyPresentation'
import { validateResult } from '../api/validateResult'
import daily from '../testing/daily.json'
import { referenceStates, withReference } from '../testing/reference'
import { indexStatusLabels } from '../model/format'
import { contextJson, exportFilename, resultCsv } from '../model/export'
import { downloadText } from '../../../shared/download/download'
vi.mock('../../../shared/download/download', async original => ({ ...await original(), downloadText: vi.fn() }))
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks() })
function clipboard(writeText = vi.fn().mockResolvedValue(undefined)) {
  vi.stubGlobal('navigator', { clipboard: { writeText } }); return writeText
}
it('translates the Daily independent snapshot disclosure only for display', async () => {
  const original = 'Daily SSE Calendar and Index exports are independent snapshots; the same-day index Close is reference-only and never enters futures calculations. Reference preparation follows the selected read-only or explicit execution permission.'
  const unknown = 'Unrecognized captured statement.'
  const r = withReference()
  r.source_context.limitations.push(original, unknown)
  const before = JSON.stringify(r)
  const csv = resultCsv(r)
  const context = contextJson(r)
  const writeText = clipboard()
  render(<DailyPresentation result={validateResult(r)} />)
  fireEvent.click(screen.getByText('关于本数据'))
  expect(screen.getByText('每日上交所交易日历与指数导出是独立快照；同日指数收盘价仅供参考，不参与期货计算。参考数据准备遵循所选的只读查询或显式执行权限。')).toBeTruthy()
  expect(screen.getByText(unknown)).toBeTruthy()
  expect(screen.queryByText(original)).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: '复制原始 JSON' }))
  await screen.findByText('复制成功')
  expect(JSON.parse(writeText.mock.calls[0][0])).toEqual(r)
  expect(JSON.parse(context).data.source_context.limitations).toContain(original)
  expect(contextJson(r)).toBe(context)
  expect(resultCsv(r)).toBe(csv)
  expect(JSON.stringify(r)).toBe(before)
})
it.each(referenceStates)('shows reference %s/%s/%s alongside six intact pairs', (...state) => {
  render(<DailyPresentation result={validateResult(withReference(daily, state))} />)
  expect(screen.getByText(state[1] ? indexStatusLabels[state[1]] : indexStatusLabels.available)).toBeTruthy()
  expect(screen.getByText('000852.SH')).toBeTruthy()
  expect(document.querySelectorAll('.ant-table-row')).toHaveLength(6)
  expect(screen.getAllByText('0.00').length).toBeGreaterThan(0)
})
it('shows historical omission, all Chinese columns and three stage labels', () => {
  const r = validateResult(structuredClone(daily)); r.day.observations[3].expiry_stage = '8_21'
  render(<DailyPresentation result={r} />)
  expect(screen.getByText('历史数据包未提供指数参考信息')).toBeTruthy()
  for (const name of ['比较组合', '近端合约', '远端合约', '近端收盘价', '远端收盘价', '价差（点）', '年化点差（点 / 365 自然日）', '年化价差比例（%）', '期限差（自然日）', '近端剩余到期天数', '到期阶段']) expect(screen.getByRole('columnheader', { name })).toBeTruthy()
  for (const text of ['0–7 天', '8–21 天', '22 天及以上']) expect(screen.getAllByText(text).length).toBeGreaterThan(0)
  expect(document.querySelector('th.ant-table-cell-fix-start')).toBeTruthy()
  expect(document.querySelector('.ant-table-content')?.getAttribute('style')).toContain('overflow-x: auto')
})
it('copies complete Raw, copies/exports identical Context, downloads CSV locally in action order', async () => {
  const writeText = clipboard()
  const fetch = vi.fn(); vi.stubGlobal('fetch', fetch)
  const r = withReference()
  render(<DailyPresentation result={r} />)
  expect(screen.getAllByRole('button').slice(0, 4).map(b => b.textContent)).toEqual(['复制原始 JSON', '复制上下文 JSON', '导出 CSV', '导出上下文 JSON'])
  fireEvent.click(screen.getByRole('button', { name: '复制原始 JSON' }))
  await screen.findByText('复制成功')
  expect(JSON.parse(writeText.mock.calls[0][0])).toEqual(r)
  fireEvent.click(screen.getByRole('button', { name: '复制上下文 JSON' }))
  await screen.findByText('复制成功')
  fireEvent.click(screen.getByRole('button', { name: '导出上下文 JSON' }))
  expect(downloadText).toHaveBeenLastCalledWith(writeText.mock.calls[1][0], exportFilename(r, true), 'application/json;charset=utf-8')
  expect(writeText.mock.calls[1][0]).toBe(contextJson(r))
  expect(screen.getByText('已开始下载')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '导出 CSV' }))
  expect(downloadText).toHaveBeenLastCalledWith(resultCsv(r), exportFilename(r), 'text/csv;charset=utf-8')
  expect(fetch).not.toHaveBeenCalled()
})
it('disables all four actions during copy and isolates old feedback when result changes', async () => {
  let finish!: () => void
  clipboard(vi.fn().mockImplementation(() => new Promise<void>(resolve => { finish = resolve })))
  const { rerender } = render(<DailyPresentation result={withReference()} />)
  fireEvent.click(screen.getByRole('button', { name: '复制原始 JSON' }))
  for (const b of screen.getAllByRole('button').slice(0, 4)) expect((b as HTMLButtonElement).disabled).toBe(true)
  rerender(<DailyPresentation result={validateResult(daily)} />)
  await act(async () => finish())
  expect(screen.queryByText('复制成功')).toBeNull()
  expect((screen.getByRole('button', { name: '复制原始 JSON' }) as HTMLButtonElement).disabled).toBe(false)
})
it('reports clipboard and download failures without exposing diagnostics', async () => {
  clipboard(vi.fn().mockRejectedValue(new Error('secret')))
  render(<DailyPresentation result={withReference()} />)
  fireEvent.click(screen.getByRole('button', { name: '复制原始 JSON' }))
  await screen.findByText('复制失败')
  vi.mocked(downloadText).mockImplementationOnce(() => { throw new Error('secret') })
  fireEvent.click(screen.getByRole('button', { name: '导出上下文 JSON' }))
  expect(screen.getByText('导出失败')).toBeTruthy()
  expect(screen.queryByText(/secret/)).toBeNull()
})
it('treats missing clipboard as failure', async () => {
  vi.stubGlobal('navigator', {})
  render(<DailyPresentation result={withReference()} />)
  fireEvent.click(screen.getByRole('button', { name: '复制上下文 JSON' }))
  await waitFor(() => expect(screen.getByText('复制失败')).toBeTruthy())
})

it('renders six calendar and four spot rows with contiguous labels, prices and metrics', () => {
  render(<DailyPresentation result={validateResult(spot)} />)
  expect(document.querySelectorAll('.ant-table-row')).toHaveLength(10)
  const tables = document.querySelectorAll('.ant-table')
  const headers = (table: Element) => Array.from(table.querySelectorAll('th')).map(th => th.textContent)
  expect(headers(tables[0])).toEqual(['比较组合', '近端合约', '远端合约', '近端收盘价', '远端收盘价', '价差（点）', '年化点差（点 / 365 自然日）', '年化价差比例（%）', '期限差（自然日）', '近端剩余到期天数', '到期阶段'])
  expect(headers(tables[1])).toEqual(['比较组合', '期货合约', '现货指数', '期货收盘价', '现货收盘价', '价差（点）', '年化点差（点 / 365 自然日）', '年化价差比例（%）', '期货剩余期限（自然日）', '到期阶段'])
  expect(Array.from(tables[1].querySelectorAll('.ant-table-row')).map(row => row.querySelector('td')?.textContent)).toEqual(['M0/现货', 'M1/现货', 'Q1/现货', 'Q2/现货'])
  for (const name of ['近端最后交易日', '远端最后交易日', '结果状态', '原因']) expect(screen.queryByRole('columnheader', { name })).toBeNull()
  const expiry = tables[1].querySelector('.ant-table-row')!
  expect(Array.from(expiry.querySelectorAll('td')).slice(6, 8).map(td => td.textContent)).toEqual(['—', '—'])
  expect(screen.queryByText('M0/现货：合约到期日，年化指标不适用')).toBeNull()
  fireEvent.click(screen.getByText('数据说明'))
  expect(screen.getByText('M0/现货：合约到期日，年化指标不适用')).toBeTruthy()
})
