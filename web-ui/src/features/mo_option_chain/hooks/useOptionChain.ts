import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ChainRequestError, loadMoOptionChain } from '../api/moOptionChain'
import type { OptionChain } from '../api/moOptionChain'
import { DEFAULT_SERIES_COLORS } from '../model/presentationState'
import type { SeriesColors } from '../model/presentationState'
import { MIN_STRIKE_HALF_RANGE_POINTS, STRIKE_HALF_RANGE_STEP, strikeViewport } from '../model/strikeViewport'

export type OptionChainPageState =
  | { status: 'idle' }
  | { status: 'loading'; date: string }
  | { status: 'success'; chain: OptionChain }
  | { status: 'error'; date: string; error: ChainRequestError }

function useOptionChainPresentation() {
  const [strikeHalfRangePoints, setStrikeHalfRangePoints] = useState(MIN_STRIKE_HALF_RANGE_POINTS)
  const [selectedExpiries, setSelectedExpiries] = useState<string[]>([])
  const [seriesColors, setSeriesColors] = useState<SeriesColors>(DEFAULT_SERIES_COLORS)

  const clearExpiries = useCallback(() => setSelectedExpiries([]), [])
  const selectAllExpiries = useCallback((chain: OptionChain) => {
    setSelectedExpiries(chain.expiries.map((group) => group.expiry_date))
  }, [])
  const toggleExpiry = useCallback((expiryDate: string) => {
    setSelectedExpiries((current) => current.includes(expiryDate)
      ? current.length > 1 ? current.filter((date) => date !== expiryDate) : current
      : [...current, expiryDate])
  }, [])
  const changeSeriesColor = useCallback((side: keyof SeriesColors, color: string) => {
    setSeriesColors((current) => ({ ...current, [side]: color }))
  }, [])

  return {
    strikeHalfRangePoints,
    selectedExpiries,
    seriesColors,
    clearExpiries,
    selectAllExpiries,
    toggleExpiry,
    changeSeriesColor,
    shrinkViewport: () => setStrikeHalfRangePoints((value) => Math.max(
      MIN_STRIKE_HALF_RANGE_POINTS,
      value - STRIKE_HALF_RANGE_STEP,
    )),
    expandViewport: () => setStrikeHalfRangePoints((value) => value + STRIKE_HALF_RANGE_STEP),
  }
}

function useOptionChainQuery(
  clearExpiries: () => void,
  selectAllExpiries: (chain: OptionChain) => void,
) {
  const [selectedDate, setSelectedDate] = useState('')
  const [page, setPage] = useState<OptionChainPageState>({ status: 'idle' })
  const request = useRef<AbortController | null>(null)
  const nextRequestId = useRef(0)

  useEffect(() => () => {
    nextRequestId.current += 1
    request.current?.abort()
  }, [])

  const selectDate = useCallback((date: string) => {
    request.current?.abort()
    const id = ++nextRequestId.current
    setSelectedDate(date)
    clearExpiries()

    if (!date) {
      request.current = null
      setPage({ status: 'idle' })
      return
    }

    const controller = new AbortController()
    request.current = controller
    setPage({ status: 'loading', date })
    void loadMoOptionChain(date, controller.signal).then((chain) => {
      if (nextRequestId.current === id && !controller.signal.aborted) {
        selectAllExpiries(chain)
        setPage({ status: 'success', chain })
      }
    }).catch((error: unknown) => {
      if (nextRequestId.current !== id || controller.signal.aborted) return
      setPage({
        status: 'error',
        date,
        error: error instanceof ChainRequestError
          ? error
          : new ChainRequestError('network', '无法连接数据服务'),
      })
    })
  }, [clearExpiries, selectAllExpiries])

  return { selectedDate, page, selectDate }
}

export function useOptionChain() {
  const presentation = useOptionChainPresentation()
  const query = useOptionChainQuery(presentation.clearExpiries, presentation.selectAllExpiries)
  const chain = query.page.status === 'success' ? query.page.chain : null
  const selectedSet = useMemo(() => new Set(presentation.selectedExpiries), [presentation.selectedExpiries])
  const selectedGroups = useMemo(() => chain === null
    ? []
    : chain.expiries.filter((group) => selectedSet.has(group.expiry_date)), [chain, selectedSet])
  const xDomain = useMemo(() => chain === null
    ? null
    : strikeViewport(chain.underlying.price, presentation.strikeHalfRangePoints), [chain, presentation.strikeHalfRangePoints])
  return {
    ...query,
    ...presentation,
    selectedSet,
    selectedGroups,
    xDomain,
  }
}
