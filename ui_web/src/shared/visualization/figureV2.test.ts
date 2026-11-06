import { describe, expect, it } from 'vitest'
import { chartViewToPlotly } from './figure'
import { extendedFixtureV2, fixtureV2 } from './fixturesV2'

const figure = (v = fixtureV2) => chartViewToPlotly(v) as any
describe('V2 deterministic projection', () => {
  it('projects the fixed fixture without mutation and keeps precisely two logical legends', () => {
    const v = structuredClone(fixtureV2); const before = structuredClone(v)
    const f = figure(v); expect(f).toEqual(figure(v)); expect(v).toEqual(before)
    const a = f.data.filter((t: any) => t.legendgroup === 'a'); const b = f.data.filter((t: any) => t.legendgroup === 'b')
    expect(a.map((t: any) => t.x)).toEqual([['2026-01-02'], ['2026-01-05', '2026-01-06'], ['2026-01-07']])
    expect(a.map((t: any) => t.y)).toEqual([[1], [2, null], [3]])
    expect(b[0].x).toEqual(['2026-01-02', '2026-01-05']); expect(b[0].y).toEqual([4, 5])
    expect(f.data.filter((t: any) => t.showlegend).map((t: any) => t.name)).toEqual(['Series A', 'Series B'])
    expect(new Set(a.map((t: any) => t.line.color)).size).toBe(1)
    expect(f.layout.legend.groupclick).toBe('togglegroup')
    expect(f.layout.hovermode).toBe('x')
    expect(f.data.every((t: any) => t.mode === 'lines+markers' && t.connectgaps === false)).toBe(true)
  })
  it('preserves same-segment null gaps and isolates segment IDs by binding', () => {
    const v = structuredClone(fixtureV2)
    v.layers[0].layer.data[3].segment_id = 'a2'; v.layers[1].layer.data.forEach(m => { m.segment_id = 'a2' })
    const f = figure(v); expect(f.data[1].y).toEqual([2, null, 3]); expect(f.data[2].legendgroup).toBe('b')
  })
  it('escapes all custom Plotly text and retains detail ordering', () => {
    const v = structuredClone(fixtureV2)
    v.layers[0].label = '<b>A</b>'
    v.layers[0].layer.data[0].details.push({ label: 'Note', value: '& second' })
    v.layout.title = '<b>title</b>'
    const f = figure(v)
    expect(f.data[0].text[0]).toBe('&lt;b&gt;A&lt;/b&gt;<br>2026-01-02<br>1 count<br>Note: &lt;b&gt;literal text&lt;/b&gt;<br>Note: &amp; second')
    expect(f.data[0].hovertemplate).toBe('%{text}<extra></extra>')
    expect(f.layout.title.text).toBe('&lt;b&gt;title&lt;/b&gt;')
  })
  it('projects same-date and event-only dates in supplied order without touching marks', () => {
    const v = extendedFixtureV2(); const f = figure(v)
    expect(f.layout.shapes.map((s: any) => [s.xref, s.x0, s.x1, s.yref, s.y0, s.y1])).toEqual(v.events.map(e => ['x', e.x, e.x, 'paper', 0, 1]))
    expect(f.layout.annotations.map((a: any) => a.text)).toEqual(v.events.map(e => e.label))
    expect(f.layout.annotations[1].yshift).toBeGreaterThan(f.layout.annotations[0].yshift)
    expect(f.layout.annotations[1].hovertext).toContain('&lt;b&gt;literal event&lt;/b&gt;')
    expect(Date.parse(f.layout.xaxis.range[1])).toBeGreaterThan(Date.parse('2026-01-12'))
    expect(f.data).toEqual(figure().data)
  })
  it('keeps distinct unit axes unfixed when browsing is enabled', () => {
    const v = structuredClone(fixtureV2)
    v.axes.push({ id: 'other', orientation: 'y', coordinate: { kind: 'number', unit: 'distance' } })
    v.layers[1].y_axis = 'other'; v.layers[1].layer.y.unit = 'distance'
    const f = figure(v)
    expect(f.data[3].yaxis).toBe('y2'); expect(f.layout.yaxis2).toMatchObject({ type: 'linear', overlaying: 'y', anchor: 'free', autoshift: true, fixedrange: false, title: { text: 'distance' } })
    expect(f.layout.yaxis.title.text).toBe('count')
  })
  it.each([true, false])('show_legend=%s applies to the view', show => {
    const v = structuredClone(fixtureV2); v.presentation.show_legend = show
    expect(figure(v).layout.showlegend).toBe(show)
  })
  it.each([
    [true, false, false, 'zoom', ['zoom2d']],
    [false, true, false, 'pan', ['pan2d']],
    [false, false, true, false, ['resetScale2d']],
    [false, false, false, false, []],
    [true, true, true, 'zoom', ['zoom2d', 'pan2d', 'resetScale2d']],
  ])('configures zoom=%s pan=%s reset=%s', (zoom, pan, reset, dragmode, buttons) => {
    const v = structuredClone(fixtureV2); Object.assign(v.presentation, { zoom, pan, reset })
    const f = figure(v)
    expect(f.layout.dragmode).toBe(dragmode); expect(f.config.scrollZoom).toBe(zoom)
    expect(f.config.modeBarButtons.flat()).toEqual(buttons); expect(f.config.doubleClick).toBe(false)
    expect(f.config.showAxisDragHandles).toBe(pan); expect(f.config.showAxisRangeEntryBoxes).toBe(false)
    expect(f.layout.yaxis.fixedrange).toBe(!zoom && !pan)
  })
  it('retains empty/all-null series without numeric markers', () => {
    const v = structuredClone(fixtureV2)
    v.layers[0].layer.data = []; v.layers[1].layer.data.forEach(m => { m.y = null })
    const f = figure(v)
    expect(f.data).toHaveLength(2); expect(f.data.every((t: any) => t.y.every((y: any) => y === null))).toBe(true)
    expect(f.layout.yaxis.range).toEqual([0, 1])
    expect(figure({ ...v, axes: [], layers: [], events: [] }).data).toEqual([])
  })
  it('fits a single event within a day of visual padding, using timezone-independent date strings', () => {
    const v = structuredClone(fixtureV2); v.layers = []
    const range = figure(v).layout.xaxis.range
    expect(range).toEqual(['2026-01-04T00:00:00.000', '2026-01-06T00:00:00.000'])
  })
})
