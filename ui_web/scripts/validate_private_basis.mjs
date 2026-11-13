import assert from 'node:assert/strict'
import { readFileSync, realpathSync } from 'node:fs'
import { isAbsolute, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

// Explicit local verification only; never an input to a public build. Research's
// official verify/replay commands own evidence integrity and scientific replay.
const root = fileURLToPath(new URL('..', import.meta.url))
assert.ok(process.argv[2] && isAbsolute(process.argv[2]), 'External absolute delivery path required')
const delivery = realpathSync(process.argv[2])
const repository = realpathSync(resolve(root, '..'))
const location = relative(repository, delivery)
assert.ok(location.startsWith('..' + sep) || isAbsolute(location), 'Delivery must be outside repository')
const read = name => JSON.parse(readFileSync(resolve(delivery, name), 'utf8'))
const report = read('report-data.json')
const request = {
  case: 'futures_basis_v1', product_code: 'IM', start_date: '2026-01-01',
  end_date: '2026-11-11', analysis_profile: 'r01a_standard_v1',
}
const server = await createServer({ root, logLevel: 'silent', configFile: false, server: { middlewareMode: true }, appType: 'custom' })
try {
  const { validateEmbeddedReport } = await server.ssrLoadModule('/src/features/futures_basis_research/api/validateResult.ts')
  const validated = validateEmbeddedReport({ request, report })
  assert.equal(validated.report, report)
  assert.equal(validated.request, request)
  assert.equal(report.definition_version, 'futures_basis_definition_v1')
  assert.equal(report.request.quantile.method, 'quantile')
  assert.deepEqual(report.request.histograms.map(h => h.method), Array(3).fill('interval_count'))
  assert.deepEqual(report.request.quantile.points, [0, .25, .5, .75, 1])
  assert.deepEqual(report.request.histograms.map(h => [h.unit, h.edges]), [
    ['index_points', [-1000, -500, -100, 0, 100, 500, 1000]],
    ['decimal_ratio', [-1, -.1, -.01, 0, .01, .1, 1]],
    ['decimal_ratio', [-10, -1, -.1, 0, .1, 1, 10]],
  ])
  assert.equal(report.fingerprint, read('manifest.json').input_fingerprint)
  assert.deepEqual(report.views, read('views.json'))
  assert.ok(report.summary && report.sources && report.formulas.length && report.limitations.length)
  assert.equal(report.distributions.length, 12)
  assert.equal(report.comparisons.length, 18)
  assert.deepEqual(report.persistence.map(p => p.slot), ['M0', 'M1', 'Q1', 'Q2'])
  assert.equal(Object.keys(report.views.history).length, 3)
  // Negative probes exercise the same published validator, never a second
  // financial validator or an HTTP Run envelope.
  for (const change of [
    p => { p.request.end_date = '2026-11-10' },
    p => { p.request.analysis_profile = 'unsupported' },
    p => { p.report.profile = 'unsupported' },
    p => { p.report.status = 'FAILED' },
    p => { p.report.views.history.basis_value.version = 99 },
    p => { delete p.report.persistence },
  ]) {
    const invalid = structuredClone({ request, report })
    change(invalid)
    assert.throws(() => validateEmbeddedReport(invalid))
  }
  console.log(JSON.stringify({
    status: 'PASS', request, profile: report.profile, definition_version: report.definition_version,
    report_status: report.status, fingerprint: report.fingerprint, payload_preserved: true,
    sections: ['Overview', 'Historical Basis', 'Distributions', 'Term Structure', 'Discount Persistence', 'Evidence / Limitations'],
    distributions: report.distributions.length, comparisons: report.comparisons.length,
    history_views: Object.keys(report.views.history).length,
    histogram_views: Object.keys(report.views.histograms).length, negative_checks: 6,
  }))
} finally {
  await server.close()
}
