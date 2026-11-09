import { ConfigProvider, Layout } from 'antd'
import { applicationTheme } from '../../shared/ui/theme'
import { Report as Reader } from '../../features/futures_basis_research/report/Report'
import type { ReportData } from './types'
import './report.css'

export function Report({ data }: { data: ReportData }) {
  return <ConfigProvider componentSize="small" theme={{ ...applicationTheme, token: { ...applicationTheme.token, fontFamily: 'system-ui, "R01A CJK", sans-serif', fontFamilyCode: 'ui-monospace, "R01A CJK", monospace' } }}><Layout className="r01a-report" style={{ minHeight: '100vh', padding: 24 }}><Layout.Content><Reader data={data} mode="offline" /></Layout.Content></Layout></ConfigProvider>
}
