import type { Result } from '../api/validateResult'
import type { ViewV2, DateMark } from '../../../shared/visualization/contractV2'

export function sessionDates(r: Result): string[] {
  return [...r.historical_days.filter(d => d.status === 'open').map(d => d.trade_date), ...(r.current_day.status === 'open' ? [r.current_day.trade_date] : [])]
}
export function historicalView(r: Result, index: number): ViewV2 {
  const pair = r.pairs[index]
  const byDate = new Map(pair.samples.map(s => [s.trade_date, s]))
  const x = { kind: 'date', unit: 'date' } as const
  const y = { kind: 'number', unit: r.unit } as const
  let segment = 0; let previousContracts = ''
  const data: DateMark[] = r.historical_days.filter(d => d.status === 'open').map(d => {
    const sample = byDate.get(d.trade_date)
    const contracts = sample ? `${sample.near.contract_code}/${sample.far.contract_code}` : ''
    if (!sample || contracts !== previousContracts) ++segment
    previousContracts = contracts
    return { x: d.trade_date, y: sample?.metric.value ?? null, segment_id: `segment-${segment}`, details: sample ? [
      { label: 'Near', value: sample.near.contract_code }, { label: 'Far', value: sample.far.contract_code },
      { label: 'Raw value', value: String(sample.metric.value) }, { label: 'Stage', value: sample.expiry_stage },
    ] : [{ label: '状态', value: '无有效观察；不插值' }] }
  })
  const current = r.current_day.observations[index]
  const currentMarks: DateMark[] = current?.outcome === 'valid' ? [{ x: current.trade_date, y: current.metrics![r.metric].value, segment_id: 'evaluation', details: [
    { label: 'Near', value: current.near!.contract_code }, { label: 'Far', value: current.far!.contract_code },
    { label: 'Raw value', value: String(current.metrics![r.metric].value) },
  ] }] : []
  return { version: 2, axes: [{ id: 'date', orientation: 'x', coordinate: x }, { id: 'value', orientation: 'y', coordinate: y }],
    layers: [
      { id: 'history', label: '历史价差', layer: { type: 'line', version: 2, x, y, data }, x_axis: 'date', y_axis: 'value' },
      { id: 'current', label: '当前评价日', layer: { type: 'line', version: 2, x, y, data: currentMarks }, x_axis: 'date', y_axis: 'value' },
    ],
    events: r.current_day.status === 'open' ? [{ id: 'evaluation', x_axis: 'date', x: r.current_day.trade_date, label: '评价日', details: [{ label: '状态', value: current?.outcome ?? '未提供' }] }] : [],
    layout: { title: `${pair.near_slot}/${pair.far_slot} · ${r.metric}` }, presentation: { show_legend: true, zoom: true, pan: true, reset: true },
  }
}
