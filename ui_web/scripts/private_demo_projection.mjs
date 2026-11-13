import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { resolve } from 'node:path'
const read = (root, name) => JSON.parse(readFileSync(resolve(root, name), 'utf8'))
const digest = value => createHash('sha256').update(value).digest('hex')
const fileDigest = (root, file) => digest(readFileSync(resolve(root, file)))
// Called only after formal inventory verification by the private builder.
export function projectPrivateExamples(paths, producers) {
  const r2 = read(paths.r2, 'manifest.json'), r3 = read(paths.r3, 'example-index.json'), wpa = read(paths.wpa, 'example-index.json')
  for (const file of ['research/catalog.json', 'research/embedded-publications.json', ...['expiry_to_M1_v1', 'expiry_to_Q1_v1'].flatMap(key => [`w2/${key}-request.json`, `w2/${key}-result.json`, `w2/${key}-evidence.json`])]) assert.equal(fileDigest(paths.wpa, file), wpa.files[file]?.sha256, 'Selected projection differs from verified inventory')
  const examples = {}
  const add = (key, payload, revision, evidenceDigest, inputFingerprint = null) => {
    const json = JSON.stringify(payload)
    examples[key] = { identity: { id: key, revision: 1, delivery: 'static', origin: 'real_market', execution: 'historical_embedded_result', rights: 'private', publicRights: 'BLOCKED', provider: key === 'catalog' ? 'formal_capability_facade' : 'Tushare', producer: producers[key], sourceRevision: revision, inputFingerprint, evidenceDigest, resultDigest: digest(json) }, json }
  }
  for (const key of ['chain', 'premium']) {
    assert.equal(r2.examples[key].classification, 'real_market'); assert.equal(r2.examples[key].provider, 'Tushare'); assert.equal(r2.examples[key].service, producers[key])
    assert.equal(fileDigest(paths.r2, `${key}/response.json`), r2.examples[key].result_sha256)
    add(key, read(paths.r2, `${key}/response.json`), r2.source_revision, fileDigest(paths.r2, 'manifest.json'))
  }
  assert.equal(fileDigest(paths.r3, 'delivery/report-data.json'), r3.result_sha256)
  add('basis', { request: r3.request, report: read(paths.r3, 'delivery/report-data.json') }, r3.source_revision, fileDigest(paths.r3, 'delivery/manifest.json'), r3.input_fingerprint)
  const revision = read(paths.wpa, 'runtime.json').source_revision
  for (const key of ['expiry_to_M1_v1', 'expiry_to_Q1_v1']) add(key, { request: read(paths.wpa, `w2/${key}-request.json`), result: read(paths.wpa, `w2/${key}-result.json`) }, revision, fileDigest(paths.wpa, `w2/${key}-evidence.json`), read(paths.wpa, `w2/${key}-evidence.json`).input_fingerprint)
  const researchRevision = read(paths.wpa, 'research/acceptance.json').source_revision ?? revision
  add('catalog', read(paths.wpa, 'research/catalog.json'), researchRevision, fileDigest(paths.wpa, 'example-index.json'))
  add('publications', read(paths.wpa, 'research/embedded-publications.json'), researchRevision, fileDigest(paths.wpa, 'research/source.json'), read(paths.wpa, 'research/source-reference.json').sha256)
  return { profile: 'wp-b-private-static-v1', examples }
}
