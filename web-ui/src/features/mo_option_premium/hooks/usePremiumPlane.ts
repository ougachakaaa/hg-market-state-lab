import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { loadMoOptionPremiumPlane, PremiumRequestError } from '../api/moOptionPremium'
import type { PremiumPlane, PremiumPriceType } from '../api/moOptionPremium'
import { projectPremiumPlane } from '../model/premiumPlane'
import type {
  SelectedOptionType,
  SelectedReferenceBasis,
  SelectedRepresentation,
  SelectedTimeNormalization,
  SelectedValueBasis,
} from '../model/premiumPlane'

export type PremiumPageState =
  | { status: 'idle' }
  | { status: 'loading'; asOf: string; priceType: PremiumPriceType }
  | { status: 'success'; plane: PremiumPlane; rawPayload: unknown }
  | { status: 'error'; asOf: string; priceType: PremiumPriceType; error: PremiumRequestError }

function usePremiumPresentation() {
  const [selectedOptionType, setSelectedOptionType] = useState<SelectedOptionType>('call')
  const [selectedReferenceBasis, setSelectedReferenceBasis] = useState<SelectedReferenceBasis>('underlying_spot')
  const [selectedValueBasis, setSelectedValueBasis] = useState<SelectedValueBasis>('total')
  const [selectedTimeNormalization, setSelectedTimeNormalization] = useState<SelectedTimeNormalization>('annualized')
  const [selectedRepresentation, setSelectedRepresentation] = useState<SelectedRepresentation>('points')
  const [selectedExpiries, setSelectedExpiries] = useState<string[]>([])

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

  return {
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
    resetPresentation,
    selectAllExpiries,
    toggleExpiry,
  }
}

function usePremiumQuery(
  resetPresentation: () => void,
  selectAllExpiries: (plane: PremiumPlane) => void,
) {
  const [selectedDate, setSelectedDate] = useState('')
  const [priceType, setPriceType] = useState<PremiumPriceType>('close')
  const [page, setPage] = useState<PremiumPageState>({ status: 'idle' })
  const request = useRef<AbortController | null>(null)
  const nextRequestId = useRef(0)

  useEffect(() => () => {
    nextRequestId.current += 1
    request.current?.abort()
  }, [])

  const load = useCallback((asOf: string, requestedPriceType: PremiumPriceType) => {
    request.current?.abort()
    const id = ++nextRequestId.current
    resetPresentation()
    if (!asOf) {
      request.current = null
      setPage({ status: 'idle' })
      return
    }

    const controller = new AbortController()
    request.current = controller
    setPage({ status: 'loading', asOf, priceType: requestedPriceType })
    void loadMoOptionPremiumPlane(asOf, requestedPriceType, controller.signal).then((result) => {
      if (nextRequestId.current === id && !controller.signal.aborted) {
        selectAllExpiries(result.plane)
        setPage({ status: 'success', plane: result.plane, rawPayload: result.rawPayload })
      }
    }).catch((error: unknown) => {
      if (nextRequestId.current !== id || controller.signal.aborted) return
      setPage({
        status: 'error',
        asOf,
        priceType: requestedPriceType,
        error: error instanceof PremiumRequestError
          ? error
          : new PremiumRequestError('invalid_response', 'The page could not process the response'),
      })
    })
  }, [resetPresentation, selectAllExpiries])

  const selectDate = useCallback((asOf: string) => {
    setSelectedDate(asOf)
    load(asOf, priceType)
  }, [load, priceType])
  const selectPriceType = useCallback((value: PremiumPriceType) => {
    setPriceType(value)
    if (selectedDate) load(selectedDate, value)
  }, [load, selectedDate])

  return { selectedDate, priceType, page, selectDate, selectPriceType }
}

export function usePremiumPlane() {
  const presentation = usePremiumPresentation()
  const query = usePremiumQuery(presentation.resetPresentation, presentation.selectAllExpiries)
  const selectedExpirySet = useMemo(() => new Set(presentation.selectedExpiries), [presentation.selectedExpiries])
  const projection = useMemo(() => query.page.status === 'success'
    ? projectPremiumPlane(
      query.page.plane,
      presentation.selectedOptionType,
      presentation.selectedReferenceBasis,
      presentation.selectedValueBasis,
      presentation.selectedTimeNormalization,
      presentation.selectedRepresentation,
      selectedExpirySet,
    )
    : null, [
      query.page,
      presentation.selectedOptionType,
      presentation.selectedReferenceBasis,
      presentation.selectedValueBasis,
      presentation.selectedTimeNormalization,
      presentation.selectedRepresentation,
      selectedExpirySet,
    ])

  return { ...query, ...presentation, selectedExpirySet, projection }
}
