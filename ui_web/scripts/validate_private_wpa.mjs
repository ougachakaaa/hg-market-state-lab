import assert from 'node:assert/strict'
import { readFileSync, realpathSync } from 'node:fs'
import { isAbsolute, relative, resolve, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createServer } from 'vite'

const web = fileURLToPath(new URL('..', import.meta.url))
assert.ok(process.argv[2] && isAbsolute(process.argv[2]), 'External absolute package path required')
const root = realpathSync(process.argv[2])
assert.ok(relative(resolve(web, '..'), root).startsWith('..' + sep), 'Private package must be external')
const stage = process.argv[3]
assert.ok(['w2', 'research'].includes(stage), 'Explicit validation stage required')
const read = name => JSON.parse(readFileSync(resolve(root, name), 'utf8'))
const server = await createServer({ root: web, logLevel: 'silent', configFile: false, server: { middlewareMode: true }, appType: 'custom' })
try {
  let negativeChecks = 0
  if (stage === 'w2') {
    const { validateEmbeddedBacktestResult: validate } = await server.ssrLoadModule('/src/features/backtesting/api/validateResult.ts')
    for (const profile of ['expiry_to_M1_v1', 'expiry_to_Q1_v1']) {
      const payload = { request: read(`w2/${profile}-request.json`), result: read(`w2/${profile}-result.json`) }
      assert.equal(validate(payload).result, payload.result)
      assert.deepEqual(payload.request, { case: 'futures_roll_long_v1', product_code: 'IM', start_date: '2026-01-01', end_date: '2026-11-11', strategy_profile: profile })
      for (const mutate of [
        p => { p.result.profile = 'unsupported' },
        p => { p.request.end_date = '2026-11-10' },
        p => { delete p.result.views.returns },
        p => { p.request.strategy_profile = profile === 'expiry_to_M1_v1' ? 'expiry_to_Q1_v1' : 'expiry_to_M1_v1' },
      ]) {
        const invalid = structuredClone(payload)
        mutate(invalid)
        assert.throws(() => validate(invalid))
        negativeChecks++
      }
    }
  } else {
    const { validateEmbeddedPublicationSet: validate } = await server.ssrLoadModule('/src/features/research_explorer/api/validateEmbeddedPublication.ts')
    const payload = read('research/embedded-publications.json')
    const validated = validate(payload)
    assert.equal(validated.publicationIds.size, 1)
    assert.equal(payload.manifests.length, 1)
    const manifest = payload.manifests[0]
    assert.deepEqual(manifest.scope.subjects, ['000852.SH'])
    assert.deepEqual(manifest.scope.horizons, [20, 60])
    assert.deepEqual(manifest.scope.windows, [{ start_date: '2026-01-01', end_date: '2026-11-11' }])
    assert.equal(payload.analyses.length, manifest.analyses.length)
    assert.equal(payload.views.length, manifest.analyses.reduce((n, a) => n + a.views.length, 0))
    assert.ok(payload.views.length > 0)
    for (const mutate of [
      p => { p.analyses[0].publication_id = 'unlisted' },
      p => { p.views[0].view_id = 'unpublished' },
      p => { p.manifests[0].jobs[0].analyses.push('unpublished') },
    ]) {
      const invalid = structuredClone(payload)
      mutate(invalid)
      assert.throws(() => validate(invalid))
      negativeChecks++
    }
    const { validateEmbeddedCatalog } = await server.ssrLoadModule('/src/features/research_catalog/api/validateCatalog.ts')
    const catalog = read('research/catalog.json')
    const result = validateEmbeddedCatalog(catalog)
    assert.equal(result.capabilities.length, 1)
    assert.deepEqual(catalog.list, catalog.details)
    assert.equal(catalog.list[0].id, 'trailing_cumulative_return_v1')
    assert.equal(catalog.list[0].status, 'supported')
    assert.equal(catalog.list[0].live_readiness, 'not_probed')
    const invalid = structuredClone(catalog)
    invalid.details[0].id = 'unlisted'
    assert.throws(() => validateEmbeddedCatalog(invalid))
    negativeChecks++
  }
  console.log(JSON.stringify({ status: 'PASS', stage, negative_checks: negativeChecks, payload_preserved: true }))
} finally {
  await server.close()
}
