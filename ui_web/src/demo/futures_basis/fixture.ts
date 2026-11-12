import raw from './report.v1.json?raw'
import { validateReportData } from '../../features/futures_basis_research/report/validate'
import type { ReportData } from '../../features/futures_basis_research/report/types'

export const FIXTURE_PROFILE = 'futures_basis_demo_fixture_v1'
export const REPORT_PROFILE = 'futures_basis_report_evidence_v1'

export interface DemoDisclosure {
  label: string
  data_source: string
  notice: string
}

/** Versioned public demo envelope; it wraps the unchanged producer reader. */
export interface FuturesBasisDemoFixture {
  fixture_profile: typeof FIXTURE_PROFILE
  classification: 'synthetic'
  generated_by: string
  report_profile: typeof REPORT_PROFILE
  disclosure: DemoDisclosure
  report: ReportData
}

function text(value: unknown, field: string): string {
  if (typeof value !== 'string' || value.trim() === '') throw new Error(`Invalid demo fixture: ${field}`)
  return value
}

function record(value: unknown, field: string): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`Invalid demo fixture: ${field}`)
  return value as Record<string, unknown>
}

/**
 * Validate one static demo envelope through the existing reader contract.
 * No network, auth, backend or financial computation is involved.
 */
export function parseFuturesBasisDemoFixture(input: unknown): FuturesBasisDemoFixture {
  const fixture = record(input, 'envelope')
  if (fixture.fixture_profile !== FIXTURE_PROFILE) throw new Error('Unsupported demo fixture profile')
  if (fixture.classification !== 'synthetic') throw new Error('Demo fixture must be classified synthetic')
  if (fixture.report_profile !== REPORT_PROFILE) throw new Error('Unsupported demo report profile')
  const disclosure = record(fixture.disclosure, 'disclosure')
  const report = fixture.report
  validateReportData(report)
  return {
    fixture_profile: FIXTURE_PROFILE,
    classification: 'synthetic',
    generated_by: text(fixture.generated_by, 'generated_by'),
    report_profile: REPORT_PROFILE,
    disclosure: {
      label: text(disclosure.label, 'disclosure.label'),
      data_source: text(disclosure.data_source, 'disclosure.data_source'),
      notice: text(disclosure.notice, 'disclosure.notice'),
    },
    report,
  }
}

/**
 * The committed demo fixture, validated at import time. WP3 renders
 * `report` with the shared reader and must show `disclosure` alongside it.
 */
export const futuresBasisDemoFixture = parseFuturesBasisDemoFixture(JSON.parse(raw))
