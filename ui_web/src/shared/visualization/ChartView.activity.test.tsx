import { Activity } from 'react'
import { act, cleanup, render } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import type { Data, Layout } from 'plotly.js'
import { ChartView } from './ChartView'
import { fixtureV2 } from './fixturesV2'
// Exercise the installed React Plotly wrapper, including its real Effect purge /
// initialization / resize lifecycle. Only the browser drawing engine is replaced.
const engine = vi.hoisted(() => ({ react: vi.fn(), purge: vi.fn(), Plots: { resize: vi.fn() } }))
vi.mock('react-plotly.js', async () => {
 const { default: factory } = await import('react-plotly.js/factory')
 return { default: factory(engine) }
})
type Graph = HTMLElement & { data: Data[]; layout: Partial<Layout>; on: ReturnType<typeof vi.fn>; removeListener: ReturnType<typeof vi.fn> }
afterEach(() => { cleanup(); vi.clearAllMocks() })
it('restores viewport, legend and drag mode through actual Plotly wrapper purge and resizes on reconnect', async () => {
 engine.react.mockImplementation(async (node: Graph, figure: { data: Data[]; layout: Partial<Layout> }) => {
  node.data = figure.data; node.layout = figure.layout
  node.on = vi.fn(); node.removeListener = vi.fn()
 })
 engine.purge.mockImplementation((node: Graph) => { delete (node as Partial<Graph>).layout; delete (node as Partial<Graph>).data })
 const tree = (active: boolean) => <Activity mode={active ? 'visible' : 'hidden'}><ChartView view={fixtureV2} retainInteractionState /></Activity>
 const view = render(tree(true)); await act(async () => {})
 const graph = view.container.querySelector('[style*="width: 100%"]')
 const node = engine.react.mock.calls[0][0] as Graph
 expect(graph).toBeTruthy()
 node.layout.xaxis = { ...node.layout.xaxis, range: [1, 2], autorange: false }
 node.layout.dragmode = 'pan'; node.data[0].visible = 'legendonly'
 const traces = node.data.map(trace => ({ ...trace, visible: undefined }))
 view.rerender(tree(false)); await act(async () => {})
 expect(engine.purge).toHaveBeenCalled()
 const resizes = engine.Plots.resize.mock.calls.length
 view.rerender(tree(true)); await act(async () => {})
 expect(node.layout.xaxis?.range).toEqual([1, 2]); expect(node.layout.dragmode).toBe('pan')
 expect(node.data[0].visible).toBe('legendonly')
 expect(node.data.map(trace => ({ ...trace, visible: undefined }))).toEqual(traces)
 expect(engine.Plots.resize.mock.calls.length).toBeGreaterThan(resizes)
})
