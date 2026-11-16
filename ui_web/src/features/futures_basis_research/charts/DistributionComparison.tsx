import { useEffect, useRef, useState } from 'react'
import { distributionTraces } from './distributionFigure'
import Plot from 'react-plotly.js'
import { Alert, Flex, theme } from 'antd'
import { BIN_PRESETS, type BasisMetric, type HistogramProjection } from '../model/histogramAggregation'

export function DistributionComparison({ projection, metric, width }: { projection: HistogramProjection; metric: BasisMetric; width: number }) {
  const { token } = theme.useToken()
  const frame = useRef<HTMLDivElement>(null)
  const [plotWidth, setPlotWidth] = useState<number>()
  useEffect(() => {
    const node = frame.current
    if (!node) return
    const resize = (width: number) => { if (width > 0) setPlotWidth(width) }
    resize(node.clientWidth)
    const observer = new ResizeObserver(([entry]) => resize(entry.contentRect.width))
    observer.observe(node)
    return () => observer.disconnect()
  }, [projection.status])
  if (projection.status !== 'ready') return <Alert role="status" type={projection.status === 'inconsistent' ? 'error' : 'info'} title={projection.message} />
  const ratio = BIN_PRESETS[metric].unit === 'decimal_ratio'
  return <Flex vertical gap="small" data-testid="distribution-comparison" style={{ minWidth: 0 }}>
    {projection.slots.filter(s => !s.n).map(s => <Alert key={s.slot} type="info" title={`${s.slot}：无有效样本（Eligible N=0）`} />)}
    <div ref={frame} style={{ width: '100%', minWidth: 0, height: 380, overflow: 'hidden' }}>
      <Plot data={distributionTraces(projection, metric, width)} layout={{
        autosize: true, width: plotWidth, title: { text: 'Distribution Comparison' },
        paper_bgcolor: token.colorBgContainer, plot_bgcolor: token.colorBgContainer, font: { color: token.colorText },
        margin: { l: 60, r: 20, t: 70, b: 65 }, showlegend: true,
        legend: { orientation: 'h', y: 1.12, uirevision: 'slots', itemdoubleclick: false },
        xaxis: { title: { text: ratio ? '%' : '基差（点）' }, tickformat: ratio ? (width === .05 ? '.2%' : '.1%') : undefined, uirevision: `${metric}/${width}` },
        yaxis: { title: { text: 'Frequency（%）' }, tickformat: '.1%', rangemode: 'tozero', uirevision: `${metric}/${width}` },
        hovermode: 'closest', dragmode: 'zoom',
      }} config={{ displaylogo: false, responsive: true, scrollZoom: true, modeBarButtons: [['zoom2d', 'pan2d', 'resetScale2d']] }}
        style={{ width: '100%', height: '100%' }} useResizeHandler />
    </div>
  </Flex>
}
