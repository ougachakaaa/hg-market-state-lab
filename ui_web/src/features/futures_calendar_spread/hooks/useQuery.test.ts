import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { useQuery } from './useQuery'
import { loadQuery, QueryError } from '../api/query'
import type { Query, Result } from '../api/validateResult'
import fixture from '../testing/daily.json'
vi.mock('../api/query', async original => ({ ...await original(), loadQuery: vi.fn() }))
const query: Query = { product_code: 'IM', trade_date: '2024-10-18' }
const response = fixture as Result
afterEach(() => { cleanup(); vi.resetAllMocks() })
it('submits explicitly, aborts superseded work and ignores late success after newer success', async () => {
  let first!: (r: Result) => void
  vi.mocked(loadQuery).mockImplementationOnce(() => new Promise(resolve => { first = resolve })).mockResolvedValueOnce(response)
  const { result, unmount } = renderHook(useQuery)
  expect(loadQuery).not.toHaveBeenCalled()
  act(() => result.current.submit(query))
  const signal = vi.mocked(loadQuery).mock.calls[0][1]
  act(() => result.current.submit({ ...query, product_code: 'IF' }))
  expect(signal.aborted).toBe(true)
  await waitFor(() => expect(result.current.state.status).toBe('success'))
  await act(async () => first({ ...response, case: 'late' } as unknown as Result))
  expect(result.current.state).toMatchObject({ status: 'success', query: { product_code: 'IF' }, result: response })
  unmount()
  expect(vi.mocked(loadQuery).mock.calls[1][1].aborted).toBe(true)
})
it('retry uses the failed submitted snapshot, with no automatic retry', async () => {
  vi.mocked(loadQuery).mockRejectedValueOnce(new QueryError('transport_busy')).mockResolvedValueOnce(response)
  const { result } = renderHook(useQuery)
  const input = { ...query }
  act(() => result.current.submit(input))
  input.product_code = 'IF'
  await waitFor(() => expect(result.current.state.status).toBe('error'))
  expect(loadQuery).toHaveBeenCalledOnce()
  act(() => result.current.retry())
  await waitFor(() => expect(result.current.state.status).toBe('success'))
  expect(vi.mocked(loadQuery).mock.calls[1][0]).toEqual(query)
})
it('unmount cancels a pending request and prevents completion', async () => {
  let finish!: (r: Result) => void
  vi.mocked(loadQuery).mockImplementation(() => new Promise(resolve => { finish = resolve }))
  const { result, unmount } = renderHook(useQuery)
  act(() => result.current.submit(query))
  const signal = vi.mocked(loadQuery).mock.calls[0][1]
  unmount(); expect(signal.aborted).toBe(true)
  await act(async () => finish(response))
})
