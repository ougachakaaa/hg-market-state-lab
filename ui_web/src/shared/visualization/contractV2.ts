import { VisualizationValidationError, validateChartView, validateLayer } from './contract'
import type { ChartView, Layer } from './contract'

export type DateCoordinate = { kind: 'date'; unit: 'date' }
export type NumberCoordinate = { kind: 'number'; unit: string }
export type Detail = { label: string; value: string }
export type DateMark = { x: string; y: number | null; segment_id: string; details: Detail[] }
export type LineV2 = { type: 'line'; version: 2; x: DateCoordinate; y: NumberCoordinate; data: DateMark[] }
export type AxisV2 = { id: string; orientation: 'x' | 'y'; coordinate: DateCoordinate | NumberCoordinate }
export type BindingV2 = { id: string; label: string; layer: LineV2; x_axis: string; y_axis: string }
export type EventV2 = { id: string; x_axis: string; x: string; label: string; details: Detail[] }
export type PresentationV2 = { show_legend: boolean; zoom: boolean; pan: boolean; reset: boolean }
export type ViewV2 = { version: 2; axes: AxisV2[]; layers: BindingV2[]; events: EventV2[]; layout: { title: string }; presentation: PresentationV2 }
export type VisualizationView = ChartView | ViewV2
export type VisualizationLayer = Layer | LineV2

function fail(path: string, message: string): never { throw new VisualizationValidationError(`${path}: ${message}`) }
function object(value: unknown, fields: string[], path: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return fail(path, 'expected object')
  const record = value as Record<string, unknown>
  if (Object.keys(record).length !== fields.length || fields.some(field => !Object.hasOwn(record, field))) fail(path, `expected exactly fields ${fields.join(', ')}`)
  return record
}
function string(value: unknown, path: string, empty = false): asserts value is string {
  if (typeof value !== 'string' || (!empty && !value.length)) fail(path, empty ? 'expected string' : 'expected nonempty string')
}
function list(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) return fail(path, 'expected array')
  return Array.from(value) // Sparse entries must be validated, never silently skipped.
}
function date(value: unknown, path: string): asserts value is string {
  string(value, path)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) fail(path, 'expected canonical calendar date')
  const [y, m, d] = value.split('-').map(Number)
  const leap = y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0)
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  if (y < 1 || m < 1 || m > 12 || d < 1 || d > days[m - 1]) fail(path, 'expected calendar date in years 0001–9999')
}
function coordinate(value: unknown, kind: 'date' | 'number', path: string): void {
  const c = object(value, ['kind', 'unit'], path)
  if (c.kind !== kind) fail(`${path}.kind`, `expected ${kind}`)
  string(c.unit, `${path}.unit`)
  if (kind === 'date' && c.unit !== 'date') fail(`${path}.unit`, 'expected date')
}
function details(value: unknown, path: string): void {
  list(value, path).forEach((raw, i) => {
    const p = `${path}[${i}]`; const d = object(raw, ['label', 'value'], p)
    string(d.label, `${p}.label`); string(d.value, `${p}.value`, true)
  })
}
export function validateLineV2(input: unknown, path = 'layer'): asserts input is LineV2 {
  const layer = object(input, ['type', 'version', 'x', 'y', 'data'], path)
  if (layer.version !== 2) fail(`${path}.version`, 'expected version 2')
  if (layer.type !== 'line') fail(`${path}.type`, 'expected line')
  coordinate(layer.x, 'date', `${path}.x`); coordinate(layer.y, 'number', `${path}.y`)
  let previousDate = ''; let segment: unknown
  const seen = new Set<string>()
  list(layer.data, `${path}.data`).forEach((raw, i) => {
    const p = `${path}.data[${i}]`; const m = object(raw, ['x', 'y', 'segment_id', 'details'], p)
    date(m.x, `${p}.x`)
    if (m.x <= previousDate) fail(`${p}.x`, 'dates must be strictly increasing and unique')
    previousDate = m.x
    if (m.y !== null && (typeof m.y !== 'number' || !Number.isFinite(m.y))) fail(`${p}.y`, 'expected finite number or null')
    string(m.segment_id, `${p}.segment_id`)
    if (m.segment_id !== segment) {
      if (seen.has(m.segment_id)) fail(`${p}.segment_id`, 'noncontiguous segment reuse')
      seen.add(m.segment_id); segment = m.segment_id
    }
    details(m.details, `${p}.details`)
  })
}
export function validateViewV2(input: unknown): asserts input is ViewV2 {
  const view = object(input, ['version', 'axes', 'layers', 'events', 'layout', 'presentation'], 'view')
  if (view.version !== 2) fail('view.version', 'expected version 2')
  string(object(view.layout, ['title'], 'view.layout').title, 'view.layout.title', true)
  const controls = ['show_legend', 'zoom', 'pan', 'reset']
  const presentation = object(view.presentation, controls, 'view.presentation')
  controls.forEach(key => { if (typeof presentation[key] !== 'boolean') fail(`view.presentation.${key}`, 'expected boolean') })
  const axes = new Map<string, AxisV2>(); let xCount = 0
  list(view.axes, 'view.axes').forEach((raw, i) => {
    const p = `view.axes[${i}]`; const a = object(raw, ['id', 'orientation', 'coordinate'], p)
    string(a.id, `${p}.id`)
    if (axes.has(a.id)) fail(`${p}.id`, 'duplicate axis id')
    if (a.orientation !== 'x' && a.orientation !== 'y') fail(`${p}.orientation`, 'expected x or y')
    if (a.orientation === 'x' && ++xCount > 1) fail(p, 'at most one x axis')
    coordinate(a.coordinate, a.orientation === 'x' ? 'date' : 'number', `${p}.coordinate`)
    axes.set(a.id, a as AxisV2)
  })
  function reference(id: unknown, direction: 'x' | 'y', p: string): AxisV2 {
    string(id, p); const axis = axes.get(id)
    if (!axis) return fail(p, 'unknown axis')
    if (axis.orientation !== direction) fail(p, 'wrong axis orientation')
    return axis
  }
  const bindings = new Set<string>()
  list(view.layers, 'view.layers').forEach((raw, i) => {
    const p = `view.layers[${i}]`; const b = object(raw, ['id', 'label', 'layer', 'x_axis', 'y_axis'], p)
    string(b.id, `${p}.id`); string(b.label, `${p}.label`)
    if (bindings.has(b.id)) fail(`${p}.id`, 'duplicate binding id')
    bindings.add(b.id); validateLineV2(b.layer, `${p}.layer`)
    for (const direction of ['x', 'y'] as const) {
      const axis = reference(b[`${direction}_axis`], direction, `${p}.${direction}_axis`)
      if (axis.coordinate.kind !== b.layer[direction].kind || axis.coordinate.unit !== b.layer[direction].unit) fail(`${p}.${direction}_axis`, 'coordinate kind or unit mismatch')
    }
  })
  const events = new Set<string>()
  list(view.events, 'view.events').forEach((raw, i) => {
    const p = `view.events[${i}]`; const e = object(raw, ['id', 'x_axis', 'x', 'label', 'details'], p)
    string(e.id, `${p}.id`); string(e.label, `${p}.label`); date(e.x, `${p}.x`)
    if (events.has(e.id)) fail(`${p}.id`, 'duplicate event id')
    events.add(e.id); reference(e.x_axis, 'x', `${p}.x_axis`); details(e.details, `${p}.details`)
  })
}
function version(input: unknown, path: string): unknown {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return fail(path, 'expected object')
  return (input as Record<string, unknown>).version
}
export function validateVisualizationView(input: unknown): asserts input is VisualizationView {
  const v = version(input, 'view')
  if (v === 1) validateChartView(input)
  else if (v === 2) validateViewV2(input)
  else fail('view.version', 'unsupported version')
}
export function validateVisualizationLayer(input: unknown, path = 'layer'): asserts input is VisualizationLayer {
  const v = version(input, path)
  if (v === 1) validateLayer(input, path)
  else if (v === 2) validateLineV2(input, path)
  else fail(`${path}.version`, 'unsupported version')
}
