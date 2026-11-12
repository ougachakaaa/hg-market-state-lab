import { act, renderHook } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import { useOptionChainPresentation } from './useOptionChainPresentation'
import { chain } from '../testing/chainFixture'
import type { OptionChain } from '../api/validateOptionChain'

it('runs on static results, resets expiry selection on replacement, and retains local preferences', () => {
  const fetch = vi.spyOn(globalThis, 'fetch')
  try {
    const { result, rerender } = renderHook(({ data }: { data: OptionChain | null }) => useOptionChainPresentation(data), { initialProps: { data: chain as OptionChain | null } })
    expect(result.current.selectedGroups).toEqual(chain.expiries)
    act(() => {
      result.current.toggleExpiry('2026-10-23')
      result.current.toggleExpiry('2026-11-27')
      result.current.toggleExpiry('2026-09-25')
      result.current.changeSeriesColor('call', '#e11d48')
      result.current.expandViewport()
    })
    expect(result.current.selectedExpiries).toEqual(['2026-09-25'])
    rerender({ data: { ...chain } })
    expect(result.current.selectedGroups).toEqual(chain.expiries)
    expect(result.current.seriesColors.call).toBe('#e11d48')
    expect(result.current.strikeHalfRangePoints).toBe(400)
    rerender({ data: null })
    expect(result.current.selectedExpiries).toEqual([])
    expect(result.current.selectedGroups).toEqual([])
    expect(result.current.xDomain).toBeNull()
    expect(fetch).not.toHaveBeenCalled()
  } finally { fetch.mockRestore() }
})
