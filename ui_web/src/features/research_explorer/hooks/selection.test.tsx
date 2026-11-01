import { act, renderHook, waitFor } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
vi.mock('react-plotly.js', () => ({ default: () => null }))
vi.mock('../api/research', () => ({
  listPublications: vi.fn().mockResolvedValue({ data: [], next_cursor: 'opaque' }),
  getPublication: vi.fn().mockResolvedValue({}),
  getAnalysis: vi.fn().mockResolvedValue({}),
  getChartView: vi.fn(),
}))
import { getChartView, getAnalysis, getPublication, listPublications } from '../api/research'
import { useExplorer } from './useExplorer'
it('requests details only on selection and ignores obsolete view completions', async () => {
  const pending: { signal: AbortSignal; finish: (value: unknown) => void }[] = []
  vi.mocked(getChartView).mockImplementation((_p, _v, signal) => new Promise(resolve => pending.push({ signal, finish: resolve as (v: unknown) => void })))
  const { result } = renderHook(() => useExplorer())
  await waitFor(() => expect(result.current.list.status).toBe('success'))
  expect(getPublication).not.toHaveBeenCalled()
  act(() => result.current.next('opaque+/='))
  await waitFor(() => expect(listPublications).toHaveBeenCalledWith('opaque+/=', expect.any(AbortSignal)))
  act(() => result.current.selectPublication('p'))
  await waitFor(() => expect(result.current.manifest.status).toBe('success'))
  expect(getAnalysis).not.toHaveBeenCalled()
  expect(getChartView).not.toHaveBeenCalled()
  act(() => result.current.selectAnalysis('a'))
  await waitFor(() => expect(result.current.result.status).toBe('success'))
  expect(getChartView).not.toHaveBeenCalled()
  act(() => result.current.setView('count'))
  act(() => result.current.setView('frequency'))
  expect(pending[0].signal.aborted).toBe(true)
  await act(async () => pending[1].finish({ title: 'frequency' }))
  await waitFor(() => expect(result.current.chart.status).toBe('success'))
  await act(async () => pending[0].finish({ title: 'count' }))
  expect(result.current.chart.status === 'success' && result.current.chart.data).toEqual({ title: 'frequency' })
  act(() => result.current.selectAnalysis('other'))
  expect(result.current.chart.status).toBe('idle')
})
