/** Development/test entry only. No application navigation or HTTP consumer. */
import { useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Button, ConfigProvider, Flex } from 'antd'
import { ChartView } from './ChartView'
import { fixtureV2, extendedFixtureV2 } from './fixturesV2'
import { fixtures } from './fixtures'
import type { VisualizationView } from './contractV2'

const multiAxis = structuredClone(fixtureV2)
multiAxis.axes.push({ id: 'distance', orientation: 'y', coordinate: { kind: 'number', unit: 'distance' } })
multiAxis.layers[1].y_axis = 'distance'; multiAxis.layers[1].layer.y.unit = 'distance'
const gap = structuredClone(fixtureV2)
gap.layers[0].layer.data.forEach(m => { m.segment_id = 'continuous' })
gap.layers[1].layer.data.forEach(m => { m.segment_id = 'continuous' })
const allNull = structuredClone(fixtureV2)
allNull.layers.forEach(b => b.layer.data.forEach(m => { m.y = null }))
const emptySeries = structuredClone(fixtureV2)
emptySeries.layers.forEach(b => { b.layer.data = [] })
const overlap = structuredClone(fixtureV2)
overlap.layers[1].layer.data[0].y = 1
overlap.presentation.show_legend = false
// Long artificial weekday domain exercises label density without market inputs.
const longDates = Array.from({ length: 800 }, (_, i) => new Date(Date.UTC(2023, 0, 2 + i)))
  .filter(d => d.getUTCDay() !== 0 && d.getUTCDay() !== 6).map(d => d.toISOString().slice(0, 10))
const longView = structuredClone(fixtureV2)
longView.axes[1].coordinate.unit = 'decimal_ratio'
longView.layers.forEach((binding, index) => {
  binding.layer.y.unit = 'decimal_ratio'
  binding.layer.data = longDates.map((x, i) => ({ x, y: i % 31 === 0 ? null : Math.sin(i / 10) * .15 + index * .1, segment_id: String(Math.floor(i / 40)), details: [] }))
})
longView.events = [{ ...longView.events[0], x: longDates[200] }]
const indexGrid = structuredClone(longView)
indexGrid.axes[1].coordinate.unit = 'index_points'
indexGrid.layers.forEach(b => { b.layer.y.unit = 'index_points'; b.layer.data.forEach(m => { if (m.y !== null) m.y *= 1000 }) })
const nearZero = structuredClone(longView)
nearZero.layers.forEach(b => { b.layer.data = b.layer.data.slice(0, 3).map((m, i) => ({ ...m, y: (i - 1) * .000001 })) })
nearZero.events = []
const variants: Record<string, VisualizationView> = {
  'Fixed V2': fixtureV2,
  'Long ordinal': longView,
  'Near zero ratio': nearZero,
  'Index grid': indexGrid,
  'Events V2': extendedFixtureV2(),
  'Multi-axis V2': multiAxis,
  'Null gap V2': gap,
  'Overlapping points': overlap,
  'Zoom only': { ...fixtureV2, presentation: { show_legend: true, zoom: true, pan: false, reset: false } },
  'Pan only': { ...fixtureV2, presentation: { show_legend: true, zoom: false, pan: true, reset: false } },
  'Disabled': { ...fixtureV2, presentation: { show_legend: false, zoom: false, pan: false, reset: false } },
  'All null': allNull,
  'Empty series': emptySeries,
  'Empty view': { ...fixtureV2, axes: [], layers: [], events: [] },
  'V1 mixed': fixtures.mixed,
  'V1 bar': fixtures.bar,
}
export function Harness() {
  const [name, setName] = useState('Fixed V2')
  return <ConfigProvider><Flex vertical gap="middle">
    <Flex wrap gap="small" aria-label="Fixture selection">{Object.keys(variants).map(key => <Button key={key} onClick={() => setName(key)}>{key}</Button>)}</Flex>
    <div style={{ height: 650 }}><ChartView key={name} view={variants[name]} options={name === 'Long ordinal' ? { ordinalDates: longDates } : name === 'Index grid' ? { ordinalDates: longDates, axisGrid: { [indexGrid.axes[1].id]: { tick0: 0, dtick: 100, gridcolor: 'rgba(180,180,180,0.25)', griddash: 'dash' } } } : undefined} /></div>
  </Flex></ConfigProvider>
}
createRoot(document.getElementById('root')!).render(<Harness />)
