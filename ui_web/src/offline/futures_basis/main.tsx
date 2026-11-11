import '../../shared/visualization/plotly.css'
import { createRoot } from 'react-dom/client'
import { Component, type ReactNode } from 'react'
import { Alert } from 'antd'
import { Report } from './Report'
import type { ReportData } from './types'

class Boundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null }
  static getDerivedStateFromError(error: Error) { return { error: error.message } }
  render() { return this.state.error ? <Alert type="error" title="离线报告无法展示" description={this.state.error} /> : this.props.children }
}
const element = document.getElementById('report-data')
if (!element) throw new Error('Missing producer report data')
const data = JSON.parse(element.textContent ?? '') as ReportData
const root = createRoot(document.getElementById('root')!)
void document.fonts.load('14px "R01A CJK"', '研究').then(() => {
  root.render(<Boundary><Report data={data} /></Boundary>)
}, () => root.render(<Alert type="error" title="Offline font failed to load" />))
