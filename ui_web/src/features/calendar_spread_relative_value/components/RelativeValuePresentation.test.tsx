import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { RelativeValuePresentation } from './RelativeValuePresentation'
import { validateResult } from '../api/validateResult'
import h0 from '../testing/history0.json'
import h1 from '../testing/history1.json'
import h29 from '../testing/history29.json'
import matchingEmpty from '../testing/matchingempty.json'
import closed from '../testing/currentclosed.json'
import excluded from '../testing/currentexcluded.json'

vi.mock('react-plotly.js', () => ({ default: () => <div data-testid="plot" /> }))
afterEach(cleanup)
it.each([h0, h1, h29, matchingEmpty, closed, excluded])('keeps unavailable and small populations visible without changing the Result ($request.evaluation_date)', raw => {
  const result = validateResult(structuredClone(raw))
  const original = JSON.stringify(result)
  const { container } = render(<RelativeValuePresentation result={result} />)
  const matching = screen.getByText('同到期阶段的历史百分位').closest('.ant-card')!
  const all = screen.getByText('全部阶段的历史百分位').closest('.ant-card')!
  const p = result.pairs[0]
  for (const [element, assessment] of [[matching, p.matching_stage], [all, p.all_stages]] as const) {
    if (assessment.percentile) expect(element.textContent).toContain((assessment.percentile.result.query_results[0].percentile * 100).toFixed(1) + '%')
    else expect(element.textContent).toContain('无可用百分位')
  }
  if (p.all_stages.status === 'small_sample') expect(screen.getAllByText(/N=1–29/).length).toBeGreaterThan(0)
  if (result.current_day.status === 'closed') expect(screen.getByText(/评价日休市/)).toBeTruthy()
  if (result.current_day.observations[0]?.outcome === 'excluded') expect(screen.getByText(/当前观察已排除/)).toBeTruthy()
  expect(screen.queryByText(/midrank_v1/)).toBeNull()
  expect(screen.getByRole('button', { name: '四组历史分布与分位点数值（Quantile）' }).getAttribute('aria-expanded')).toBe('false')
  fireEvent.click(screen.getByRole('button', { name: '研究参数与方法详情' }))
  expect(container.textContent).toContain(result.request.histogram_edges === null ? '未请求' : JSON.stringify(result.request.histogram_edges))
  expect(JSON.stringify(result)).toBe(original)
})
it('preserves valid zero instead of presenting it as unavailable', () => {
  const result = validateResult(structuredClone(h1))
  result.current_day.observations[0].metrics!.annualized_spread_ratio.value = 0
  const { container } = render(<RelativeValuePresentation result={result} />)
  const row = [...container.querySelectorAll('.ant-descriptions-item')].find(e => e.textContent?.includes('年化对数价差率'))!
  expect(within(row as HTMLElement).getByText('0.0%')).toBeTruthy()
})
