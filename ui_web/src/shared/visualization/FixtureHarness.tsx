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
const variants: Record<string, VisualizationView> = {
  'Fixed V2': fixtureV2,
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
    <div style={{ height: 650 }}><ChartView key={name} view={variants[name]} /></div>
  </Flex></ConfigProvider>
}
createRoot(document.getElementById('root')!).render(<Harness />)
