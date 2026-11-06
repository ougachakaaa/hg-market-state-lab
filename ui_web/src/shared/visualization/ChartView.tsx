import Plot from 'react-plotly.js'
import type { ChartView as ChartViewContract } from './contract'
import { chartViewToPlotly } from './figure'
import type { ViewV2, VisualizationView, Detail } from './contractV2'
import { validateVisualizationView } from './contractV2'
import { viewV2ToPlotly } from './figureV2'
import { Alert, Collapse, Flex, Typography } from 'antd'
import type { MouseEvent, TouchEvent } from 'react'

function DetailList({ details }: { details: Detail[] }) {
  return <>{details.map((detail, i) => <div key={i}>{detail.label}: {detail.value}</div>)}</>
}

function V2Chart({ view }: { view: ViewV2 }) {
  const figure = viewV2ToPlotly(view)
  const missing = view.layers.flatMap(b => b.layer.data.filter(m => m.y === null).map(m => ({ key: `${b.id}:${m.x}`, label: `${b.label} — ${m.x} — No value`, children: <DetailList details={m.details} /> })))
  const events = view.events.map(e => ({ key: e.id, label: `${e.id} — ${e.x} — ${e.label}`, children: <DetailList details={e.details} /> }))
  // Plotly's Shift/Ctrl shortcuts can switch drag modes even when their buttons
  // are absent. Block only shortcuts that would enable a disabled interaction.
  function guardDrag(event: MouseEvent<HTMLDivElement> | TouchEvent<HTMLDivElement>) {
    const p = view.presentation
    const plot = event.currentTarget.querySelector('.js-plotly-plot') as (HTMLElement & { _fullLayout?: { dragmode: string } }) | null
    const mode = plot?._fullLayout?.dragmode
    const shortcutPan = event.shiftKey ? mode !== 'pan' : event.ctrlKey
    const shortcutZoom = event.shiftKey && mode === 'pan'
    const target = event.target as Element
    const axisDrag = target.classList.contains('drag') && !target.classList.contains('nsewdrag')
    const axisScale = axisDrag && !target.classList.contains('ewdrag') && !target.classList.contains('nsdrag')
    if ((shortcutPan && !p.pan) || (shortcutZoom && !p.zoom) || (axisDrag && !p.pan) || (axisScale && !p.zoom)) {
      event.preventDefault(); event.stopPropagation()
    }
  }
  return <Flex vertical gap="small" style={{ height: '100%', width: '100%' }}>
    {!view.layers.some(b => b.layer.data.some(m => m.y !== null)) && <Alert title="No numeric data" type="info" />}
    <div onMouseDownCapture={guardDrag} onTouchStartCapture={guardDrag} style={{ flex: '1 0 320px', minHeight: 320 }}>
      <Plot {...figure} style={{ width: '100%', height: '100%' }} useResizeHandler />
    </div>
    {missing.length > 0 && <section aria-label="Missing values"><Typography.Title level={5}>Missing values</Typography.Title><Collapse items={missing} /></section>}
    {events.length > 0 && <section aria-label="Date events"><Typography.Title level={5}>Date events</Typography.Title><Collapse items={events} /></section>}
  </Flex>
}

/** Renders a complete inline View; validation errors are thrown to the caller. */
export function ChartView({ view }: { view: VisualizationView }) {
  validateVisualizationView(view)
  if (view.version === 2) return <V2Chart view={view} />
  return <V1Chart view={view} />
}

function V1Chart({ view }: { view: ChartViewContract }) {
  const figure = chartViewToPlotly(view)
  return <Plot {...figure} style={{ width: '100%', height: '100%' }} useResizeHandler />
}
