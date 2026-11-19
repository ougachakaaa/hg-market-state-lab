import { strategyRoutesFixture } from '../../tests/static/strategyRoutesFixture'
import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { useWorkspaceRoute } from './routes'
import { useRunNavigation } from './useRunNavigation'

const backtest = '/backtesting/futures-roll-long'
const research = '/research/futures-basis'
function useNavigation() {
  const route = useWorkspaceRoute(strategyRoutesFixture)
  return { path: route.path, navigate: useRunNavigation(route.navigate) }
}
function visit(url: string) {
  act(() => {
    window.history.replaceState(null, '', url)
    window.dispatchEvent(new PopStateEvent('popstate'))
  })
}
afterEach(() => { cleanup(); window.history.replaceState(null, '', '/') })

it('samples the latest URL, restores each route separately and roundtrips opaque IDs', () => {
  const opaque = ' B+/&?=#中 '
  window.history.replaceState(null, '', `${backtest}?run_id=A`)
  const { result } = renderHook(useNavigation)
  // No application rerender follows a feature's accepted submission.
  window.history.pushState(null, '', `${backtest}?${new URLSearchParams({ run_id: opaque })}`)
  act(() => result.current.navigate(research))
  expect(window.location.search).toBe('')
  window.history.pushState(null, '', `${research}?run_id=C`)
  act(() => result.current.navigate(backtest))
  expect(new URLSearchParams(window.location.search).get('run_id')).toBe(opaque)
  act(() => result.current.navigate(research))
  expect(window.location.search).toBe('?run_id=C')
})

it('preserves same-page URLs and history, including a missing identity', () => {
  window.history.replaceState(null, '', `${backtest}?run_id=A&other=1#details`)
  const { result } = renderHook(useNavigation)
  const length = window.history.length
  act(() => result.current.navigate(backtest))
  expect(window.location.search + window.location.hash).toBe('?run_id=A&other=1#details')
  expect(window.history.length).toBe(length)
  act(() => result.current.navigate('/research'))
  visit(backtest)
  act(() => result.current.navigate(backtest))
  expect(window.location.search).toBe('')
})

it.each(['', '?run_id='])('clears obsolete memory when leaving a Run URL with %s', query => {
  window.history.replaceState(null, '', `${backtest}?run_id=A`)
  const { result } = renderHook(useNavigation)
  act(() => result.current.navigate('/research'))
  visit(backtest + query)
  expect(window.location.search).toBe(query)
  act(() => result.current.navigate('/research'))
  act(() => result.current.navigate(backtest))
  expect(window.location.search).toBe('')
})

it('respects explicit history URLs instead of rewriting them with remembered identity', () => {
  window.history.replaceState(null, '', `${backtest}?run_id=B`)
  const { result } = renderHook(useNavigation)
  act(() => result.current.navigate('/research'))
  for (const query of ['?run_id=A', '', '?run_id=B']) {
    visit(backtest + query)
    expect(result.current.path).toBe(backtest)
    expect(window.location.search).toBe(query)
  }
})

it('does not retain identities from other routes or inherit memory across instances', () => {
  window.history.replaceState(null, '', '/data?run_id=unrelated')
  const first = renderHook(useNavigation)
  act(() => first.result.current.navigate(backtest))
  expect(window.location.search).toBe('')
  visit(`${backtest}?run_id=A`)
  act(() => first.result.current.navigate('/research'))
  first.unmount()
  const next = renderHook(useNavigation)
  act(() => next.result.current.navigate(backtest))
  expect(window.location.search).toBe('')
})

it('keeps the original Run identity during actual Back and Forward traversal', async () => {
  window.history.replaceState(null, '', `${backtest}?run_id=A`)
  const { result } = renderHook(useNavigation)
  act(() => result.current.navigate('/research'))
  act(() => result.current.navigate(backtest))
  window.history.pushState(null, '', `${backtest}?run_id=B`)
  act(() => result.current.navigate('/research'))
  await act(async () => { window.history.back() })
  await waitFor(() => expect(result.current.path).toBe(backtest))
  expect(window.location.search).toBe('?run_id=B')
  await act(async () => { window.history.back() })
  await waitFor(() => expect(window.location.search).toBe('?run_id=A'))
  await act(async () => { window.history.forward() })
  await waitFor(() => expect(window.location.search).toBe('?run_id=B'))
})

it('starts afresh on reload while preserving the explicit deep link', () => {
  window.history.replaceState(null, '', `${backtest}?run_id=A`)
  const first = renderHook(useNavigation)
  first.unmount()
  const next = renderHook(useNavigation)
  expect(next.result.current.path).toBe(backtest)
  expect(window.location.search).toBe('?run_id=A')
})
