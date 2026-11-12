import { cleanup, renderHook } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { useStaticBacktesting } from './useStaticBacktesting'
import {
  embeddedBacktestResultPayload,
  invalidBacktestResultPayload,
  mismatchedBacktestResultPayload,
} from '../testing/backtestingFixture'

afterEach(cleanup)

it('validates the fixed request and complete embedded Result once without network or Run state', () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  const { result } = renderHook(() => useStaticBacktesting(embeddedBacktestResultPayload))
  expect(result.current.status).toBe('validated')
  if (result.current.status === 'validated') {
    expect(result.current.data.request).toBe(embeddedBacktestResultPayload.request)
    expect(result.current.data.result).toBe(embeddedBacktestResultPayload.result)
    expect(result.current.data.result.window.cffex_session_count).toBe(5)
  }
  expect(fetch).not.toHaveBeenCalled()
  vi.unstubAllGlobals()
})

it('exposes an invalid state for a Result outside the formal profile and for mismatched fixed requests', () => {
  for (const payload of [invalidBacktestResultPayload, mismatchedBacktestResultPayload]) {
    const { result, unmount } = renderHook(() => useStaticBacktesting(payload))
    expect(result.current.status).toBe('invalid')
    unmount()
  }
})
