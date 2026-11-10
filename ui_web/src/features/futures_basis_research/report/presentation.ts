import { categoryLabelOptions } from '../../../shared/visualization/presentation'
import { formatUnit } from '../../../shared/format/unit'
import { intervalLabels } from '../../../shared/format/interval'
import type { RenderOptions, VisualizationView } from '../../../shared/visualization'
import type { Method } from './types'

export const historyDetails: RenderOptions['pointDetails'] = (mark, unit) => mark.details.map(detail =>
  detail.label === '结果' && mark.y !== null && unit === 'decimal_ratio'
    ? { ...detail, value: formatUnit(mark.y, unit) } : detail)

export function histogramOptions(view: VisualizationView, result?: Method['result']): RenderOptions {
  if (view.version !== 1 || !result?.bins || result.unit !== 'decimal_ratio') return {}
  return categoryLabelOptions(view, intervalLabels(result))
}

export function historyOptions(view: VisualizationView, dates: string[], tradingDays: boolean, basisValue: boolean): RenderOptions {
  return {
    ordinalDates: tradingDays ? dates : undefined,
    pointDetails: historyDetails,
    axisGrid: basisValue ? Object.fromEntries(view.axes.filter(a => a.orientation === 'y' && a.coordinate.unit === 'index_points')
      .map(a => [a.id, { tick0: 0, dtick: 100, gridcolor: 'rgba(180,180,180,0.25)', griddash: 'dash' as const }])) : undefined,
  }
}
