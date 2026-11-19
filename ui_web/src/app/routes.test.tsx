import { strategyRoutesFixture as strategies } from '../../tests/static/strategyRoutesFixture'
import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { workspaceRoutes, isFixedWorkspacePath, isStaticWorkspacePath } from './routeInventory'
import { useWorkspaceRoute } from './routes'
import { hashWorkspacePath, staticHref, useHashRoute } from '../../demo/runtime/hashRoutes'

afterEach(() => { cleanup(); window.history.replaceState(null, '', '/') })

describe('canonical routes and runtime adapters', () => {
  it('declares ten fixed Production and Static pages once', () => {
    expect(workspaceRoutes.map(route => route.path)).toEqual([
      '/research', '/research/futures-basis', '/research/calendar-spread-relative-value', '/research/publications', '/data',
      '/data/mo-option-chain', '/data/mo-premium-plane', '/data/futures-calendar-spread', '/backtesting', '/backtesting/futures-roll-long',
    ])
    expect(new Set(workspaceRoutes.map(route => route.path)).size).toBe(10)
    for (const route of workspaceRoutes) {
      expect(isFixedWorkspacePath(route.path)).toBe(true)
      expect(hashWorkspacePath(staticHref(route.path), strategies)).toBe(isStaticWorkspacePath(route.path) ? route.path : strategies.defaultPath)
    }
    expect(workspaceRoutes.filter(route => isStaticWorkspacePath(route.path))).toHaveLength(10)
    expect(isFixedWorkspacePath('/unknown')).toBe(false)
    expect(workspaceRoutes.filter(route => route.area === '/research' && route.sidebarVisible).map(route => route.path))
      .toEqual(['/research', '/research/futures-basis', '/research/calendar-spread-relative-value'])
  })

  it.each(['/research/futures-basis', '/backtesting/futures-roll-long'] as const)('preserves %s run identity on mount, same-page navigation and history', path => {
    window.history.replaceState(null, '', `${path}?run_id=first`)
    const { result } = renderHook(() => useWorkspaceRoute(strategies))
    expect(result.current.path).toBe(path)
    act(() => result.current.navigate(path))
    expect(window.location.search).toBe('?run_id=first')
    act(() => result.current.navigate('/data'))
    expect(window.location.search).toBe('')
    act(() => {
      window.history.replaceState(null, '', `${path}?run_id=restored`)
      window.dispatchEvent(new PopStateEvent('popstate'))
    })
    expect(result.current.path).toBe(path)
    expect(window.location.search).toBe('?run_id=restored')
  })

  it.each(['', '#', '#unknown', '#/unknown', '#section-1'])('normalizes unknown/empty hash %s without leaving the base', hash => {
    window.history.replaceState(null, '', `/hg-market-state-lab/${hash}`)
    const { result } = renderHook(() => useHashRoute(strategies))
    expect(result.current.path).toBe(strategies.defaultPath)
    expect(window.location.pathname).toBe('/hg-market-state-lab/')
    expect(window.location.hash).toBe(staticHref(strategies.defaultPath))
  })

  it('isolates static route identity from server Run query and synchronizes hash changes', () => {
    window.history.replaceState(null, '', '/hg-market-state-lab/#/backtesting?run_id=server')
    const { result } = renderHook(() => useHashRoute(strategies))
    expect(result.current.path).toBe('/backtesting')
    expect(window.location.hash).toBe('#/backtesting')
    act(() => result.current.navigate('/research/publications'))
    expect(window.location.hash).toBe('#/research/publications')
    act(() => {
      window.history.replaceState(null, '', '/hg-market-state-lab/#/data')
      window.dispatchEvent(new HashChangeEvent('hashchange'))
    })
    expect(result.current.path).toBe('/data')
  })
})

it('shares the overview icon identity across both areas', () => {
  expect(workspaceRoutes.find(route => route.path === '/data')?.icon).toBe('overview')
  expect(workspaceRoutes.find(route => route.path === '/research')?.icon).toBe('overview')
})

it('normalizes legacy Run deep links on mount and history without losing identity', () => {
  window.history.replaceState(null, '', '/backtesting?run_id=first&source=bookmark#details')
  const length = window.history.length
  const { result } = renderHook(() => useWorkspaceRoute(strategies))
  expect(result.current.path).toBe('/backtesting/futures-roll-long')
  expect(window.location.search).toBe('?run_id=first&source=bookmark')
  expect(window.location.hash).toBe('#details')
  expect(window.history.length).toBe(length)
  act(() => {
    window.history.replaceState(null, '', '/backtesting?run_id=second')
    window.dispatchEvent(new PopStateEvent('popstate'))
  })
  expect(result.current.path).toBe('/backtesting/futures-roll-long')
  expect(window.location.search).toBe('?run_id=second')
  act(() => result.current.navigate('/backtesting'))
  expect(result.current.path).toBe('/backtesting')
  expect(window.location.search).toBe('')
})

it('uses one overview icon and one instance icon across every visible route', () => {
  const overviews = ['/data', '/research', '/backtesting']
  for (const route of workspaceRoutes.filter(route => route.sidebarVisible)) {
    expect(route.icon).toBe(overviews.includes(route.path) ? 'overview' : 'instance')
  }
})

it('uses the graph order and a single resolver for strategy aliases, valid IDs and unknown IDs', () => {
  const [first, second] = strategies.entries
  expect(first.path).toBe(strategies.defaultPath)
  expect(strategies.match(second.path)).toEqual(second)
  expect(isFixedWorkspacePath(second.path)).toBe(false)
  for (const mode of ['production', 'static'] as const) {
    expect(strategies.resolve(second.path, mode)).toBe(second.path)
    for (const path of ['/roadmap', '/roadmap/strategy-missing', `${second.path}/extra`]) {
      expect(strategies.resolve(path, mode)).toBe(first.path)
    }
  }
})

it('normalizes Online strategy aliases only after authentication and restores other strategies from history', () => {
  const second = strategies.entries[1].path
  window.history.replaceState(null, '', '/roadmap')
  const { result, rerender } = renderHook(({ authenticated }) => useWorkspaceRoute(strategies, authenticated), {
    initialProps: { authenticated: false },
  })
  expect(window.location.pathname).toBe('/roadmap')
  const length = window.history.length
  rerender({ authenticated: true })
  expect(window.location.pathname).toBe(strategies.defaultPath)
  expect(window.history.length).toBe(length)
  act(() => {
    window.history.replaceState(null, '', second)
    window.dispatchEvent(new PopStateEvent('popstate'))
  })
  expect(result.current.path).toBe(second)
  expect(window.location.pathname).toBe(second)
})

it('normalizes a legacy static alias inside the Demo base and accepts canonical strategy hashes', () => {
  window.history.replaceState(null, '', '/hg-market-state-lab/#/roadmap')
  const { result } = renderHook(() => useHashRoute(strategies))
  expect(window.location.hash).toBe(staticHref(strategies.defaultPath))
  const second = strategies.entries[1].path
  act(() => result.current.navigate(second))
  expect(result.current.path).toBe(second)
  expect(window.location.hash).toBe(staticHref(second))
  expect(window.location.pathname).toBe('/hg-market-state-lab/')
})
