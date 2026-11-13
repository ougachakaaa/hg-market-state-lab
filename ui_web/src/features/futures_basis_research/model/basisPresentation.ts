import type { ReportData } from '../report/types'

// Feature-owned presentation facts shared by the Production controller composition and the
// static Embedded Report composition. Projections only read producer values; nothing here
// recomputes Basis, DTE, statistics, coverage or persistence.

export interface FuturesBasisCoverage {
  reportProfile: string
  definitionVersion: string
  status: string
  fingerprint: string
  candidateCount: number
  firstCandidate: string | null
  lastCandidate: string | null
  complete: boolean
}

/** Actual observed coverage claimed by the validated producer report. */
export function observedCoverage(report: ReportData): FuturesBasisCoverage {
  return {
    reportProfile: report.profile,
    definitionVersion: report.definition_version,
    status: report.status,
    fingerprint: report.fingerprint,
    candidateCount: report.candidate_dates.length,
    firstCandidate: report.candidate_dates[0] ?? null,
    lastCandidate: report.candidate_dates.at(-1) ?? null,
    complete: Object.keys(report.coverage).length > 0 && Object.values(report.coverage).every(item => item.complete),
  }
}

export const STATIC_BASIS_DISCLOSURE =
  'Embedded Research Example · 静态嵌入研究示例；未创建服务器 Run，未执行 Preflight 或研究，也未查询在线服务。展示的数据来自已提交的 Producer Reader Payload。'

export const STATIC_BASIS_SOURCE_NOTE =
  '展示成功仅表示该 Payload 通过正式 Report Profile、Visualization 与固定请求关联校验；不代表浏览器完成了一次服务器研究执行，也不代表在线服务当前状态。'
