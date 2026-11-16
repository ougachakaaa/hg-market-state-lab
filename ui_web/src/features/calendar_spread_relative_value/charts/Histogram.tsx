import Plot from 'react-plotly.js'
import { theme } from 'antd'
import type { Result } from '../api/validateResult'
import { literalText } from '../../../shared/visualization/figureV2'
export function Histogram({ distribution }: { distribution: Result['pairs'][number]['distributions'][number] }) {
  const { token } = theme.useToken()
  const h = distribution.histogram!.result
  return <div style={{ height: 300, width: '100%', minWidth: 0 }}><Plot
    data={[{ type: 'bar', x: h.bins.map(b => `[${b.left}, ${b.right}${b.right_inclusive ? ']' : ')'}`), y: h.bins.map(b => b.count),
      text: h.bins.map(b => `count=${b.count} · frequency=${b.frequency}`), hovertemplate: '%{x}<br>%{text}<extra></extra>' }]}
    layout={{ autosize: true, title: { text: literalText(`${distribution.stage} · ${h.unit}`) }, xaxis: { type: 'category' }, yaxis: { title: { text: 'Sample count' } }, paper_bgcolor: token.colorBgContainer, plot_bgcolor: token.colorBgContainer, font: { color: token.colorText }, margin: { t: 50, b: 70 } }}
    config={{ displaylogo: false, responsive: true }} useResizeHandler style={{ width: '100%', height: '100%' }} /></div>
}
