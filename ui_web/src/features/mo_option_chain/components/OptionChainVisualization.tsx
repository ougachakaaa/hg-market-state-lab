import { Collapse, Flex, Space, Typography } from 'antd'
import type { OptionChain } from '../api/validateOptionChain'
import CombinedExpiryChart from '../charts/CombinedExpiryChart'
import { buildExpiryPalette } from '../charts/expiryPalette'
import type { SeriesColors } from '../model/presentationState'
import { ExpirySelector, SeriesColorControls, StrikeViewportControl } from './OptionChainControls'
import { ExpiryDetails } from './OptionChainResults'

export function OptionChainVisualization({ chain, selectedExpiries, selectedSet, selectedGroups, xDomain,
  seriesColors, toggleExpiry, changeSeriesColor, halfRangePoints, shrink, expand }: {
  halfRangePoints: number
  shrink: () => void
  expand: () => void
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
    <Space orientation="vertical" size="middle" style={{ display: 'flex' }}>
      <Flex vertical gap="small" role="group" aria-label="期权链展示设置">
        <Typography.Text type="secondary">展示设置 · 仅调整当前结果</Typography.Text>
        <Flex gap="middle" wrap align="center" justify="space-between">
          <ExpirySelector expiries={chain.expiries} selectedExpiries={selectedExpiries}
            palette={palette} toggleExpiry={toggleExpiry} />
          <StrikeViewportControl halfRangePoints={halfRangePoints} shrink={shrink} expand={expand} />
        </Flex>
        <Collapse ghost size="small" items={[{ key: 'colors', label: '高级设置 · 图表颜色', children: <SeriesColorControls colors={seriesColors} changeColor={changeSeriesColor} /> }]} />
      </Flex>
      <CombinedExpiryChart chain={chain} selectedExpiries={selectedSet} xDomain={xDomain} palette={palette} />
      <ExpiryDetails groups={selectedGroups} palette={palette} />
    </Space>
  )
}
