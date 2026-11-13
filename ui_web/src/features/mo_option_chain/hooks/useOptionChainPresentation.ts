import { useCallback, useMemo, useState } from 'react'
import type { OptionChain } from '../api/validateOptionChain'
import { DEFAULT_SERIES_COLORS } from '../model/presentationState'
import type { SeriesColors } from '../model/presentationState'
import { MIN_STRIKE_HALF_RANGE_POINTS, STRIKE_HALF_RANGE_STEP, strikeViewport } from '../model/strikeViewport'

export function useOptionChainPresentation(chain: OptionChain | null) {
  const [strikeHalfRangePoints, setStrikeHalfRangePoints] = useState(MIN_STRIKE_HALF_RANGE_POINTS)
  const [result, setResult] = useState(chain)
  const [selectedExpiries, setSelectedExpiries] = useState<string[]>(() => chain?.expiries.map(group => group.expiry_date) ?? [])

  // Reset selection for each new result, before children render; keep viewport/colors.
  if (result !== chain) {
    setResult(chain)
    setSelectedExpiries(chain?.expiries.map(group => group.expiry_date) ?? [])
  }
  const [seriesColors, setSeriesColors] = useState<SeriesColors>(DEFAULT_SERIES_COLORS)

  const toggleExpiry = useCallback((expiryDate: string) => {
    setSelectedExpiries((current) => current.includes(expiryDate)
      ? current.length > 1 ? current.filter((date) => date !== expiryDate) : current
      : [...current, expiryDate])
  }, [])
  const changeSeriesColor = useCallback((side: keyof SeriesColors, color: string) => {
    setSeriesColors((current) => ({ ...current, [side]: color }))
  }, [])

  const selectedSet = useMemo(() => new Set(selectedExpiries), [selectedExpiries])
  const selectedGroups = useMemo(() => chain === null
    ? []
    : chain.expiries.filter((group) => selectedSet.has(group.expiry_date)), [chain, selectedSet])
  const xDomain = useMemo(() => chain === null
    ? null
    : strikeViewport(chain.underlying.price, strikeHalfRangePoints), [chain, strikeHalfRangePoints])
  return {
    selectedSet,
    selectedGroups,
    xDomain,
    strikeHalfRangePoints,
    selectedExpiries,
    seriesColors,
    toggleExpiry,
    changeSeriesColor,
    shrinkViewport: () => setStrikeHalfRangePoints((value) => Math.max(
      MIN_STRIKE_HALF_RANGE_POINTS,
      value - STRIKE_HALF_RANGE_STEP,
    )),
    expandViewport: () => setStrikeHalfRangePoints((value) => value + STRIKE_HALF_RANGE_STEP),
  }
}
