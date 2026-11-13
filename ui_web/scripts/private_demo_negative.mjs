import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { createServer } from 'vite'
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { projectPrivateExamples } from './private_demo_projection.mjs'
import { parsePrivateArgs, web, externalPath } from './private_demo_boundary.mjs'

const paths = parsePrivateArgs(process.argv.slice(2))
const server = await createServer({ root: web, logLevel: 'silent', configFile: false, server: { middlewareMode: true }, appType: 'custom' })
const checks = []
const pass = label => { checks.push(label); console.log(`PASS: ${label}`) }
try {
  const { producers, admitPrivateEnvelope, validateIdentity } = await server.ssrLoadModule('/src/demo/private/admission.ts')
  const original = projectPrivateExamples(paths, producers)
  await admitPrivateEnvelope(original)
  for (const [label, mutate] of [
    ['Wrong Date', p => { p.chain.target_trade_date = '2026-11-10' }],
    ['Wrong Strategy Profile', p => { p.expiry_to_M1_v1.request.strategy_profile = 'expiry_to_Q1_v1' }],
    ['Basis Fingerprint Mismatch', p => { p.basis.report.fingerprint = '0'.repeat(64) }],
    ['Missing Premium Points', p => { p.premium.points.pop() }],
    ['Missing Basis View', p => { delete p.basis.report.views.history.basis_value }],
    ['Publication Foreign ID', p => { p.publications.analyses[0].publication_id = 'foreign' }],
    ['Publication Unlisted View', p => { p.publications.views[0].view_id = 'unlisted' }],
    ['Missing Referenced Detail', p => { p.publications.views.pop() }],
  ]) {
    const broken = structuredClone(original)
    const payloads = Object.fromEntries(Object.entries(broken.examples).map(([k, e]) => [k, JSON.parse(e.json)]))
    mutate(payloads)
    for (const [key, payload] of Object.entries(payloads)) {
      broken.examples[key].json = JSON.stringify(payload)
      broken.examples[key].identity.resultDigest = createHash('sha256').update(broken.examples[key].json).digest('hex')
    }
    await assert.rejects(() => admitPrivateEnvelope(broken)); pass(label)
  }
  for (const [label, mutate] of [
    ['Result Digest Mismatch', e => { e.examples.chain.json += ' ' }],
    ['Synthetic Illegally Promoted', e => { e.examples.basis.identity.origin = 'synthetic' }],
    ['Incomplete Identity', e => { delete e.examples.catalog.identity.evidenceDigest }],
    ['Wrong Example Identity', e => { e.examples.chain.identity.id = 'premium' }],
    ['Wrong Producer', e => { e.examples.publications.identity.producer = 'mock' }],
    ['Wrong Rights', e => { e.examples.premium.identity.rights = 'cleared_public' }],
    ['Missing Example', e => { delete e.examples.expiry_to_Q1_v1 }],
  ]) {
    const broken = structuredClone(original); mutate(broken)
    await assert.rejects(() => admitPrivateEnvelope(broken)); pass(label)
  }
  assert.throws(() => validateIdentity({ ...original.examples.chain.identity, delivery: 'production' }, 'chain')); pass('Delivery separated from origin')
  assert.throws(() => externalPath(resolve(paths.output, 'missing-package'))); pass('Missing Private Package')
  assert.throws(() => externalPath(resolve(web, '.build/tests/v1'))); pass('Private Data Routed to Public Build')
  assert.throws(() => externalPath('relative/path')); pass('Relative Input Rejected')
  mkdirSync(paths.output, { mode: 0o700 })
  writeFileSync(resolve(paths.output, 'negative.json'), JSON.stringify({ status: 'PASS', checks }, null, 2))
} finally { await server.close() }
