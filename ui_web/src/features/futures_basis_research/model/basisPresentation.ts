import type { Distribution, Method } from '../report/types'
import { formatUnit } from '../../../shared/format/unit'

export const STATIC_BASIS_DISCLOSURE =
  '本页面为静态研究成果展示。数据不保证准确，不构成任何投资建议，仅供项目功能演示。'

function statistic(method: Method | undefined, identity: string, point?: number): string {
  if (method?.failure_category) return `不可用（${method.failure_category}）`
  const result = method?.result
  if (!result || result.method !== identity || result.sample_count <= 0) return '不可用'
  const value = identity === 'mean' ? result.value : result.points_and_values?.find(([p]) => p === point)?.[1]
  if (value == null || !Number.isFinite(value)) return '不可用'
  return formatUnit(value, result.unit)
}

export function distributionMean(distribution: Distribution): string {
  return statistic(distribution.methods.find(method => method.spec.method === 'mean'), 'mean')
}

/** Projection of producer results only; no numerical statistics are computed here. */
export function distributionSummary(distributions: Distribution[], metric: string) {
  return ['M0', 'M1', 'Q1', 'Q2'].map(slot => {
    const distribution = distributions.find(d => d.request.metric === metric && d.request.slot === slot)
    const methods = distribution?.methods ?? []
    const quantile = methods.find(method => method.spec.method === 'quantile')
    const mean = methods.find(method => method.spec.method === 'mean')
    const cell = (method: Method | undefined, identity: string, point?: number) =>
      distribution?.binding.length ? statistic(method, identity, point)
        : method?.failure_category ? `不可用（${method.failure_category}）` : '不可用'
    return {
      slot, n: distribution ? distribution.binding.length : '不可用',
      min: cell(quantile, 'quantile', 0), p25: cell(quantile, 'quantile', .25),
      median: cell(quantile, 'quantile', .5), p75: cell(quantile, 'quantile', .75),
      max: cell(quantile, 'quantile', 1), mean: cell(mean, 'mean'),
    }
  })
}
