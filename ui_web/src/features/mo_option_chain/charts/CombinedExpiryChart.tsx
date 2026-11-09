import { Card, Empty, Typography, theme } from 'antd'
import Plot from 'react-plotly.js'
import type { OptionChain } from '../api/moOptionChain'
import { projectCombinedChain } from '../model/combinedChartData'
import { formatPrice } from '../model/priceDisplay'
import { buildCombinedPlot } from './combinedPlot'
import type { ExpiryColors } from './expiryPalette'

type Projection = ReturnType<typeof projectCombinedChain>

function SeriesSymbol({ side, color }: { side: 'Call' | 'Put' | 'Futures'; color: string }) {
  return (
    <span className={`chart-legend-symbol chart-legend-symbol-${side.toLowerCase()}`} style={{ color }} aria-hidden="true">
      <span className="chart-legend-line" />
      {side !== 'Futures' && <span className="chart-legend-marker" />}
    </span>
  )
}

function ChartLegends({ projection, palette }: {
  projection: Projection
  palette: Record<string, ExpiryColors>
}) {
  const optionSeries = projection.groups.flatMap((group) => (
    ([['Call', group.calls], ['Put', group.puts]] as const)
      .filter(([, points]) => points.some((point) => point.price !== null))
      .map(([side]) => ({ expiryDate: group.expiry_date, side }))
  ))
  const futuresGroups = projection.groups.filter((group) => group.futures !== null)

  return (
    <div className="chart-legends" aria-label="图表图例">
      <section className="chart-legend chart-option-legend" aria-label="Call 与 Put 图例">
        <h4>Call / Put</h4>
        <ul className="chart-legend-items">
          {optionSeries.map(({ expiryDate, side }) => (
            <li key={`${expiryDate}-${side}`}>
              <SeriesSymbol side={side} color={side === 'Call' ? palette[expiryDate].call : palette[expiryDate].put} />
              <span>{expiryDate} {side}</span>
            </li>
          ))}
        </ul>
      </section>
      {futuresGroups.length > 0 && (
        <section className="chart-legend chart-futures-legend" aria-label="Futures 图例">
          <h4>Futures</h4>
          <ul className="chart-legend-items">
            {futuresGroups.map((group) => (
              <li key={group.expiry_date}>
                <SeriesSymbol side="Futures" color={palette[group.expiry_date].futures} />
                <span>{group.futures!.instrument_id} · {formatPrice(group.futures!.price)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

export default function CombinedExpiryChart({ chain, selectedExpiries, xDomain, palette }: {
  chain: OptionChain
  selectedExpiries: ReadonlySet<string>
  xDomain: [number, number]
  palette: Record<string, ExpiryColors>
}) {
  const { token } = theme.useToken()
  const projection = projectCombinedChain(chain, selectedExpiries, xDomain)
  const figure = buildCombinedPlot(chain, projection, xDomain, palette)
  return (
    <Card size="small" role="region" aria-label="合并到期日分析图" title="价格分布">
      <Typography.Paragraph className="spot-reference">
        Spot：{chain.underlying.instrument_id} · {formatPrice(chain.underlying.price)}
      </Typography.Paragraph>
      {!projection.hasDrawablePrice && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选中的到期日没有可绘制的价格。" />}
      <ChartLegends projection={projection} palette={palette} />
      <div className="chart-frame" role="group" aria-label="所选到期日 Call 与 Put 价格散点图；横轴 Strike，纵轴 Price">
        <Plot {...figure} layout={{ ...figure.layout, paper_bgcolor: token.colorBgContainer,
          plot_bgcolor: token.colorBgContainer, font: { color: token.colorText } }}
          style={{ width: '100%', height: '100%' }} useResizeHandler />
      </div>
    </Card>
  )
}
