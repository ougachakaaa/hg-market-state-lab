import { useCallback, useState } from 'react'
import type { PlotRelayoutEvent } from 'plotly.js'
import { ordinalTicks, type RenderOptions } from './presentation'
import Plot from 'react-plotly.js'
import type { ChartView as ChartViewContract } from './contract'
import { chartViewToPlotly } from './figure'
import type { ViewV2, VisualizationView, Detail } from './contractV2'
import { validateVisualizationView } from './contractV2'
import { viewV2ToPlotly } from './figureV2'
import { Alert, Collapse, Flex, Typography, theme } from 'antd'
import type { MouseEvent, TouchEvent } from 'react'

function DetailList({ details }: { details: Detail[] }) {
  return <>{details.map((detail, i) => <div key={i}>{detail.label}: {detail.value}</div>)}</>
}

function V2Chart({ view, minPlotHeight, options }: { view: ViewV2; minPlotHeight: number; options: RenderOptions }) {
  const { token } = theme.useToken()
  const [viewport, setViewport] = useState<{ domain: readonly string[] | undefined; range?: number[] }>({ domain: options.ordinalDates })
  // A coordinate-system change invalidates viewport labels, not the Plot instance.
  if (viewport.domain !== options.ordinalDates) setViewport({ domain: options.ordinalDates })
  const [resetRevision, setResetRevision] = useState(0)
  // Stable modebar callbacks avoid Plotly treating every render as a new config.
  const resetViewport = useCallback(() => {
    setViewport(current => ({ domain: current.domain }))
    setResetRevision(value => value + 1)
  }, [])
  const figure = viewV2ToPlotly(view, options, resetViewport)
  // Plotly's built-in reset caches the first coordinate system. Explicit revisions
  // reset to the current full-data ranges after an ordinal/calendar switch.
  for (const [key, axis] of Object.entries(figure.layout)) {
    if (/^[xy]axis\d*$/.test(key)) axis.uirevision = `${axis.uirevision ?? 'axis'}:reset-${resetRevision}`
  }
  if (options.ordinalDates && viewport.domain === options.ordinalDates && figure.layout.xaxis) {
    Object.assign(figure.layout.xaxis, ordinalTicks(options.ordinalDates, viewport.range))
  }
  function updateTicks(event: PlotRelayoutEvent) {
    if (!options.ordinalDates) return
    const range = event['xaxis.range'] ?? (event['xaxis.range[0]'] !== undefined ? [event['xaxis.range[0]'], event['xaxis.range[1]']] : undefined)
    if (!range && !event['xaxis.autorange']) return
    setViewport({ domain: options.ordinalDates, range: range?.map(Number) })
  }
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
    <div onMouseDownCapture={guardDrag} onTouchStartCapture={guardDrag} style={{ flex: `1 0 ${minPlotHeight}px`, minHeight: minPlotHeight }}>
      <Plot {...figure} onRelayout={updateTicks} layout={{ ...figure.layout, paper_bgcolor: token.colorBgContainer,
        plot_bgcolor: token.colorBgContainer, font: { color: token.colorText } }}
        style={{ width: '100%', height: '100%' }} useResizeHandler />
    </div>
    {missing.length > 0 && <section aria-label="Missing values"><Typography.Title level={5}>Missing values</Typography.Title><Collapse items={missing} /></section>}
    {events.length > 0 && <section aria-label="Date events"><Typography.Title level={5}>Date events</Typography.Title><Collapse items={events} /></section>}
  </Flex>
}

/** Renders a complete inline View; validation errors are thrown to the caller. */
export function ChartView({ view, minPlotHeight = 320, options = {} }: { view: VisualizationView; minPlotHeight?: number; options?: RenderOptions }) {
  validateVisualizationView(view)
  if (view.version === 2) return <V2Chart view={view} minPlotHeight={minPlotHeight} options={options} />
  return <V1Chart view={view} options={options} />
}

function V1Chart({ view, options }: { view: ChartViewContract; options: RenderOptions }) {
  const { token } = theme.useToken()
  const figure = chartViewToPlotly(view, options)
  return <Plot {...figure} layout={{ ...figure.layout, paper_bgcolor: token.colorBgContainer,
    plot_bgcolor: token.colorBgContainer, font: { color: token.colorText } }}
    style={{ width: '100%', height: '100%' }} useResizeHandler />
}
