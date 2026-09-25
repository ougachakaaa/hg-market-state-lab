import type { OptionChain } from '../api/moOptionChain'
import CombinedExpiryChart from '../charts/CombinedExpiryChart'
import { buildExpiryPalette } from '../charts/expiryPalette'
import type { SeriesColors } from '../model/presentationState'
import { ExpirySelector, SeriesColorControls } from './OptionChainControls'
import { ExpiryDetails } from './OptionChainResults'

export function OptionChainVisualization({ chain, selectedExpiries, selectedSet, selectedGroups, xDomain,
  seriesColors, toggleExpiry, changeSeriesColor }: {
  chain: OptionChain
  selectedExpiries: string[]
  selectedSet: ReadonlySet<string>
  selectedGroups: OptionChain['expiries']
  xDomain: [number, number]
  seriesColors: SeriesColors
  toggleExpiry: (expiryDate: string) => void
  changeSeriesColor: (side: keyof SeriesColors, color: string) => void
}) {
  const palette = buildExpiryPalette(chain.expiries, seriesColors)
  return (
    <>
      <ExpirySelector expiries={chain.expiries} selectedExpiries={selectedExpiries}
        palette={palette} toggleExpiry={toggleExpiry} />
      <SeriesColorControls colors={seriesColors} changeColor={changeSeriesColor} />
      <CombinedExpiryChart chain={chain} selectedExpiries={selectedSet} xDomain={xDomain} palette={palette} />
      <ExpiryDetails groups={selectedGroups} palette={palette} />
    </>
  )
}
