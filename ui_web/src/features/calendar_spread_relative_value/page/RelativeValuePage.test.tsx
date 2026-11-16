import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import RelativeValuePage from './RelativeValuePage'
import { parseEdges } from '../model/queryInput'
import { commitDate } from '../../../test/datePicker'
import { createRequestBoundary, installRequestBoundary } from '../../../shared/http/protectedRequest'
import fixture from '../testing/history1.json'
vi.mock('react-plotly.js', () => ({ default: ({ data, layout }: any) => <div data-testid="plot" data-axis={layout.xaxis.type} data-y={JSON.stringify(data.map((t: any) => t.y))} /> }))
let dispose: (() => void) | undefined
afterEach(() => { cleanup(); dispose?.(); vi.unstubAllGlobals() })
it('requires explicit submission, switches pair and axis locally, and labels edited drafts', async () => {
  dispose = installRequestBoundary(createRequestBoundary(vi.fn()))
  const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify(fixture))); vi.stubGlobal('fetch', fetch)
  render(<RelativeValuePage />)
  expect(fetch).not.toHaveBeenCalled()
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Product' }))
  fireEvent.click(screen.getByText('IM', { selector: '.ant-select-item-option-content' }))
  commitDate(screen.getByLabelText('History Start'), fixture.request.history_start)
  commitDate(screen.getByLabelText('Evaluation Date'), fixture.request.evaluation_date)
  fireEvent.change(screen.getByLabelText('Histogram Edges'), { target: { value: '[-0.1,0,0.1]' } })
  expect(fetch).not.toHaveBeenCalled()
  fireEvent.click(screen.getByRole('button', { name: '开始研究' }))
  await screen.findByText('当前价差相对于可比历史样本处于什么位置？')
  expect(fetch).toHaveBeenCalledOnce()
  expect(JSON.parse(fetch.mock.calls[0][1].body).metric).toBe('annualized_spread_ratio')
  expect(screen.getAllByTestId('plot')[0].getAttribute('data-axis')).toBe('linear')
  const y = screen.getAllByTestId('plot')[0].getAttribute('data-y')
  fireEvent.click(screen.getByText('Calendar Days'))
  expect(screen.getAllByTestId('plot')[0].getAttribute('data-axis')).toBe('date')
  expect(screen.getAllByTestId('plot')[0].getAttribute('data-y')).toBe(y)
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Pair' }))
  fireEvent.click(screen.getByText('Q1/Q2', { selector: '.ant-select-item-option-content' }))
  expect(fetch).toHaveBeenCalledOnce()
  fireEvent.change(screen.getByLabelText('Histogram Edges'), { target: { value: '[-1,0,1]' } })
  expect(screen.getByText(/参数已修改/)).toBeTruthy()
  expect(fetch).toHaveBeenCalledOnce()
  // A replacement request must clear the previous result while in flight.
  let finish!: (r: Response) => void
  fetch.mockImplementationOnce(() => new Promise(resolve => { finish = resolve }))
  fireEvent.click(screen.getByRole('button', { name: '开始研究' }))
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
  expect(screen.queryByText('当前价差相对于可比历史样本处于什么位置？')).toBeNull()
  expect(screen.getByText('正在准备所需数据并计算结果，请稍候。')).toBeTruthy()
  const changed = structuredClone(fixture); changed.request.histogram_edges = [-1, 0, 1]
  await act(async () => finish(new Response(JSON.stringify(changed))))
  await screen.findByText(/服务返回的数据未通过完整性验证/)
})
it('parses only explicit increasing finite edges', () => {
  expect(parseEdges('')).toBeUndefined()
  expect(parseEdges('[0,1]')).toEqual([0,1])
  for (const value of ['[]', '[1,0]', '[0,0]', 'null', '[true,2]', '[0,1e400]']) expect(() => parseEdges(value)).toThrow()
})

it('submits new metric and date identity only after explicit activation', async () => {
  dispose = installRequestBoundary(createRequestBoundary(vi.fn()))
  const signed = (await import('../testing/signed_spread.json')).default
  const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(fixture))).mockResolvedValueOnce(new Response(JSON.stringify(signed)))
  vi.stubGlobal('fetch', fetch)
  render(<RelativeValuePage />)
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Product' }))
  fireEvent.click(screen.getByText('IM', { selector: '.ant-select-item-option-content' }))
  commitDate(screen.getByLabelText('History Start'), fixture.request.history_start)
  commitDate(screen.getByLabelText('Evaluation Date'), fixture.request.evaluation_date)
  fireEvent.change(screen.getByLabelText('Histogram Edges'), { target: { value: '[-0.1,0,0.1]' } })
  fireEvent.click(screen.getByRole('button', { name: '开始研究' }))
  await screen.findByText('当前价差相对于可比历史样本处于什么位置？')
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Metric' }))
  fireEvent.click(screen.getByText('Signed Spread（点）', { selector: '.ant-select-item-option-content' }))
  commitDate(screen.getByLabelText('History Start'), signed.request.history_start)
  fireEvent.change(screen.getByLabelText('Histogram Edges'), { target: { value: '' } })
  expect(fetch).toHaveBeenCalledOnce()
  expect(screen.getByText(/参数已修改/)).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: '开始研究' }))
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2))
  expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({ product_code: 'IM', history_start: signed.request.history_start, evaluation_date: signed.request.evaluation_date, metric: 'signed_spread' })
  await waitFor(() => expect(screen.queryByText(/参数已修改/)).toBeNull())
  expect(screen.getAllByTestId('plot')[0].getAttribute('data-axis')).toBe('linear')
})
