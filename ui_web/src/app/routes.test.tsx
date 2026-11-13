import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { workspaceRoutes, isWorkspacePath } from './routeInventory'
import { useWorkspaceRoute } from './routes'
import { hashWorkspacePath, staticHref, useHashRoute } from '../demo/shell/hashRoutes'

afterEach(() => { cleanup(); window.history.replaceState(null, '', '/') })

describe('canonical routes and runtime adapters', () => {
  it('declares each of the seven formal pages once', () => {
    expect(workspaceRoutes.map(route => route.path)).toEqual([
      '/research', '/research/futures-basis', '/research/publications', '/data',
      '/data/mo-option-chain', '/data/mo-premium-plane', '/backtesting',
    ])
    expect(new Set(workspaceRoutes.map(route => route.path)).size).toBe(7)
    for (const route of workspaceRoutes) {
      expect(isWorkspacePath(route.path)).toBe(true)
      expect(hashWorkspacePath(staticHref(route.path))).toBe(route.path)
    }
    expect(isWorkspacePath('/unknown')).toBe(false)
  })

  it.each(['/research/futures-basis', '/backtesting'] as const)('preserves %s run identity on mount, same-page navigation and history', path => {
    window.history.replaceState(null, '', `${path}?run_id=first`)
    const { result } = renderHook(useWorkspaceRoute)
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
    const { result } = renderHook(useHashRoute)
    expect(result.current.path).toBe('/research')
    expect(window.location.pathname).toBe('/hg-market-state-lab/')
    expect(window.location.hash).toBe('#/research')
  })

  it('isolates static route identity from server Run query and synchronizes hash changes', () => {
    window.history.replaceState(null, '', '/hg-market-state-lab/#/backtesting?run_id=server')
    const { result } = renderHook(useHashRoute)
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
