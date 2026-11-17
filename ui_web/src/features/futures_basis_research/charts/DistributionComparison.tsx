import { useEffect, useRef, useState } from 'react'
import { distributionTraces } from './distributionFigure'
import Plot from 'react-plotly.js'
import { Alert, Flex, theme } from 'antd'
import { BIN_PRESETS, type BasisMetric, type HistogramProjection } from '../model/histogramAggregation'
import { plotlyAxisFormat } from '../../../shared/visualization/presentation'

export function DistributionComparison({ projection, metric, width, tail = 0 }: { projection: HistogramProjection; metric: BasisMetric; width: number; tail?: number }) {
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
  const axisTitle = { basis_value: '基差（点）', basis_ratio: '基差率（%）', annualized_basis_ratio: '年化基差率（%）', annualized_basis_value: '年化基差点（点/年）' }[metric]
  return <Flex vertical gap="small" data-testid="distribution-comparison" style={{ minWidth: 0 }}>
    {projection.slots.filter(s => !s.n).map(s => <Alert key={s.slot} type="info" title={`${s.slot}：无有效样本（Eligible N=0）`} />)}
    <div ref={frame} style={{ width: '100%', minWidth: 0, height: 380, overflow: 'hidden' }}>
      <Plot data={distributionTraces(projection, metric, width)} layout={{
        autosize: true, width: plotWidth, title: { text: 'Distribution Comparison' },
        paper_bgcolor: token.colorBgContainer, plot_bgcolor: token.colorBgContainer, font: { color: token.colorText },
        margin: { l: 60, r: 20, t: 70, b: 65 }, showlegend: true,
        legend: { orientation: 'h', y: 1.12, uirevision: 'slots', itemdoubleclick: false },
        xaxis: { title: { text: axisTitle }, ...plotlyAxisFormat(BIN_PRESETS[metric].unit), ...(metric === 'basis_ratio' && width === .05 ? { tickformat: '.2%', hoverformat: '.2%' } : {}), uirevision: `${metric}/${width}/${tail}` },
        yaxis: { title: { text: 'Frequency（%）' }, ...plotlyAxisFormat('decimal_ratio'), rangemode: 'tozero', uirevision: `${metric}/${width}/${tail}` },
        hovermode: 'closest', dragmode: 'zoom',
      }} config={{ displaylogo: false, responsive: true, scrollZoom: true, modeBarButtons: [['zoom2d', 'pan2d', 'resetScale2d']] }}
        style={{ width: '100%', height: '100%' }} useResizeHandler />
    </div>
  </Flex>
}
