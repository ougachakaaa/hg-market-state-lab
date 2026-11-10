import { formatUnit } from '../format/unit'
import type { RenderOptions } from './presentation'
import { literalText } from './figureV2'
import type { Config, Data, Layout } from 'plotly.js'
import { validateChartView } from './contract'
import type { Axis, ChartView, Layer } from './contract'
import { validateVisualizationView } from './contractV2'
import { viewV2ToPlotly } from './figureV2'

export class UnsupportedLayerError extends Error {
  constructor(message: string) { super(message); this.name = 'UnsupportedLayerError' }
}
function coordinateFields(layer: Layer, direction: 'x' | 'y'): string[] {
  if (layer.type === 'segment') return direction === 'x' ? ['x1', 'x2'] : ['y1', 'y2']
  if (layer.type === 'candlestick') return direction === 'x' ? ['x'] : ['open', 'high', 'low', 'close']
  if (layer.type === 'area') return direction === 'x' ? ['x'] : ['y0', 'y1']
  return [direction]
}
function categories(view: ChartView, axis: Axis): string[] {
  const seen = new Set<string>()
  for (const binding of view.layers) {
    if (binding[`${axis.orientation}_axis`] !== axis.id) continue
    const fields = coordinateFields(binding.layer, axis.orientation)
    for (const mark of binding.layer.data) for (const field of fields) seen.add((mark as unknown as Record<string, string>)[field])
  }
  return [...seen]
}
/** Validates first, then deterministically projects to an internal Plotly figure. */
export function chartViewToPlotly(input: unknown, options: RenderOptions = {}): { data: Data[]; layout: Partial<Layout>; config?: Partial<Config> } {
  validateVisualizationView(input)
  if (input.version === 2) return viewV2ToPlotly(input, options)
  validateChartView(input)
  const view = input
  const ids = new Map<string, string>()
  const layout: Record<string, unknown> = { title: { text: view.layout.title }, showlegend: view.presentation.show_legend, autosize: true, barmode: 'overlay' }
  const counts = { x: 0, y: 0 }
  for (const axis of view.axes) {
    const direction = axis.orientation; const n = ++counts[direction]; const suffix = n === 1 ? '' : String(n)
    ids.set(axis.id, `${direction}${suffix}`)
    const config: Record<string, unknown> = { type: axis.coordinate.kind === 'number' ? 'linear' : axis.coordinate.kind }
    if (axis.coordinate.kind === 'category') { config.categoryorder = 'array'; config.categoryarray = categories(view, axis) }
    if (axis.coordinate.kind === 'number' && axis.coordinate.unit === 'decimal_ratio') Object.assign(config, { tickformat: '.1%', hoverformat: '.1%' })
    const labels = options.categoryLabels?.[axis.id]
    if (labels && axis.coordinate.kind === 'category') Object.assign(config, { tickmode: 'array', tickvals: categories(view, axis), ticktext: categories(view, axis).map(c => literalText(labels.get(c) ?? c)) })
    if (n > 1) { config.overlaying = direction; config.side = direction === 'x' ? 'top' : 'right' }
    layout[`${direction}axis${suffix}`] = config
  }
  const data: Data[] = view.layers.map(({ id, layer, x_axis, y_axis }) => {
    if (layer.type !== 'line' && layer.type !== 'bar' && layer.type !== 'point') throw new UnsupportedLayerError(`binding ${id}: renderer for ${layer.type} is not supported`)
    if (layer.type === 'bar' && layer.x.kind !== 'category') throw new UnsupportedLayerError(`binding ${id}: only categorical bar rendering is supported`)
    const display = (value: string | number, direction: 'x' | 'y') => typeof value === 'number' ? formatUnit(value, layer[direction].unit) : options.categoryLabels?.[direction === 'x' ? x_axis : y_axis]?.get(value) ?? value
    const common = { text: layer.data.map(m => `${literalText(String(display(m.x, 'x')))}<br>${literalText(String(display(m.y, 'y')))}`), hovertemplate: '%{text}<extra></extra>', name: id, xaxis: ids.get(x_axis), yaxis: ids.get(y_axis), x: layer.data.map((m) => m.x), y: layer.data.map((m) => m.y) }
    return (layer.type === 'bar' ? { ...common, type: 'bar' } : { ...common, type: 'scatter', mode: layer.type === 'line' ? 'lines' : 'markers', connectgaps: false }) as Data
  })
  return { data, layout: layout as Partial<Layout> }
}
