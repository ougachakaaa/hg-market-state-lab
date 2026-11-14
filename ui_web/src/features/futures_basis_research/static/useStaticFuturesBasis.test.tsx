import { renderHook } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { useStaticFuturesBasis } from './useStaticFuturesBasis'
import { embeddedReportPayload, mismatchedReportPayload } from '../testing/embeddedReportFixture'

afterEach(() => vi.unstubAllGlobals())

it('validates the embedded report once and exposes the fixed request identity', () => {
  const fetch = vi.fn(() => { throw new Error('Unexpected network') })
  vi.stubGlobal('fetch', fetch)
  const before = structuredClone(embeddedReportPayload)
  const { result, rerender } = renderHook(() => useStaticFuturesBasis(embeddedReportPayload))
  expect(result.current.status).toBe('validated')
  if (result.current.status !== 'validated') throw new Error('expected a validated example')
  expect(result.current.data.request).toEqual({
    case: 'futures_basis_v1', product_code: 'IM', start_date: '2024-10-18', end_date: '2024-10-21', analysis_profile: 'r01a_standard_v1',
  })
  expect(result.current.data.report.profile).toBe('futures_basis_report_evidence_v1')
  expect(result.current.data.report.request.observation).toMatchObject({ start_date: '2024-10-18', end_date: '2024-10-21' })
  expect(embeddedReportPayload).toEqual(before)
  rerender()
  expect(result.current.status).toBe('validated')
  expect(fetch).not.toHaveBeenCalled()
})

it('reports an invalid embedded example instead of mounting a report', () => {
  const { result } = renderHook(() => useStaticFuturesBasis(mismatchedReportPayload))
  expect(result.current.status).toBe('invalid')
  if (result.current.status !== 'invalid') throw new Error('expected an invalid example')
  expect(String(result.current.error)).toMatch(/observation does not match/)
})
