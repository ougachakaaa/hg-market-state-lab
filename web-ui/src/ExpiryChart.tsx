import {
  CartesianGrid,
  Legend,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TooltipContentProps } from 'recharts'
import type { ExpiryGroup, OptionChain } from './api/moOptionChain'
import { projectExpiry } from './expiryChartData'
import type { ChartPoint } from './expiryChartData'

function PointTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload as ChartPoint
  return (
    <div className="chart-tooltip">
      <strong>{point.instrument_id}</strong>
      <span>{point.side} · Strike {point.strike} · Price {point.price}</span>
    </div>
  )
}

export default function ExpiryChart({ group, underlying }: {
  group: ExpiryGroup
  underlying: OptionChain['underlying']
}) {
  const chart = projectExpiry(group, underlying.price)
  const hasDrawablePrice = chart.calls.length + chart.puts.length > 0

  return (
    <section className="expiry-chart" aria-label={`${group.expiry_date} 散点图`}>
      <h4>价格分布</h4>
      <p className="chart-reference">标的参考线：{underlying.instrument_id} · {underlying.price}</p>
      {chart.missingPriceCount > 0 && (
        <p className="missing-price">{chart.missingPriceCount} 个合约缺少所选价格，未绘制为散点；可在合约明细中查看。</p>
      )}
      {hasDrawablePrice ? (
        <div className="chart-frame" role="group" aria-label={`${group.expiry_date} Call 与 Put 价格散点图；横轴 Strike，纵轴 Price；参考价 ${underlying.price}`}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 22, right: 24, bottom: 26, left: 12 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="strike" domain={chart.xDomain} allowDataOverflow name="Strike" label={{ value: 'Strike', position: 'insideBottom', offset: -16 }} />
              <YAxis type="number" dataKey="price" domain={chart.yDomain} allowDataOverflow name="Price" label={{ value: 'Price', angle: -90, position: 'insideLeft' }} />
              <Tooltip content={PointTooltip} />
              <Legend verticalAlign="top" />
              <ReferenceLine x={underlying.price} stroke="#64748b" strokeDasharray="5 4" label={{ value: underlying.instrument_id, position: 'insideTopRight', fill: '#475569' }} />
              <Scatter name="Calls" data={chart.calls} fill="#2563eb" />
              <Scatter name="Puts" data={chart.puts} fill="#ea580c" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="chart-empty">该到期日没有可绘制的价格。</p>
      )}
    </section>
  )
}
