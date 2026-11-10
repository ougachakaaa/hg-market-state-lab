import { formatUnit } from '../format/unit'
import { ordinalTicks, type RenderOptions } from './presentation'
import type { Config, Data, Layout } from 'plotly.js'
import type { DateMark, ViewV2 } from './contractV2'

/** Plotly supports a subset of HTML even in labels and hover text. */
export function literalText(text: string): string {
  return text.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;')
}
const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
function paddedRange(values: number[], fallback: [number, number], singletonPadding?: number): [number, number] {
  if (!values.length) return fallback
  let min = values[0]; let max = min
  for (const value of values) { min = Math.min(min, value); max = Math.max(max, value) }
  const padding = (max - min) * 0.06 || singletonPadding || Math.abs(min) * 0.06 || 1
  // Valid finite extremes must not introduce nonfinite Plotly ranges.
  return [Number.isFinite(min - padding) ? min - padding : min, Number.isFinite(max + padding) ? max + padding : max]
}
function tooltip(label: string, mark: DateMark, unit: string, options: RenderOptions): string {
  return [label, mark.x, mark.y === null ? 'No value' : unit === 'decimal_ratio' ? formatUnit(mark.y, unit) : `${formatUnit(mark.y, unit)} ${unit}`, ...(options.pointDetails?.(mark, unit) ?? mark.details).map(d => `${d.label}: ${d.value}`)].map(literalText).join('<br>')
}

/** Internal projection only; its caller validates the complete View first. */
export function viewV2ToPlotly(view: ViewV2, options: RenderOptions = {}, resetViewport?: () => void): { data: Data[]; layout: Partial<Layout>; config: Partial<Config> } {
  const p = view.presentation
  const domain = options.ordinalDates
  if (domain?.some((d, i) => i > 0 && d <= domain[i - 1])) throw new Error('Ordinal dates must be strictly increasing')
  const positions = new Map(domain?.map((date, i) => [date, i]))
  function position(date: string): string | number {
    if (!domain) return date
    const index = positions.get(date)
    if (index === undefined) throw new Error(`Date ${date} is absent from ordinal domain`)
    return index
  }
  const ordinalRange = paddedRange(domain?.length ? [0, domain.length - 1] : [], [-1, 1], 1)
  const ids = new Map<string, string>(); let yCount = 0
  const layout: Record<string, unknown> = {
    title: { text: literalText(view.layout.title) }, autosize: true,
    showlegend: p.show_legend, legend: { groupclick: 'togglegroup', uirevision: 'legend' },
    // Date hover keeps coincident points in different Bindings inspectable.
    hovermode: 'x', dragmode: p.zoom ? 'zoom' : p.pan ? 'pan' : false,
    margin: { t: 100, b: 60 },
  }
  const dated = [...view.layers.flatMap(b => b.layer.data.map(m => m.x)), ...view.events.map(e => e.x)]
  const dates = dated.map(d => Date.parse(`${d}T00:00:00Z`))
  const dateRange = paddedRange(dates, [Date.UTC(2000, 0, 1), Date.UTC(2000, 0, 2)], 86400000)
    // Plotly treats numeric date ranges as legacy *local-time* milliseconds.
    // Explicit date strings keep the viewport stable across browser timezones.
    .map(ms => new Date(Math.max(Date.parse('0001-01-01T00:00:00Z'), Math.min(Date.parse('9999-12-31T23:59:59.999Z'), ms))).toISOString().slice(0, -1))
  for (const axis of view.axes) {
    const x = axis.orientation === 'x'
    const n = x ? 1 : ++yCount; const suffix = n === 1 ? '' : String(n)
    ids.set(axis.id, `${axis.orientation}${suffix}`)
    const values = x ? [] : view.layers.filter(b => b.y_axis === axis.id).flatMap(b => b.layer.data.flatMap(m => m.y === null ? [] : [m.y]))
    const config: Record<string, unknown> = {
      type: x && !domain ? 'date' : 'linear', title: { text: literalText(axis.coordinate.unit) },
      range: x ? (domain ? ordinalRange : dateRange) : paddedRange(values, [0, 1]), autorange: false,
      fixedrange: !p.zoom && !p.pan,
    }
    if (x) Object.assign(config, { uirevision: domain ? `ordinal:${domain.join(',')}` : 'calendar', ...(domain ? { ...ordinalTicks(domain), hoverformat: 'd', labelalias: Object.fromEntries(domain.map((date, index) => [String(index), date])) } : { nticks: 8 }) })
    if (!x && axis.coordinate.unit === 'decimal_ratio') Object.assign(config, { tickformat: '.1%', hoverformat: '.1%', title: { text: '%' } })
    if (options.axisGrid?.[axis.id]) Object.assign(config, { showgrid: true, ...options.axisGrid[axis.id] })
    if (!x && n > 1) Object.assign(config, { overlaying: 'y', anchor: 'free', side: 'right', autoshift: true })
    layout[`${axis.orientation}axis${suffix}`] = config
  }
  const data: Data[] = []
  view.layers.forEach((binding, bindingIndex) => {
    const segments: DateMark[][] = []
    for (const mark of binding.layer.data) {
      if (!segments.length || segments[segments.length - 1][0].segment_id !== mark.segment_id) segments.push([])
      segments[segments.length - 1].push(mark)
    }
    if (!segments.length) segments.push([])
    segments.forEach((marks, segmentIndex) => data.push({
      type: 'scatter', mode: 'lines+markers', connectgaps: false,
      name: literalText(binding.label), legendgroup: binding.id, showlegend: segmentIndex === 0,
      line: { color: colors[bindingIndex % colors.length] }, marker: { color: colors[bindingIndex % colors.length], size: 7 },
      xaxis: ids.get(binding.x_axis), yaxis: ids.get(binding.y_axis),
      // Plotly removes zero-length traces from the legend. A null-only internal
      // placeholder retains the empty Binding's entry without inventing a point.
      x: marks.length ? marks.map(m => position(m.x)) : [null], y: marks.length ? marks.map(m => m.y) : [null],
      text: marks.map(m => tooltip(binding.label, m, binding.layer.y.unit, options)), hovertemplate: '%{text}<extra></extra>',
    } as Data))
  })
  const sameDate = new Map<string, number>()
  layout.shapes = view.events.map(e => ({ type: 'line', xref: ids.get(e.x_axis), x0: position(e.x), x1: position(e.x), yref: 'paper', y0: 0, y1: 1, line: { color: '#666', width: 1, dash: 'dot' } }))
  layout.annotations = view.events.map(e => {
    const row = sameDate.get(e.x) ?? 0; sameDate.set(e.x, row + 1)
    return { xref: ids.get(e.x_axis), x: position(e.x), yref: 'paper', y: 1, yshift: 12 + row * 20, showarrow: false,
      text: literalText(e.label), hovertext: [e.id, e.x, e.label, ...e.details.map(d => `${d.label}: ${d.value}`)].map(literalText).join('<br>') }
  })
  const rows = Math.max(1, ...sameDate.values())
  layout.margin = { t: 80 + rows * 20, b: 60 }
  const buttons: (string | { name: string; icon: { width: number; height: number; path: string }; click: () => void })[] = []
  if (p.zoom) buttons.push('zoom2d')
  if (p.pan) buttons.push('pan2d')
  if (p.reset) buttons.push(resetViewport ? {
    name: 'Reset axes',
    icon: { width: 24, height: 24, path: 'M3 10L12 2L21 10V22H14V15H10V22H3Z' },
    click: resetViewport,
  } : 'resetScale2d')
  return { data, layout: layout as Partial<Layout>, config: {
    displayModeBar: buttons.length > 0, displaylogo: false,
    modeBarButtons: buttons.length ? [buttons] as Config['modeBarButtons'] : [],
    scrollZoom: p.zoom, doubleClick: false, showAxisDragHandles: p.pan, showAxisRangeEntryBoxes: false,
  } }
}
