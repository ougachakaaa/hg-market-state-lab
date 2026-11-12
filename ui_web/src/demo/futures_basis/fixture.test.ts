import { describe, expect, it } from 'vitest'
import {
  FIXTURE_PROFILE,
  REPORT_PROFILE,
  futuresBasisDemoFixture,
  parseFuturesBasisDemoFixture,
} from './fixture'

const clone = () => JSON.parse(JSON.stringify(futuresBasisDemoFixture))

describe('futures basis demo fixture', () => {
  it('parses the committed synthetic envelope through the reader contract', () => {
    expect(futuresBasisDemoFixture.fixture_profile).toBe(FIXTURE_PROFILE)
    expect(futuresBasisDemoFixture.classification).toBe('synthetic')
    expect(futuresBasisDemoFixture.report_profile).toBe(REPORT_PROFILE)
    expect(futuresBasisDemoFixture.disclosure.label).toBe('Synthetic Demo')
    expect(futuresBasisDemoFixture.disclosure.notice).toContain('Synthetic Demo')
    expect(futuresBasisDemoFixture.disclosure.data_source).toContain('no Tushare')
    expect(futuresBasisDemoFixture.report.profile).toBe(REPORT_PROFILE)
    expect(futuresBasisDemoFixture.report.status).toBe('complete')
    expect(futuresBasisDemoFixture.report.runtime).toBeUndefined()
  })

  it('carries complete producer data for every reader section', () => {
    const report = futuresBasisDemoFixture.report
    expect(report.request.observation.product_code).toBe('IM')
    expect(report.candidate_dates).toHaveLength(44)
    expect(report.candidate_dates[0]).toBe('2024-09-02')
    expect(report.candidate_dates.at(-1)).toBe('2024-10-31')
    expect(Object.values(report.coverage).every(coverage => coverage.complete)).toBe(true)
    expect(report.distributions).toHaveLength(12)
    expect(report.comparisons).toHaveLength(18)
    expect(report.persistence).toHaveLength(4)
    expect(Object.keys(report.views.history)).toEqual([
      'basis_value',
      'basis_ratio',
      'annualized_basis_ratio',
    ])
    expect(Object.keys(report.views.histograms)).toHaveLength(24)
    expect(Object.values(report.views.histograms).every(view => view.version === 1)).toBe(true)
    expect(report.fingerprint).toHaveLength(64)
  })

  it('keeps producer coordinates, transitions and honest null points', () => {
    const report = futuresBasisDemoFixture.report
    for (const [metric, view] of Object.entries(report.views.history)) {
      expect(view.version, metric).toBe(2)
      if (view.version !== 2) throw new Error('expected V2 history view')
      expect(view.layers, metric).toHaveLength(4)
      for (const binding of view.layers) {
        expect(binding.layer.data, metric).toHaveLength(report.candidate_dates.length)
        expect(binding.layer.data.map(mark => mark.x), metric).toEqual(report.candidate_dates)
      }
      expect(view.events.length, metric).toBeGreaterThan(0)
      expect(view.presentation.zoom && view.presentation.pan && view.presentation.reset).toBe(true)
      const nulls = view.layers.flatMap(binding => binding.layer.data).filter(mark => mark.y === null)
      expect(nulls.length, metric).toBe(metric === 'annualized_basis_ratio' ? 2 : 0)
    }
  })

  it('includes complete and censored discount runs', () => {
    const persistence = futuresBasisDemoFixture.report.persistence
    expect(persistence.map(summary => summary.slot)).toEqual(['M0', 'M1', 'Q1', 'Q2'])
    expect(persistence.some(summary => summary.complete.length > 0)).toBe(true)
    expect(persistence.some(summary => summary.censored.length > 0)).toBe(true)
    const m0 = persistence.find(summary => summary.slot === 'M0')
    if (!m0) throw new Error('missing M0 persistence summary')
    expect(m0.complete).toHaveLength(2)
    expect(m0.censored).toHaveLength(2)
    expect(m0.complete[0].observed_trading_sessions).toBeGreaterThan(1)
  })

  it('rejects foreign, non-synthetic or corrupted envelopes', () => {
    expect(() => parseFuturesBasisDemoFixture(null)).toThrow()
    expect(() => parseFuturesBasisDemoFixture([])).toThrow()
    const profile = clone()
    profile.fixture_profile = 'other_fixture_v1'
    expect(() => parseFuturesBasisDemoFixture(profile)).toThrow('Unsupported demo fixture profile')
    const real = clone()
    real.classification = 'real'
    expect(() => parseFuturesBasisDemoFixture(real)).toThrow('synthetic')
    const notice = clone()
    notice.disclosure.notice = ''
    expect(() => parseFuturesBasisDemoFixture(notice)).toThrow('disclosure.notice')
    const report = clone()
    report.report.profile = 'other_report_v1'
    expect(() => parseFuturesBasisDemoFixture(report)).toThrow()
    const dates = clone()
    dates.report.candidate_dates = '2024-09-02'
    expect(() => parseFuturesBasisDemoFixture(dates)).toThrow()
  })

  it('re-reads the committed fixture deterministically', () => {
    expect(parseFuturesBasisDemoFixture(clone())).toEqual(futuresBasisDemoFixture)
  })
})
