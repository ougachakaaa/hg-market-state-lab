import Plot from 'react-plotly.js'
import { theme } from 'antd'
import type { Result } from '../api/validateResult'
import { literalText } from '../../../shared/visualization/figureV2'
import { formatUnit } from '../../../shared/format/unit'
import { formatPercent } from '../../../shared/format/number'
export function Histogram({ distribution }: { distribution: Result['pairs'][number]['distributions'][number] }) {
  const { token } = theme.useToken()
  const h = distribution.histogram!.result
  // Raw edge strings stay the category identity; only ticktext/hovertemplate are rounded.
  const identities = h.bins.map(b => `[${b.left}, ${b.right}${b.right_inclusive ? ']' : ')'}`)
  const labels = h.bins.map(b => `[${formatUnit(b.left, h.unit)}, ${formatUnit(b.right, h.unit)}${b.right_inclusive ? ']' : ')'}`)
  return <div style={{ height: 300, width: '100%', minWidth: 0 }}><Plot
    data={[{ type: 'bar', x: identities, y: h.bins.map(b => b.count),
      text: h.bins.map((b, i) => `${labels[i]}<br>count=${b.count} · frequency=${formatPercent(b.frequency)}`), hovertemplate: '%{text}<extra></extra>' }]}
    layout={{ autosize: true, title: { text: literalText(`${distribution.stage} · ${h.unit}`) }, xaxis: { type: 'category', tickmode: 'array', tickvals: identities, ticktext: labels.map(literalText) }, yaxis: { title: { text: 'Sample count' }, tickformat: 'd' }, paper_bgcolor: token.colorBgContainer, plot_bgcolor: token.colorBgContainer, font: { color: token.colorText }, margin: { t: 50, b: 70 } }}
    config={{ displaylogo: false, responsive: true }} useResizeHandler style={{ width: '100%', height: '100%' }} /></div>
}
