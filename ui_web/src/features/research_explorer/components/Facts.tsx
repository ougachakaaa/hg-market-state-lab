import { Descriptions, Typography } from 'antd'
import { displayValue } from './displayValue'

const labels: Record<string, string> = {
  status: '发布状态', metric: '指标', metric_parameters: '指标参数', subjects: '标的',
  horizons: '时间跨度', inclusive_windows: '日期窗口（含首尾）',
  analysis_requests: '声明的分析请求', on_job_failure: 'Job 失败策略',
  jobs: 'Jobs 数量', analyses: 'Analyses 数量',
}

export function Facts({ title, data }: { title: string; data: object }) {
  return <section aria-label={title}><Typography.Title level={5}>{title}</Typography.Title><Descriptions size="small" column={{ xs: 1, lg: 2 }} items={Object.entries(data).map(([key, value]) => ({
    key,
    label: labels[key] ?? key,
    children: <span style={{ overflowWrap: 'anywhere', whiteSpace: 'pre-wrap' }}>{Array.isArray(value)
      ? value.map((item, index) => <div key={index}>{displayValue(item)}</div>)
      : displayValue(value)}</span>,
  }))} /></section>
}
