import { useState } from 'react'
import { validateEmbeddedReport, type EmbeddedReportPayload, type ValidatedEmbeddedReport } from '../api/validateResult'

// Static controller: validates the fixed request and the complete Embedded Report once.
// It owns no Run, HTTP request, Auth, preflight, polling or `run_id` restore.
export type StaticFuturesBasisState =
  | { status: 'validated'; data: ValidatedEmbeddedReport }
  | { status: 'invalid'; error: unknown }

export function useStaticFuturesBasis(payload: EmbeddedReportPayload): StaticFuturesBasisState {
  const [state] = useState<StaticFuturesBasisState>(() => {
    try {
      return { status: 'validated', data: validateEmbeddedReport(payload) }
    } catch (error) {
      return { status: 'invalid', error }
    }
  })
  return state
}
