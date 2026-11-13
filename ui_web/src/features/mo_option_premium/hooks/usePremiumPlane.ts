import { useCallback, useEffect, useRef, useState } from 'react'
import { loadMoOptionPremiumPlane, PremiumRequestError } from '../api/moOptionPremium'
import type { PremiumPlane, PremiumPriceType } from '../api/moOptionPremium'
import { usePremiumPresentation } from './usePremiumPresentation'

export type PremiumPageState =
  | { status: 'idle' }
  | { status: 'loading'; asOf: string; priceType: PremiumPriceType }
  | { status: 'success'; plane: PremiumPlane; rawPayload: unknown }
  | { status: 'error'; asOf: string; priceType: PremiumPriceType; error: PremiumRequestError }

function usePremiumQuery() {
  const [selectedDate, setSelectedDate] = useState('')
  const [priceType, setPriceType] = useState<PremiumPriceType>('close')
  const [page, setPage] = useState<PremiumPageState>({ status: 'idle' })
  const [queryRevision, setQueryRevision] = useState(0)
  const request = useRef<AbortController | null>(null)
  const nextRequestId = useRef(0)

  useEffect(() => () => {
    nextRequestId.current += 1
    request.current?.abort()
  }, [])

  const load = useCallback((asOf: string, requestedPriceType: PremiumPriceType) => {
    request.current?.abort()
    const id = ++nextRequestId.current
    setQueryRevision(value => value + 1)
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
  }, [])

  const selectDate = useCallback((asOf: string) => {
    setSelectedDate(asOf)
    load(asOf, priceType)
  }, [load, priceType])
  const selectPriceType = useCallback((value: PremiumPriceType) => {
    setPriceType(value)
    if (selectedDate) load(selectedDate, value)
  }, [load, selectedDate])

  return { selectedDate, priceType, page, selectDate, selectPriceType, queryRevision }
}

export function usePremiumPlane() {
  const query = usePremiumQuery()
  const presentation = usePremiumPresentation(query.page.status === 'success' ? query.page.plane : null, query.queryRevision)
  return { ...query, ...presentation }
}
