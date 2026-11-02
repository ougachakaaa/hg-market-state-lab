import type { ChartView, Layer } from './contract'

const category = { kind: 'category', unit: 'category' } as const
const number = { kind: 'number', unit: 'count' } as const
const line: Layer = { type: 'line', version: 1, x: category, y: number, data: [{ x: 'B', y: 3 }, { x: 'A', y: 1 }] }
const bar: Layer = { type: 'bar', version: 1, x: category, y: number, data: [{ x: 'B', y: 0 }, { x: 'A', y: 2 }] }
const point: Layer = { type: 'point', version: 1, x: category, y: number, data: [{ x: 'A', y: 2 }, { x: 'A', y: 2 }, { x: 'C', y: 4 }] }
function view(layers: Layer[]): ChartView {
  return { version: 1, axes: [{ id: 'horizontal', orientation: 'x', coordinate: category }, { id: 'vertical', orientation: 'y', coordinate: number }], layers: layers.map((layer, index) => ({ id: `series-${index + 1}`, layer, x_axis: 'horizontal', y_axis: 'vertical' })), layout: { title: 'Example' }, presentation: { show_legend: true } }
}
export const fixtures = { line: view([line]), bar: view([bar]), point: view([point]), mixed: view([line, point]), invalid: { ...view([line]), layers: [{ id: 'bad', layer: line, x_axis: 'missing', y_axis: 'vertical' }] } }
