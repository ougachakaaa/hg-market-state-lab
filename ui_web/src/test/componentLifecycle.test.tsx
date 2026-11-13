import { act, renderHook } from '@testing-library/react'
import { useDelayState } from '@rc-component/util'
import { expect, it, vi } from 'vitest'

it('cancels the real Ant Design utility delayed update when its consumer unmounts', () => {
  vi.useFakeTimers()
  const { result, unmount } = renderHook(() => useDelayState(false))
  try {
    act(() => result.current[1](true, { ms: 1000 }))
    expect(vi.getTimerCount()).toBe(1)
    unmount()
    expect(vi.getTimerCount()).toBe(0)
  } finally {
    unmount()
    vi.useRealTimers()
  }
})
