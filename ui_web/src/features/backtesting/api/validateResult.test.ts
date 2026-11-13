import { describe, expect, it } from 'vitest'
import fixture from './result.fixture.json'
import type { BacktestResult, ImmutableRequest, Run } from './validateResult'
import {
  DEFINITION_VERSION,
  matchesResponse,
  products,
  RESULT_PROFILE,
  sameRequest,
  strategies,
  validateEmbeddedBacktestResult,
  validateImmutableRequest,
  validateResult,
  validateResultResponse,
  validateRunState,
} from './validateResult'

const result = fixture as unknown as BacktestResult
const request = result.request
const runId = 'a'.repeat(32)
const envelope = { run_id: runId, request, data: result }
const clone = () => structuredClone(result)
const payload = (overrides: { request?: unknown; result?: unknown } = {}) => ({
  request: overrides.request ?? structuredClone(request),
  result: overrides.result ?? clone(),
})

describe('Futures Roll pure request validation', () => {
  it('uses generated product/strategy enumerations and accepts the immutable fixture request unchanged', () => {
    expect(products).toEqual(['IM', 'IC', 'IF', 'IH'])
    expect(strategies).toEqual(['expiry_to_M1_v1', 'expiry_to_Q1_v1'])
    expect(validateImmutableRequest(request)).toBe(request)
  })

  it('rejects malformed, aliased and incomplete requests instead of casting', () => {
    for (const value of [
      { ...request, extra: true },
      { ...request, product_code: 'ZZ' },
      { ...request, strategy_profile: 'other_profile' },
      { ...request, case: 'other_case' },
      { ...request, start_date: '2025/02/17' },
      { ...request, end_date: '2025-02-30' },
      { case: request.case, product_code: request.product_code, start_date: request.start_date, end_date: request.end_date },
    ]) {
      expect(() => validateImmutableRequest(value)).toThrow(/immutable request/)
    }
  })

  it('keeps the five-field identity semantics for every request field', () => {
    expect(sameRequest(request, structuredClone(request))).toBe(true)
    const mutations: Array<Partial<Record<keyof ImmutableRequest, string>>> = [
      { case: 'other_case' },
      { product_code: 'IC' },
      { start_date: '2025-02-18' },
      { end_date: '2025-03-26' },
      { strategy_profile: 'expiry_to_Q1_v1' },
    ]
    for (const mutation of mutations) expect(sameRequest(request, { ...request, ...mutation } as ImmutableRequest)).toBe(false)
  })
})

describe('Futures Roll pure result validation', () => {
  it('accepts the complete producer fixture with both V2 Views and returns the original payload', () => {
    const input = payload()
    const before = structuredClone(input)
    const validated = validateEmbeddedBacktestResult(input)
    expect(validated.request).toBe(input.request)
    expect(validated.result).toBe(input.result)
    expect(validated.result.profile).toBe(RESULT_PROFILE)
    expect(validated.result.definition_version).toBe(DEFINITION_VERSION)
    expect(validated.result.case).toBe('futures_roll_long_v1')
    expect(validated.result.status).toBe('complete')
    expect(validated.result.views.returns.version).toBe(2)
    expect(validated.result.views.drawdown.version).toBe(2)
    expect(input).toEqual(before)
  })

  it('rejects Result profile, definition, case, status and envelope shape drift', () => {
    const values: unknown[] = [
      { ...clone(), profile: 'other_profile' },
      { ...clone(), definition_version: 'other_definition' },
      { ...clone(), case: 'other_case' },
      { ...clone(), status: 'partial' },
      { ...clone(), summary: { ...result.summary, extra: 1 } },
      { ...clone(), views: undefined },
    ]
    for (const value of values) expect(() => validateResult(value, request)).toThrow()
  })

  it('requires the fixed request to answer the Result request exactly', () => {
    for (const mutation of [
      { end_date: '2025-03-26' },
      { strategy_profile: 'expiry_to_Q1_v1' as const },
      { product_code: 'IC' as const },
    ]) {
      const fixed = { ...request, ...mutation }
      expect(() => validateEmbeddedBacktestResult({ request: fixed, result: clone() })).toThrow(/does not match/)
    }
  })

  it('rejects malformed Returns and Drawdown V2 Views without recomputing their data', () => {
    const returns = clone()
    returns.views.returns.layers[0].x_axis = 'missing'
    expect(() => validateResult(returns, request)).toThrow(/V2 view/)

    const drawdown = clone()
    drawdown.views.drawdown.layers[0].layer.data.reverse()
    expect(() => validateResult(drawdown, request)).toThrow(/V2 view/)

    const version = clone()
    const versionedView = version.views.returns as unknown as { version: number }
    versionedView.version = 1
    expect(() => validateResult(version, request)).toThrow()
  })

  it('preserves supplied producer summary and chart coordinates without projection', () => {
    const input = clone()
    input.summary.gross_return = 0.123456
    const validated = validateResult(input, request)
    expect(validated.summary.gross_return).toBe(0.123456)
    expect(validated.views).toEqual(result.views)
  })

  it('validates the generated Result response envelope and its internal request association', () => {
    expect(matchesResponse('get', '/backtesting/futures-roll/runs/{run_id}/result', 200, envelope)).toBe(true)
    expect(validateResultResponse(envelope)).toBe(envelope)
    expect(() => validateResultResponse({ ...envelope, run_id: 'short' })).toThrow()
    const association = clone()
    association.request = { ...association.request, strategy_profile: 'expiry_to_Q1_v1' }
    expect(() => validateResultResponse({ ...envelope, data: association })).toThrow(/does not match/)
    expect(() => validateResultResponse({ ...envelope, request: { ...request, end_date: '2025-03-26' } })).toThrow(/does not match/)
  })

  it('rejects an invalid embedded payload instead of casting it', () => {
    expect(() => validateEmbeddedBacktestResult(null as never)).toThrow(/embedded Backtest Result payload/)
    expect(() => validateEmbeddedBacktestResult({ request, result: null })).toThrow()
    expect(() => validateEmbeddedBacktestResult({ request: null, result })).toThrow(/immutable request/)
  })
})

describe('Futures Roll pure Run state validation', () => {
  const base: Run = {
    run_id: runId,
    request,
    status: 'PENDING',
    created_at: '2026-11-09T00:00:00Z',
    started_at: null,
    finished_at: null,
    result_available: false,
    failure: null,
  }
  const run = (overrides: Partial<Run>): Run => ({ ...base, ...overrides })

  it('accepts coherent PENDING, RUNNING, COMPLETED, FAILED and INTERRUPTED states', () => {
    expect(validateRunState(base)).toBe(base)
    expect(validateRunState(run({ status: 'RUNNING', started_at: '2026-11-09T00:00:01Z' }))).toBeTruthy()
    expect(validateRunState(run({ status: 'COMPLETED', started_at: '2026-11-09T00:00:01Z', finished_at: '2026-11-09T00:00:02Z', result_available: true }))).toBeTruthy()
    for (const status of ['FAILED', 'INTERRUPTED'] as const) {
      expect(validateRunState(run({ status, started_at: '2026-11-09T00:00:01Z', finished_at: '2026-11-09T00:00:02Z', failure: { stage: 'execution', category: 'internal_failure', dependency: null, reason: 'internal_failure' } }))).toBeTruthy()
    }
  })

  it('rejects incoherent timestamps, availability and failure fields', () => {
    for (const value of [
      run({ status: 'RUNNING' }),
      run({ started_at: '2026-11-09T00:00:01Z' }),
      run({ finished_at: '2026-11-09T00:00:02Z' }),
      run({ status: 'COMPLETED', started_at: '2026-11-09T00:00:01Z', finished_at: '2026-11-09T00:00:02Z' }),
      run({ status: 'FAILED', started_at: '2026-11-09T00:00:01Z', finished_at: '2026-11-09T00:00:02Z' }),
      run({ failure: { stage: 'execution', category: 'internal_failure', dependency: null, reason: 'internal_failure' } }),
    ]) expect(() => validateRunState(value)).toThrow(/Run/)
  })
})
