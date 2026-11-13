import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
vi.mock('react-plotly.js', () => ({ default: () => null }))
import type { Analysis } from '../api/research'
import { AnalysisDetails } from '../components/AnalysisDetails'
afterEach(cleanup)
const summary: Analysis['summary'] = { analysis_id: 'a', request_id: 'same', status: 'success', job_identity: { subject: 'S', horizon: 2, horizon_unit: 'days', start_date: '2020-01-01', end_date: '2020-02-01', bounds: 'inclusive', anchor_meaning: 'end', metric: 'm', metric_parameters: {} }, spec: { method: 'quantile', points: [0.5] }, views: [] }
const base: Analysis = { schema_version: 1, publication_id: 'p', summary, outcome: 'success', reason: null, result: null, coverage: null }
it('displays original quantile values and reports missing coverage', () => {
  render(<AnalysisDetails analysis={{ ...base, result: { method: 'quantile', sample_count: 2, unit: 'decimal_ratio', estimator: 'linear', points_and_values: [[0.5, 0.123456789]] } }} />)
  expect(screen.getByText('12.3%')).toBeTruthy()
  expect(screen.getByText('linear')).toBeTruthy()
  expect(screen.getByText('Coverage 不可用')).toBeTruthy()
})
it('preserves interval boundaries, inclusion flags, zero and tail counts', () => {
  render(<AnalysisDetails analysis={{ ...base, result: { method: 'interval_count', sample_count: 2, unit: 'decimal_ratio', edges: [-1, 0], bins: [{ left: -1, right: 0, left_inclusive: true, right_inclusive: false, count: 0, frequency: 0 }], underflow_count: 1, underflow_frequency: 0.5, overflow_count: 1, overflow_frequency: 0.5 } }} />)
  for (const text of ['Underflow', 'Overflow', 'Bin 1', 'true', 'false']) expect(screen.getByText(text)).toBeTruthy()
  expect(screen.getAllByText('-100.0%')).toHaveLength(2)
  expect(screen.getAllByText('0').length).toBeGreaterThan(1)
  expect(screen.getAllByText('0.5')).toHaveLength(2)
})
it('shows unavailable and excluded counts separately, retains null ratios and fact coverage', () => {
  const fact = { expected_fact_count: 0, available_fact_count: 0, coverage_ratio: null }
  render(<AnalysisDetails analysis={{ ...base, coverage: { candidate_count: 4, eligible_count: 1, unavailable_count: 2, excluded_count: 1, observation_coverage: 0.25, unavailable_ratio: 0.5, excluded_ratio: 0.25, observation_unit: 'decimal_ratio', input_profile: 'trailing_return_inputs_v2', input_fingerprint: 'fingerprint', market_facts: { overall: fact, warm_up: fact, sample: fact } } }} />)
  fireEvent.click(screen.getByRole('button', { name: '展开覆盖与来源证据' }))
  for (const text of ['unavailable_count', 'excluded_count', '0.5', 'fingerprint']) expect(screen.getByText(text)).toBeTruthy()
  expect(screen.getAllByText('N/A')).toHaveLength(3)
})
it.each(['failed', 'not_attempted'] as const)('shows %s outcome without a fabricated result', outcome => {
  render(<AnalysisDetails analysis={{ ...base, outcome, result: null, reason: outcome === 'failed' ? 'Analysis failed.' : 'Analysis was not attempted.' }} />)
  expect(screen.getByText(new RegExp(outcome))).toBeTruthy()
  expect(screen.queryByText('原始统计结果')).toBeNull()
})

it('renders zero-denominator observation ratios as N/A and keeps zero population counts', () => {
  const fact = { expected_fact_count: 0, available_fact_count: 0, coverage_ratio: null }
  render(<AnalysisDetails analysis={{ ...base, coverage: { candidate_count: 0, eligible_count: 0, unavailable_count: 0, excluded_count: 0, observation_coverage: null, unavailable_ratio: null, excluded_ratio: null, observation_unit: 'decimal_ratio', input_profile: 'trailing_return_inputs_v2', input_fingerprint: 'zero', market_facts: { overall: fact, warm_up: fact, sample: fact } } }} />)
  fireEvent.click(screen.getByRole('button', { name: '展开覆盖与来源证据' }))
  expect(screen.getAllByText('N/A')).toHaveLength(6)
  expect(screen.getAllByText('0')).toHaveLength(10)
})

it('retains complete coverage as published without using sample count to derive it', () => {
  const fact = { expected_fact_count: 5, available_fact_count: 5, coverage_ratio: 1 }
  const coverage: NonNullable<Analysis['coverage']> = { candidate_count: 3, eligible_count: 3, unavailable_count: 0, excluded_count: 0, observation_coverage: 1, unavailable_ratio: 0, excluded_ratio: 0, observation_unit: 'decimal_ratio', input_profile: 'trailing_return_inputs_v2', input_fingerprint: 'shared-job', market_facts: { overall: fact, warm_up: fact, sample: fact } }
  const first = { ...base, coverage, result: { method: 'quantile' as const, sample_count: 3, unit: 'decimal_ratio', estimator: 'linear', points_and_values: [[0.5, 0] as [number, number]] } }
  const { rerender } = render(<AnalysisDetails analysis={first} />)
  fireEvent.click(screen.getByRole('button', { name: '展开覆盖与来源证据' }))
  expect(screen.getByText('shared-job')).toBeTruthy()
  rerender(<AnalysisDetails analysis={{ ...first, summary: { ...summary, analysis_id: 'other' }, result: { ...first.result, sample_count: 17 } }} />)
  expect(screen.getByText('shared-job')).toBeTruthy()
  expect(screen.getByText('17')).toBeTruthy()
  expect(screen.getByText('candidate_count').closest('tr')?.textContent).toContain('3')
})
