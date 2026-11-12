import { useState } from 'react'
import {
  validateEmbeddedBacktestResult,
  type EmbeddedBacktestResultPayload,
  type ValidatedEmbeddedBacktestResult,
} from '../api/validateResult'

// Static controller: validates the fixed request and complete Embedded Backtest Result once.
// It owns no Run, HTTP request, Auth, preflight, polling, retry or `run_id` restore.
export type StaticBacktestingState =
  | { status: 'validated'; data: ValidatedEmbeddedBacktestResult }
  | { status: 'invalid'; error: unknown }

export function useStaticBacktesting(payload: EmbeddedBacktestResultPayload): StaticBacktestingState {
  const [state] = useState<StaticBacktestingState>(() => {
    try {
      return { status: 'validated', data: validateEmbeddedBacktestResult(payload) }
    } catch (error) {
      return { status: 'invalid', error }
    }
  })
  return state
}
