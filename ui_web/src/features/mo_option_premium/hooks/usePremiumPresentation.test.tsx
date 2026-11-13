import { act, renderHook } from '@testing-library/react'
import { expect, it } from 'vitest'
import { usePremiumPresentation } from './usePremiumPresentation'
import { plane } from '../testing/planeFixture'
import type { PremiumPlane } from '../api/validatePremiumPlane'

it('resets every local selection on static result replacement and query start, including consecutive loading queries', () => {
  const { result, rerender } = renderHook(({ data, revision }: { data: PremiumPlane | null; revision: number }) =>
    usePremiumPresentation(data, revision), { initialProps: { data: plane as PremiumPlane | null, revision: 0 } })
  const change = () => act(() => {
    result.current.setSelectedOptionType('put')
    result.current.setSelectedReferenceBasis('expiry_futures')
    result.current.setSelectedValueBasis('time_value')
    result.current.setSelectedTimeNormalization('unannualized')
    result.current.setSelectedRepresentation('yield')
    result.current.toggleExpiry('2026-10-23')
  })
  const defaults = () => {
    expect(result.current).toMatchObject({ selectedOptionType: 'call', selectedReferenceBasis: 'underlying_spot',
      selectedValueBasis: 'total', selectedTimeNormalization: 'annualized', selectedRepresentation: 'points' })
  }
  change()
  rerender({ data: structuredClone(plane), revision: 0 })
  defaults()
  expect(result.current.selectedExpiries).toEqual(plane.expiries.map(expiry => expiry.expiry_date))
  expect(result.current.selectedExpirySet.size).toBe(2)
  change()
  rerender({ data: null, revision: 1 })
  defaults()
  expect(result.current.projection).toBeNull()
  expect(result.current.selectedExpiries).toEqual([])
  act(() => result.current.setSelectedRepresentation('yield'))
  rerender({ data: null, revision: 2 })
  defaults()
})
