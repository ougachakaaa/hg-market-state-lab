import Plot from 'react-plotly.js'
import type { ChartView as ChartViewContract } from './contract'
import { chartViewToPlotly } from './figure'

/** Renders a complete inline View; validation errors are thrown to the caller. */
export function ChartView({ view }: { view: ChartViewContract }) {
  const figure = chartViewToPlotly(view)
  return <Plot {...figure} style={{ width: '100%', height: '100%' }} useResizeHandler />
}
