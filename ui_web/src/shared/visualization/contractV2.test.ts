import authority from '../../../VISUALIZATION_V2.md?raw'
import { describe, expect, it } from 'vitest'
import { validateChartView, validateLayer } from './contract'
import { validateLineV2, validateViewV2, validateVisualizationView, validateVisualizationLayer } from './contractV2'
import type { ViewV2 } from './contractV2'
import { fixtures } from './fixtures'
import { extendedFixtureV2, fixtureV2 } from './fixturesV2'

const copy = () => structuredClone(fixtureV2)
describe('V2 strict contract', () => {
  it('keeps the acceptance fixture identical to authority', () => {
    expect(fixtureV2).toEqual(JSON.parse(authority.split('```json\n')[1].split('\n```')[0]))
  })
  it('accepts supplied order, empty/all-null content and independent ID namespaces without mutation', () => {
    const v = extendedFixtureV2(); const before = structuredClone(v)
    validateViewV2(v); expect(v).toEqual(before)
    v.layers[1].layer.data[0].segment_id = 'a1'; validateViewV2(v)
    v.layers[0].id = 'time'; v.events[0].id = 'time'; validateViewV2(v)
    v.layers.forEach(b => b.layer.data.forEach(m => { m.y = null })); validateViewV2(v)
    v.layers.forEach(b => { b.layer.data = [] }); validateViewV2(v)
    validateViewV2({ ...v, axes: [], layers: [], events: [] })
  })
  it('allows boundary and leap dates, ordered duplicate detail labels and empty text', () => {
    const v = copy(); const marks = v.layers[0].layer.data
    marks[0].x = '0001-01-01'; marks[1].x = '2000-02-29'; marks[3].x = '9999-12-31'
    marks[0].details = [{ label: 'Note', value: '' }, { label: 'Note', value: 'next' }]
    validateViewV2(v)
  })
  it.each<[string, (v: ViewV2) => void, RegExp]>([
    ['year zero', v => { v.layers[0].layer.data[0].x = '0000-01-01' }, /data\[0\].x/],
    ['invalid leap date', v => { v.events[0].x = '2025-02-29' }, /events\[0\].x/],
    ['noncanonical date', v => { v.layers[0].layer.data[0].x = '2026-1-02' }, /data\[0\].x/],
    ['timestamp', v => { v.events[0].x = '2026-01-05T00:00:00Z' }, /events\[0\].x/],
    ['duplicate null date', v => { v.layers[0].layer.data[2].x = '2026-01-05' }, /data\[2\].x/],
    ['decreasing date', v => { v.layers[0].layer.data.reverse() }, /data\[1\].x/],
    ['bad date unit', v => { (v.layers[0].layer.x.unit as string) = 'day' }, /layer.x.unit/],
    ['empty numeric unit', v => { v.layers[0].layer.y.unit = '' }, /layer.y.unit/],
    ['unit mismatch', v => { v.axes[1].coordinate.unit = 'other' }, /y_axis/],
    ['unknown axis', v => { v.layers[0].x_axis = 'missing' }, /x_axis/],
    ['wrong orientation', v => { v.layers[0].x_axis = 'value' }, /x_axis/],
    ['event axis', v => { v.events[0].x_axis = 'value' }, /events\[0\].x_axis/],
    ['duplicate axis', v => { v.axes.push(structuredClone(v.axes[1])) }, /axes\[2\].id/],
    ['second x axis', v => { v.axes.push({ ...v.axes[0], id: 'second' }) }, /axes\[2\]/],
    ['duplicate binding', v => { v.layers[1].id = 'a' }, /layers\[1\].id/],
    ['duplicate event', v => { v.events.push(structuredClone(v.events[0])) }, /events\[1\].id/],
    ['segment reuse', v => { v.layers[0].layer.data[3].segment_id = 'a1' }, /segment_id/],
    ['NaN', v => { v.layers[0].layer.data[0].y = NaN }, /data\[0\].y/],
    ['Infinity', v => { v.layers[0].layer.data[0].y = Infinity }, /data\[0\].y/],
    ['sparse marks', v => { v.layers[0].layer.data = new Array(1) }, /data\[0\]/],
    ['sparse axes', v => { v.axes = new Array(1) }, /axes\[0\]/],
    ['sparse details', v => { v.events[0].details = new Array(1) }, /details\[0\]/],
  ])('rejects %s with a field path', (_, mutate, path) => {
    const v = copy(); mutate(v); expect(() => validateViewV2(v)).toThrow(path)
  })
  it.each([
    ['view', (v: any) => v], ['axis', (v: any) => v.axes[0]], ['coordinate', (v: any) => v.axes[0].coordinate],
    ['binding', (v: any) => v.layers[0]], ['layer', (v: any) => v.layers[0].layer], ['mark', (v: any) => v.layers[0].layer.data[0]],
    ['detail', (v: any) => v.layers[0].layer.data[0].details[0]], ['event', (v: any) => v.events[0]],
    ['layout', (v: any) => v.layout], ['presentation', (v: any) => v.presentation],
  ])('rejects extra and missing fields in %s', (_, target) => {
    const v = copy(); target(v).extra = true; expect(() => validateViewV2(v)).toThrow(/expected exactly fields/)
    delete target(v).extra; delete target(v)[Object.keys(target(v))[0]]; expect(() => validateViewV2(v)).toThrow(/expected exactly fields/)
  })
  it.each([
    (v: any) => { v.layers[0].layer.data[0].y = true },
    (v: any) => { v.layers[0].layer.type = 'point' },
    (v: any) => { v.axes[1].coordinate.kind = 'date' },
    (v: any) => { v.layers[0].label = '' },
    (v: any) => { v.layers[0].layer.data[0].segment_id = '' },
    (v: any) => { v.events[0].details = null },
    (v: any) => { v.layers[0].layer.data[0].details[0].value = {} },
    (v: any) => { v.presentation.zoom = 1 },
  ])('rejects wrong values without coercion', mutate => { const v = copy(); mutate(v); expect(() => validateViewV2(v)).toThrow() })
})
describe('explicit version admission', () => {
  it('dispatches while keeping existing V1 validators V1-only', () => {
    validateVisualizationView(fixtures.line); validateVisualizationView(fixtureV2)
    validateVisualizationLayer(fixtures.line.layers[0].layer); validateVisualizationLayer(fixtureV2.layers[0].layer)
    expect(() => validateChartView(fixtureV2)).toThrow()
    expect(() => validateLayer(fixtureV2.layers[0].layer)).toThrow()
    expect(() => validateLineV2(fixtures.line.layers[0].layer)).toThrow()
    const v1 = structuredClone(fixtures.line) as any
    v1.layers[0].layer.data[0].details = []; expect(() => validateVisualizationView(v1)).toThrow()
    const v = copy() as any
    v.layers[0].layer.version = 1; expect(() => validateVisualizationView(v)).toThrow(/version/)
    v.version = 1; expect(() => validateVisualizationView(v)).toThrow()
    v.version = 3; expect(() => validateVisualizationView(v)).toThrow(/view.version/)
    expect(() => validateVisualizationLayer({ ...fixtureV2.layers[0].layer, version: 3 })).toThrow(/layer.version/)
  })
})
