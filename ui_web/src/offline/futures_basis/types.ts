import type { VisualizationView } from '../../shared/visualization'

export interface Method {
  spec: { method: string }
  failure_category: string | null
  reason: string | null
  result: {
    method: string; unit: string; sample_count: number; estimator?: string
    value?: number; points_and_values?: [number, number][]; edges?: number[]
    bins?: { left: number; right: number; left_inclusive: boolean; right_inclusive: boolean; count: number; frequency: number }[]
    underflow_count?: number; overflow_count?: number
    underflow_frequency?: number; overflow_frequency?: number
  } | null
}
export interface AnalysisRequest { analysis_id: string; metric: string; histogram?: { unit: string }; slot?: string; slots?: string[] }
export interface Distribution { request: AnalysisRequest; candidates: unknown[]; binding: unknown[]; methods: Method[] }
export interface Comparison {
  request: AnalysisRequest; common_dates: string[]; dropped: unknown[]
  dropped_details: { date: string; left: { slot: string; outcome: { status: string; reason: string | null } }; right: { slot: string; outcome: { status: string; reason: string | null } } }[]
  left_methods: Method[]; right_methods: Method[]
}
export interface Run {
  slot: string; start: string; end: string; observed_trading_sessions: number
  left_boundary: string; right_boundary: string; transitions: unknown[]
}
export interface ReportData {
  runtime?: { revision: string; dirty: boolean; python: string; node: string; packages: Record<string, string>; frontend_packages: Record<string, string> }
  profile: string; status: string; fingerprint: string; definition_version: string
  summary: string; sources: string; formulas: string[]; limitations: string[]
  request: { observation: { product_code: string; start_date: string; end_date: string } }
  candidate_dates: string[]
  coverage: Record<string, { requested_units: number; successful_units: number; missing_units: number; pending_units: number; failed_units: number; complete: boolean }>
  accounting: { slot: string; metric: string; candidate_count: number; outcomes: { status: string; identities: unknown[]; candidate_ratio: number | null }[] }[]
  distributions: Distribution[]; comparisons: Comparison[]
  persistence: { slot: string; complete: Run[]; censored: Run[] }[]
  views: { history: Record<string, VisualizationView>; histograms: Record<string, VisualizationView> }
}
