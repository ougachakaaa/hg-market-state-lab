import type { DateAxisMode, RenderOptions } from '../../../shared/visualization'

/** Ordered observed-session domain supplied by the result; no calendar inference or sorting. */
export function tradingDates(daily: readonly { trade_date: string }[]): readonly string[] {
  return daily.map(row => row.trade_date)
}

/** Shared presentation options for every date-axis chart of one result. */
export function resultChartOptions(dates: readonly string[], mode: DateAxisMode): RenderOptions {
  return { ordinalDates: mode === 'trading' ? dates : undefined }
}
