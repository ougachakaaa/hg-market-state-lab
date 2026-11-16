import { describe, expect, it } from 'vitest'
import { validateResult } from './validateResult'
import h0 from '../testing/history0.json'
import h1 from '../testing/history1.json'
import h29 from '../testing/history29.json'
import h30 from '../testing/history30.json'
describe('Historical result association', () => {
  it.each([[h0, 0, 'empty_sample'], [h1, 1, 'small_sample'], [h29, 29, 'small_sample'], [h30, 30, 'available']] as const)('accepts actual HTTP result N=%s', (r, n, status) => {
    expect(validateResult(r)).toBe(r)
    expect(r.pairs[0].distributions[3].sample_count).toBe(n)
    expect(r.pairs[0].distributions[3].status).toBe(status)
  })
  it.each([
    (r: any) => r.pairs.reverse(),
    (r: any) => r.pairs[0].samples[0].trade_date = r.request.evaluation_date,
    (r: any) => r.pairs[0].distributions[3].sample_count++,
    (r: any) => r.pairs[0].distributions[3].quantile.result.estimator = 'other',
    (r: any) => r.pairs[0].all_stages.percentile.result.estimator = 'other',
    (r: any) => r.pairs[0].matching_stage.distribution_stage = 'all_stages',
    (r: any) => r.pairs[0].all_stages.percentile.result.query_results[0].query++,
    (r: any) => r.pairs[0].all_stages.percentile.result.query_results[0].less_count++,
    (r: any) => r.pairs[0].distributions[3].histogram.result.underflow_count++,
    (r: any) => r.historical_days.splice(1, 1),
  ])('rejects illegal DTO / broken associations', mutate => { const r = structuredClone(h30); mutate(r); expect(() => validateResult(r)).toThrow() })
  it('rejects changed request identity without recomputing statistics', () => {
    const r = validateResult(h1)
    const q = { ...r.request, metric: 'signed_spread' as const }
    expect(() => validateResult(r, q)).toThrow()
  })
})

it.each(['nohist', 'currentclosed', 'currentexcluded', 'matchingempty'])('accepts real %s business outcome', async name => {
  const r = (await import(`../testing/${name}.json`)).default
  const result = validateResult(r)
  if (name === 'matchingempty') {
    expect(result.pairs[0].matching_stage.status).toBe('empty_sample')
    expect(result.pairs[0].all_stages.percentile).not.toBeNull()
  }
  if (name === 'currentclosed' || name === 'currentexcluded') {
    expect(result.pairs[0].matching_stage.status).toBe('not_applicable')
    expect(result.pairs[0].distributions[3].quantile).not.toBeNull()
  }
})

it.each(['signed_spread', 'annualized_point_spread'])('accepts the backend-selected %s metric without deriving another metric', async metric => {
  const r = (await import(`../testing/${metric}.json`)).default
  expect(validateResult(r).metric).toBe(metric)
})
