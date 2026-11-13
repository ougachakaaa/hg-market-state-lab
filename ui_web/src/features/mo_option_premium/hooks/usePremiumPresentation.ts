import { useCallback, useMemo, useState } from 'react'
import type { PremiumPlane } from '../api/validatePremiumPlane'
import { projectPremiumPlane } from '../model/premiumPlane'
import type {
  SelectedOptionType,
  SelectedReferenceBasis,
  SelectedRepresentation,
  SelectedTimeNormalization,
  SelectedValueBasis,
} from '../model/premiumPlane'

export function usePremiumPresentation(plane: PremiumPlane | null, queryRevision = 0) {
  const [selectedOptionType, setSelectedOptionType] = useState<SelectedOptionType>('call')
  const [selectedReferenceBasis, setSelectedReferenceBasis] = useState<SelectedReferenceBasis>('underlying_spot')
  const [selectedValueBasis, setSelectedValueBasis] = useState<SelectedValueBasis>('total')
  const [selectedTimeNormalization, setSelectedTimeNormalization] = useState<SelectedTimeNormalization>('annualized')
  const [selectedRepresentation, setSelectedRepresentation] = useState<SelectedRepresentation>('points')
  const [selectedExpiries, setSelectedExpiries] = useState<string[]>(() => plane?.expiries.map(expiry => expiry.expiry_date) ?? [])

  const resetPresentation = useCallback(() => {
    setSelectedOptionType('call')
    setSelectedReferenceBasis('underlying_spot')
    setSelectedValueBasis('total')
    setSelectedTimeNormalization('annualized')
    setSelectedRepresentation('points')
    setSelectedExpiries([])
  }, [])
  const selectAllExpiries = useCallback((plane: PremiumPlane) => {
    setSelectedExpiries(plane.expiries.map((expiry) => expiry.expiry_date))
  }, [])
  const toggleExpiry = useCallback((expiryDate: string) => {
    setSelectedExpiries((current) => current.includes(expiryDate)
      ? current.length > 1 ? current.filter((date) => date !== expiryDate) : current
      : [...current, expiryDate])
  }, [])

  // A query can start again while no result is loaded, so result identity alone
  // cannot express Production's reset-at-query-start rule.
  const [previous, setPrevious] = useState({ plane, queryRevision, revision: 0 })
  if (previous.plane !== plane || previous.queryRevision !== queryRevision) {
    setPrevious({ plane, queryRevision, revision: previous.revision + 1 })
    resetPresentation()
    if (plane) selectAllExpiries(plane)
  }
  const selectedExpirySet = useMemo(() => new Set(selectedExpiries), [selectedExpiries])
  const projection = useMemo(() => plane === null ? null : projectPremiumPlane(
    plane, selectedOptionType, selectedReferenceBasis, selectedValueBasis,
    selectedTimeNormalization, selectedRepresentation, selectedExpirySet,
  ), [plane, selectedOptionType, selectedReferenceBasis, selectedValueBasis,
    selectedTimeNormalization, selectedRepresentation, selectedExpirySet])

  return {
    resultRevision: previous.revision,
    selectedOptionType,
    selectedReferenceBasis,
    selectedValueBasis,
    selectedTimeNormalization,
    selectedRepresentation,
    selectedExpiries,
    setSelectedOptionType,
    setSelectedReferenceBasis,
    setSelectedValueBasis,
    setSelectedTimeNormalization,
    setSelectedRepresentation,
    selectedExpirySet,
    projection,
    toggleExpiry,
  }
}
