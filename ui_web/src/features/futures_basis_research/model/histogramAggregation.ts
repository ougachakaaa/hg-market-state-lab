import type { ReportData } from '../report/types'

export const SLOTS = ['M0', 'M1', 'Q1', 'Q2'] as const
export const BIN_PRESETS = {
  basis_value: { default: 10, widths: [5, 10, 20, 50], unit: 'index_points', denominator: 1 },
  basis_ratio: { default: .1, widths: [.1, .2, .5], unit: 'decimal_ratio', denominator: 100 },
  annualized_basis_ratio: { default: 5, widths: [2.5, 5, 10, 20], unit: 'decimal_ratio', denominator: 100 },
} as const
export type BasisMetric = keyof typeof BIN_PRESETS
export const MAX_DISPLAY_BINS = 2000
export interface DisplayBin { left: number; right: number; rightInclusive: boolean; count: number; frequency: number }
export interface SlotHistogram { slot: string; n: number; bins: DisplayBin[]; failure: string | null; layerIndex: number }
export type HistogramProjection =
  | { status: 'ready'; edges: number[]; slots: SlotHistogram[] }
  | { status: 'empty' | 'inconsistent' | 'capacity'; message: string }

/** Feature-local display aggregation. Original samples, report and formal results stay untouched. */
export function histogramAggregation(report: ReportData, metric: BasisMetric, width: number): HistogramProjection {
  const preset = BIN_PRESETS[metric]
  if (!(preset.widths as readonly number[]).includes(width)) return { status: 'inconsistent', message: '展示数据不一致：不支持的分箱宽度。' }
  try {
    const view = report.views.history[metric]
    if (view.version !== 2) throw new Error('历史 View 版本')
    if (view.layers.length !== SLOTS.length || report.distributions.filter(d => d.request.metric === metric).length !== SLOTS.length || report.accounting.filter(a => a.metric === metric).length !== SLOTS.length) throw new Error('四 Slot 输入缺失或重复')
    const product = report.request.observation.product_code
    const dates = report.candidate_dates
    const unique = (values: string[]) => {
      if (new Set(values).size !== values.length) throw new Error('重复身份')
      return new Set(values)
    }
    unique(dates)
    function identities(raw: unknown[], slot: string): Set<string> {
      return unique(raw.map(item => {
        if (!Array.isArray(item) || item.length !== 3 || item[0] !== product || item[2] !== slot || typeof item[1] !== 'string' || !dates.includes(item[1])) throw new Error(`${slot} 样本身份`)
        return item[1]
      }))
    }
    function same(a: Set<string>, b: Set<string>, slot: string) {
      if (a.size !== b.size || [...a].some(key => !b.has(key))) throw new Error(`${slot} 样本关联/数量`)
    }
    const samples = SLOTS.map(slot => {
      const bindings = view.layers.filter(b => b.id === slot)
      const distributions = report.distributions.filter(d => d.request.metric === metric && d.request.slot === slot)
      const accounts = report.accounting.filter(a => a.metric === metric && a.slot === slot)
      if (bindings.length !== 1 || distributions.length !== 1 || accounts.length !== 1) throw new Error(`${slot} 必要输入缺失或重复`)
      const layerIndex = view.layers.findIndex(b => b.id === slot)
      const layer = bindings[0].layer; const distribution = distributions[0]; const account = accounts[0]
      if (layer.y.unit !== preset.unit || distribution.request.histogram?.unit !== preset.unit) throw new Error(`${slot} 单位`)
      same(unique(layer.data.map(p => p.x)), new Set(dates), slot)
      same(identities(distribution.candidates, slot), new Set(dates), slot)
      if (account.candidate_count !== dates.length) throw new Error(`${slot} 候选数`)
      const values: number[] = []; const eligibleDates: string[] = []
      for (const point of layer.data) {
        if (point.y === null) continue
        if (typeof point.y !== 'number' || !Number.isFinite(point.y)) throw new Error(`${slot} 非有限数值`)
        values.push(point.y); eligibleDates.push(point.x)
      }
      const eligible = unique(eligibleDates)
      same(eligible, identities(distribution.binding, slot), slot)
      const statuses = ['eligible', 'unavailable', 'excluded', 'not_applicable']
      if (account.outcomes.length !== statuses.length) throw new Error(`${slot} Accounting 分类`)
      const population: string[] = []
      for (const status of statuses) {
        const outcomes = account.outcomes.filter(o => o.status === status)
        if (outcomes.length !== 1) throw new Error(`${slot} Accounting 分类`)
        const keys = identities(outcomes[0].identities, slot)
        population.push(...keys)
        if (status === 'eligible') same(eligible, keys, slot)
      }
      same(unique(population), new Set(dates), slot)
      for (const method of distribution.methods) {
        if (!method.failure_category && method.result && (method.result.method !== method.spec.method || method.result.sample_count !== values.length || method.result.unit !== preset.unit)) throw new Error(`${slot} Method Result`)
      }
      const intervals = distribution.methods.filter(m => m.spec.method === 'interval_count')
      if (intervals.length !== 1) throw new Error(`${slot} IntervalCount 缺失或重复`)
      const formal = intervals[0]
      // `no_eligible_sample` is only legal for an empty Eligible population. With samples
      // it contradicts the formal Method contract, so the whole Metric is rejected rather
      // than presenting a silently missing curve.
      if (values.length && formal.failure_category === 'no_eligible_sample') throw new Error(`${slot} Eligible 样本与 no_eligible_sample 矛盾`)
      if (values.length && !formal.failure_category && !formal.result) throw new Error(`${slot} IntervalCount Result 缺失`)
      // An empty finding is not a numerical failure; other formal failures stay explicit.
      return { slot, values, failure: formal.failure_category === 'no_eligible_sample' ? null : formal.failure_category, layerIndex }
    })
    const all = samples.flatMap(s => s.values)
    if (!all.length) return { status: 'empty', message: '无有效样本（Eligible N=0）' }
    let min = all[0]; let max = min
    for (const value of all) { min = Math.min(min, value); max = Math.max(max, value) }
    // Presets are rational decimal widths. Generate each edge independently instead
    // of accumulating a binary64 width, and compare original values without snapping.
    const numerator = Math.round(width * 100)
    const denominator = preset.denominator * 100
    const edge = (index: number) => index * numerator / denominator
    let first = Math.floor(min / (numerator / denominator))
    let last = Math.ceil(max / (numerator / denominator))
    const capacity = (): HistogramProjection => ({ status: 'capacity', message: `分箱范围超出展示容量（最多 ${MAX_DISPLAY_BINS} 个 Bin），请选择更大的分箱宽度。` })
    if (![first, last, first * numerator, last * numerator].every(Number.isSafeInteger)) return capacity()
    if (edge(first) > min) first--
    else if (edge(first + 1) <= min) first++
    if (edge(last) < max) last++
    else if (edge(last - 1) >= max) last--
    last = Math.max(first + 1, last)
    if (last - first > MAX_DISPLAY_BINS || ![first * numerator, last * numerator].every(Number.isSafeInteger)) return capacity()
    const edges = Array.from({ length: last - first + 1 }, (_, i) => edge(first + i))
    if (edges[0] > min || edges.at(-1)! < max || edges.some((e, i) => !Number.isFinite(e) || (i > 0 && e <= edges[i - 1]))) return capacity()
    const slots = samples.map(({ slot, values, failure, layerIndex }) => {
      const counts = Array<number>(edges.length - 1).fill(0)
      for (const value of values) {
        // Upper bound: an interior edge belongs to the bin on its right.
        let lo = 0; let hi = edges.length
        while (lo < hi) { const mid = (lo + hi) >>> 1; if (edges[mid] <= value) lo = mid + 1; else hi = mid }
        counts[Math.min(lo - 1, counts.length - 1)]++
      }
      if (counts.reduce((a, b) => a + b, 0) !== values.length) throw new Error(`${slot} Count 不守恒`)
      return { slot, n: values.length, failure, layerIndex, bins: values.length ? counts.map((count, i) => ({ left: edges[i], right: edges[i + 1], rightInclusive: i === counts.length - 1, count, frequency: count / values.length })) : [] }
    })
    return { status: 'ready', edges, slots }
  } catch (error) {
    return { status: 'inconsistent', message: `展示数据不一致：${error instanceof Error ? error.message : '必要输入损坏'}。` }
  }
}
