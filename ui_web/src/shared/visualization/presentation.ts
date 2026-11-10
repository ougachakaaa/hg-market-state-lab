import type { DateMark, Detail, VisualizationView } from './contractV2'

/** Frontend options, never serialized into a producer View. */
export interface RenderOptions {
  ordinalDates?: readonly string[]
  axisGrid?: Record<string, { tick0: number; dtick: number; gridcolor: string; griddash: 'dash' | 'dot' }>
  categoryLabels?: Record<string, ReadonlyMap<string, string>>
  pointDetails?: (mark: DateMark, unit: string) => Detail[]
}

export function ordinalTicks(dates: readonly string[], range: readonly number[] = [0, dates.length - 1]) {
  const first = Math.max(0, Math.ceil(range[0]))
  const last = Math.min(dates.length - 1, Math.floor(range[1]))
  const step = Math.max(1, Math.ceil((last - first + 1) / 8))
  const tickvals: number[] = []
  for (let i = first; i <= last; i += step) tickvals.push(i)
  return { tickmode: 'array' as const, tickvals, ticktext: tickvals.map(i => dates[i]) }
}

/** Bind ordered display labels to exact category identities, without parsing them. */
export function categoryLabelOptions(view: VisualizationView, labels: readonly string[]): RenderOptions {
  if (view.version !== 1) return {}
  const categoryLabels: NonNullable<RenderOptions['categoryLabels']> = {}
  for (const axis of view.axes.filter(a => a.coordinate.kind === 'category')) {
    const categories = [...new Set(view.layers.filter(b => b[`${axis.orientation}_axis`] === axis.id)
      .flatMap(b => b.layer.data.map(m => String(m[axis.orientation as keyof typeof m]))))]
    if (categories.length !== labels.length) throw new Error('Category/display-label count mismatch')
    categoryLabels[axis.id] = new Map(categories.map((category, i) => [category, labels[i]]))
  }
  return { categoryLabels }
}
