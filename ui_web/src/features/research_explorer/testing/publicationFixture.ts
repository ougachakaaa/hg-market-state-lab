import views from '../../../../../market_research/tests/fixtures/publication_visualization_v1.json'
import type { EmbeddedPublicationSetPayload } from '../api/validateEmbeddedPublication'
import type { Analysis, Manifest, PublicationList } from '../api/validateResearch'

// Test-only Deep Reader fixture. Not an official D3 Publication Example, not live
// research and not proof of market-source authenticity. Existing ChartView regression
// data is reused unchanged; the surrounding Publication/Manifest/Analysis identities are
// deliberately minimal test data.
const jobIdentity = (subject: string): Manifest['jobs'][number]['job_identity'] => ({
  subject, metric: 'trailing_cumulative_return_v1', metric_parameters: {},
  horizon: 2, horizon_unit: 'sessions', start_date: '2020-01-01', end_date: '2020-12-31',
  bounds: 'inclusive', anchor_meaning: 'end_session',
})
const quantileSpec: Manifest['analyses'][number]['spec'] = { method: 'quantile', points: [0, 0.5, 1] }
const intervalSpec: Manifest['analyses'][number]['spec'] = { method: 'interval_count', edges: [0, 1, 3], unit: 'decimal_ratio' }

const quantileJob = jobIdentity('AAA')
const intervalJob = jobIdentity('BBB')
const quantileSummary: Manifest['analyses'][number] = {
  analysis_id: 'analysis-quantile', request_id: 'quantile-request', job_identity: quantileJob,
  status: 'success', spec: quantileSpec, views: [{ measure: 'quantile', view_id: 'quantile-id' }],
}
const intervalSummary: Manifest['analyses'][number] = {
  analysis_id: 'analysis-interval', request_id: 'interval-request', job_identity: intervalJob,
  status: 'success', spec: intervalSpec,
  views: [{ measure: 'count', view_id: 'count-id' }, { measure: 'frequency', view_id: 'frequency-id' }],
}

export const publicationList: PublicationList = {
  data: [{ publication_id: 'pub-static-one', status: 'success' }],
  next_cursor: null,
}

export const publicationManifest: Manifest = {
  schema_version: 1,
  publication_id: 'pub-static-one',
  status: 'success',
  context: null,
  source: { sha256: 'a'.repeat(64), size: 4096 },
  scope: {
    metric: 'trailing_cumulative_return_v1',
    metric_parameters: {},
    subjects: ['AAA', 'BBB'],
    horizons: [2],
    windows: [{ start_date: '2020-01-01', end_date: '2020-12-31' }],
    analysis_requests: [
      { request_id: 'quantile-request', spec: quantileSpec },
      { request_id: 'interval-request', spec: intervalSpec },
    ],
    on_job_failure: 'continue',
  },
  jobs: [
    { job_identity: quantileJob, status: 'Success', analyses: ['analysis-quantile'] },
    { job_identity: intervalJob, status: 'Success', analyses: ['analysis-interval'] },
  ],
  analyses: [quantileSummary, intervalSummary],
}

const factCoverage = { expected_fact_count: 4, available_fact_count: 4, coverage_ratio: 1 }
const coverage: NonNullable<Analysis['coverage']> = {
  candidate_count: 4,
  eligible_count: 4,
  unavailable_count: 0,
  excluded_count: 0,
  observation_coverage: 1,
  unavailable_ratio: 0,
  excluded_ratio: 0,
  observation_unit: 'decimal_ratio',
  input_profile: 'trailing_return_inputs_v2',
  input_fingerprint: 'test-only-input-fingerprint',
  market_facts: { overall: factCoverage, warm_up: factCoverage, sample: factCoverage },
}

export const publicationAnalyses: Analysis[] = [
  {
    schema_version: 1,
    publication_id: 'pub-static-one',
    summary: quantileSummary,
    outcome: 'success',
    reason: null,
    coverage,
    result: {
      method: 'quantile', sample_count: 4, unit: 'decimal_ratio', estimator: 'type7_linear_v1',
      points_and_values: [[0, -1], [0.5, 0], [1, 3.25]],
    },
  },
  {
    schema_version: 1,
    publication_id: 'pub-static-one',
    summary: intervalSummary,
    outcome: 'success',
    reason: null,
    coverage,
    result: {
      method: 'interval_count', sample_count: 4, unit: 'decimal_ratio', edges: [0, 1, 3],
      bins: [
        { left: 0, right: 1, left_inclusive: true, right_inclusive: false, count: 1, frequency: 0.25 },
        { left: 1, right: 3, left_inclusive: true, right_inclusive: true, count: 1, frequency: 0.25 },
      ],
      underflow_count: 1, underflow_frequency: 0.25,
      overflow_count: 1, overflow_frequency: 0.25,
    },
  },
]

export const publicationViews = [
  { publication_id: 'pub-static-one', view_id: 'quantile-id', view: views[0] },
  { publication_id: 'pub-static-one', view_id: 'count-id', view: views[1] },
  { publication_id: 'pub-static-one', view_id: 'frequency-id', view: views[2] },
]

export const embeddedPublicationSet: EmbeddedPublicationSetPayload = {
  pages: [publicationList],
  manifests: [publicationManifest],
  analyses: publicationAnalyses,
  views: publicationViews,
}
