import { Segmented } from 'antd'
import type { DateAxisMode } from './presentation'

const options: { label: string; value: DateAxisMode }[] = [
  { label: 'Trading Days', value: 'trading' },
  { label: 'Calendar Days', value: 'calendar' },
]

/** Single implementation of the repository date-axis mode control (see DATE_AXIS_PRESENTATION.md). */
export function DateAxisControl({ value, onChange, label }: {
  value: DateAxisMode
  onChange: (mode: DateAxisMode) => void
  label: string
}) {
  return <Segmented aria-label={label} style={{ alignSelf: 'flex-start' }} options={options} value={value} onChange={onChange} />
}
