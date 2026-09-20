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
import { formatPrice } from './priceDisplay'

function PointTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload as ChartPoint
  return (
    <div className="chart-tooltip">
      <strong>{point.instrument_id}</strong>
      <span>{point.side} · Strike {formatPrice(point.strike)} · Price {formatPrice(point.price)}</span>
    </div>
  )
}

export default function ExpiryChart({ group, underlying, xDomain }: {
  group: ExpiryGroup
  underlying: OptionChain['underlying']
  xDomain: [number, number]
}) {
  const chart = projectExpiry(group)
  const hasDrawablePrice = chart.calls.length + chart.puts.length > 0

  return (
    <section className="expiry-chart" aria-label={`${group.expiry_date} 散点图`}>
      <h4>价格分布</h4>
      <div className="chart-references">
        <p className="chart-reference spot-reference">Spot：{underlying.instrument_id} · {formatPrice(underlying.price)}</p>
        <p className="chart-reference futures-reference">Futures：{group.futures.instrument_id} · {formatPrice(group.futures.price)}</p>
      </div>
      {chart.missingPriceCount > 0 && (
        <p className="missing-price">{chart.missingPriceCount} 个合约缺少所选价格，未绘制为散点；可在合约明细中查看。</p>
      )}
      {hasDrawablePrice ? (
        <div className="chart-frame" role="group" aria-label={`${group.expiry_date} Call 与 Put 价格散点图；横轴 Strike，纵轴 Price；Spot ${underlying.instrument_id} ${formatPrice(underlying.price)}；Futures ${group.futures.instrument_id} ${formatPrice(group.futures.price)}`}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 22, right: 24, bottom: 26, left: 12 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="strike" domain={xDomain} allowDataOverflow tickFormatter={formatPrice} name="Strike" label={{ value: 'Strike', position: 'insideBottom', offset: -16 }} />
              <YAxis type="number" dataKey="price" domain={chart.yDomain} allowDataOverflow tickFormatter={formatPrice} name="Price" label={{ value: 'Price', angle: -90, position: 'insideLeft' }} />
              <Tooltip content={PointTooltip} />
              <Legend verticalAlign="top" />
              <ReferenceLine x={underlying.price} stroke="#64748b" strokeDasharray="5 4" label={{ value: `Spot ${formatPrice(underlying.price)}`, position: 'insideTopRight', fill: '#475569' }} />
              <ReferenceLine x={group.futures.price} stroke="#7c3aed" strokeDasharray="2 3" label={{ value: `IM ${formatPrice(group.futures.price)}`, position: 'insideBottomRight', fill: '#6d28d9' }} />
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
