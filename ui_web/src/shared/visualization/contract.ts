/** Runtime representation of the V1 contract in ui_web/VISUALIZATION.md. */
export type Coordinate = { kind: 'number' | 'date' | 'category'; unit: string }
export type Value = number | string
export type XYMark = { x: Value; y: Value }
type LayerBase = { version: 1; x: Coordinate; y: Coordinate }
export type Layer = LayerBase & (
  | { type: 'line' | 'bar' | 'point'; data: XYMark[] }
  | { type: 'segment'; data: { x1: Value; y1: Value; x2: Value; y2: Value }[] }
  | { type: 'candlestick'; data: { x: Value; open: number; high: number; low: number; close: number }[] }
  | { type: 'area'; data: { x: Value; y0: number; y1: number }[] }
)
export type Axis = { id: string; orientation: 'x' | 'y'; coordinate: Coordinate }
export type Binding = { id: string; layer: Layer; x_axis: string; y_axis: string }
export type ChartView = { version: 1; axes: Axis[]; layers: Binding[]; layout: { title: string }; presentation: { show_legend: boolean } }

export class VisualizationValidationError extends Error {
  constructor(message: string) { super(message); this.name = 'VisualizationValidationError' }
}
function fail(path: string, message: string): never { throw new VisualizationValidationError(`${path}: ${message}`) }
function object(value: unknown, fields: string[], path: string): Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return fail(path, 'expected object')
  const record = value as Record<string, unknown>
  const keys = Object.keys(record)
  if (keys.length !== fields.length || fields.some((field) => !Object.hasOwn(record, field))) return fail(path, `expected exactly fields ${fields.join(', ')}`)
  return record
}
function nonempty(value: unknown, path: string): asserts value is string {
  if (typeof value !== 'string' || value.length === 0) fail(path, 'expected nonempty string')
}
function coordinate(value: unknown, path: string): asserts value is Coordinate {
  const c = object(value, ['kind', 'unit'], path)
  if (c.kind !== 'number' && c.kind !== 'date' && c.kind !== 'category') fail(path, 'unknown coordinate kind')
  nonempty(c.unit, `${path}.unit`)
  if ((c.kind === 'date' && c.unit !== 'date') || (c.kind === 'category' && c.unit !== 'category')) fail(path, 'invalid coordinate unit')
}
function validDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const [year, month, day] = value.split('-').map(Number)
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  return month >= 1 && month <= 12 && day >= 1 && day <= days[month - 1]
}
function valueFor(value: unknown, c: Coordinate, path: string): void {
  if (c.kind === 'number') { if (typeof value !== 'number' || !Number.isFinite(value)) fail(path, 'expected finite number'); return }
  if (typeof value !== 'string' || value.length === 0) return fail(path, `expected ${c.kind} string`)
  if (c.kind === 'date' && !validDate(value)) fail(path, 'expected canonical calendar date')
}
const fields = {
  line: ['x', 'y'], bar: ['x', 'y'], point: ['x', 'y'],
  segment: ['x1', 'y1', 'x2', 'y2'], candlestick: ['x', 'open', 'high', 'low', 'close'], area: ['x', 'y0', 'y1'],
} as const
export function validateLayer(input: unknown, path = 'layer'): asserts input is Layer {
  const layer = object(input, ['type', 'version', 'x', 'y', 'data'], path)
  if (layer.version !== 1) fail(`${path}.version`, 'unsupported version')
  if (typeof layer.type !== 'string' || !Object.hasOwn(fields, layer.type)) fail(`${path}.type`, 'unknown layer type')
  coordinate(layer.x, `${path}.x`); coordinate(layer.y, `${path}.y`)
  if (!Array.isArray(layer.data)) return fail(`${path}.data`, 'expected array')
  const type = layer.type as keyof typeof fields
  if ((type === 'area' || type === 'candlestick' || (type === 'bar' && layer.x.kind === 'category')) && layer.y.kind !== 'number') fail(`${path}.y`, 'expected numeric coordinate')
  const categories = new Set<unknown>()
  Array.from(layer.data).forEach((raw, index) => {
    const markPath = `${path}.data[${index}]`
    const mark = object(raw, [...fields[type]], markPath)
    for (const key of fields[type]) valueFor(mark[key], key.startsWith('x') ? layer.x as Coordinate : layer.y as Coordinate, `${markPath}.${key}`)
    if (type === 'bar' && (layer.x as Coordinate).kind === 'category') {
      if (categories.has(mark.x)) fail(`${markPath}.x`, 'duplicate bar category')
      categories.add(mark.x)
    }
    if (type === 'candlestick' && !((mark.low as number) <= (mark.open as number) && (mark.open as number) <= (mark.high as number) && (mark.low as number) <= (mark.close as number) && (mark.close as number) <= (mark.high as number))) fail(markPath, 'invalid candlestick range')
  })
}
export function validateChartView(input: unknown): asserts input is ChartView {
  const view = object(input, ['version', 'axes', 'layers', 'layout', 'presentation'], 'view')
  if (view.version !== 1) fail('view.version', 'unsupported version')
  const layout = object(view.layout, ['title'], 'view.layout')
  if (typeof layout.title !== 'string') fail('view.layout.title', 'expected string')
  const presentation = object(view.presentation, ['show_legend'], 'view.presentation')
  if (typeof presentation.show_legend !== 'boolean') fail('view.presentation.show_legend', 'expected boolean')
  if (!Array.isArray(view.axes)) return fail('view.axes', 'expected array')
  if (!Array.isArray(view.layers)) return fail('view.layers', 'expected array')
  const axes = new Map<string, Axis>()
  Array.from(view.axes).forEach((raw, index) => {
    const path = `view.axes[${index}]`; const axis = object(raw, ['id', 'orientation', 'coordinate'], path)
    nonempty(axis.id, `${path}.id`); coordinate(axis.coordinate, `${path}.coordinate`)
    if (axis.orientation !== 'x' && axis.orientation !== 'y') fail(`${path}.orientation`, 'expected x or y')
    if (axes.has(axis.id)) fail(`${path}.id`, 'duplicate axis id')
    axes.set(axis.id, axis as Axis)
  })
  const ids = new Set<string>()
  Array.from(view.layers).forEach((raw, index) => {
    const path = `view.layers[${index}]`; const binding = object(raw, ['id', 'layer', 'x_axis', 'y_axis'], path)
    nonempty(binding.id, `${path}.id`)
    if (ids.has(binding.id)) fail(`${path}.id`, 'duplicate binding id'); ids.add(binding.id)
    validateLayer(binding.layer, `${path}.layer`)
    for (const direction of ['x', 'y'] as const) {
      const id = binding[`${direction}_axis`]; nonempty(id, `${path}.${direction}_axis`)
      const axis = axes.get(id); if (!axis) return fail(`${path}.${direction}_axis`, 'unknown axis')
      if (axis.orientation !== direction) fail(`${path}.${direction}_axis`, 'wrong axis orientation')
      const c = binding.layer[direction]
      if (axis.coordinate.kind !== c.kind || axis.coordinate.unit !== c.unit) fail(`${path}.${direction}_axis`, 'coordinate kind or unit mismatch')
    }
  })
}
