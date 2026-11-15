import type { Distribution } from '../report/types'
import { formatUnit } from '../../../shared/format/unit'

export const STATIC_BASIS_DISCLOSURE =
  '本页面为静态研究成果展示。数据不保证准确，不构成任何投资建议，仅供项目功能演示。'

export function distributionMean(distribution: Distribution): string {
  const mean = distribution.methods.find(method => method.spec.method === 'mean')
  if (mean?.failure_category) return `不可用（${mean.failure_category}）`
  const result = mean?.result
  if (!result || result.method !== 'mean' || !Number.isFinite(result.value)) return '不可用'
  return formatUnit(result.value, result.unit)
}
