import { projectPrivateExamples } from './private_demo_projection.mjs'
import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, mkdirSync, writeFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { build, createServer } from 'vite'
import react from '@vitejs/plugin-react'
import { parsePrivateArgs, web, repository } from './private_demo_boundary.mjs'
import { privateDemoIsolation } from './private_demo_isolation.mjs'

const paths = parsePrivateArgs(process.argv.slice(2))
const read = (root, name) => JSON.parse(readFileSync(resolve(root, name), 'utf8'))
const digest = value => createHash('sha256').update(value).digest('hex')
const fileDigest = (root, file) => digest(readFileSync(resolve(root, file)))
const receipts = []
// Fixed read-only operations. Formal offline replay belongs to admission, before bundling.
for (const [script, args] of [
  ['ui_web/scripts/private_mo_examples.py', ['verify', '--output', paths.r2]],
  ['market_research/scripts/futures_basis_report.py', ['verify', resolve(paths.r3, 'delivery')]],
  ['market_research/scripts/futures_basis_report.py', ['replay', resolve(paths.r3, 'delivery')]],
  ['ui_web/scripts/private_wpa_examples.py', ['verify', '--output', paths.wpa]],
]) {
  console.log(`Verifying ${script} ${args[0]}`)
  const stdout = execFileSync(resolve(repository, '.venv/bin/python'), [resolve(repository, script), ...args], { cwd: repository, encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 })
  receipts.push({ script, operation: args[0], status: 'PASS', receiptDigest: digest(stdout) })
}
const r2 = read(paths.r2, 'manifest.json'), r3 = read(paths.r3, 'example-index.json'), wpa = read(paths.wpa, 'example-index.json')
for (const index of [r2, r3, wpa]) { assert.equal(index.classification, 'real_market'); assert.equal(index.publication_rights, 'BLOCKED') }
assert.equal(r2.profile, 'd3-r2-private-mo-v1'); assert.equal(r2.example_revision, 1)
assert.equal(r3.example_profile, 'd3-r3-private-basis-v1'); assert.equal(r3.revision, 1)
assert.equal(wpa.profile, 'wp-a-private-example-index-v1'); assert.equal(wpa.revision, 1)
assert.equal(fileDigest(paths.r3, 'example-index.json'), readFileSync(resolve(paths.r3, 'example-index.sha256'), 'utf8').trim().split(/\s+/)[0])
for (const [root, manifest] of [[paths.r2, 'manifest.json'], [paths.r3, 'example-index.json']]) {
  const prior = wpa.prior_examples.find(p => p.manifest === manifest)
  assert.ok(prior && prior.sha256 === fileDigest(root, manifest), 'Explicit package does not match accepted WP-A reference')
}
const server = await createServer({ root: web, configFile: false, logLevel: 'silent', server: { middlewareMode: true }, appType: 'custom' })
let envelope
try {
  const { producers, admitPrivateEnvelope } = await server.ssrLoadModule('/src/demo/private/admission.ts')
  envelope = projectPrivateExamples(paths, producers)
  await admitPrivateEnvelope(envelope)
} finally { await server.close() }
// Static bundling only: no Python, evidence lookup, market I/O or calculation below.
const serialized = JSON.stringify(envelope)
for (const root of [paths.r2, paths.r3, paths.wpa, repository]) assert.ok(!serialized.includes(root), 'Private absolute path in browser projection')
assert.ok(!/TUSHARE_TOKEN|LAB_AUTH_|\/home\/|[A-Z]:\\\\Users\\\\/.test(serialized), 'Sensitive metadata in browser projection')
// Vite SSR sets NODE_ENV=development. Explicitly restore production before JSX
// compilation so no jsxDEV source filename metadata can enter browser assets.
process.env.NODE_ENV = 'production'
mkdirSync(paths.output, { mode: 0o700 })
await build({ configFile: false, root: resolve(web, 'src/demo/private'), base: './', publicDir: false, envDir: false, plugins: [react(), {
  name: 'explicit-private-results',
  resolveId(id) { if (id === 'virtual:private-examples') return '\0private-examples' },
  load(id) { if (id === '\0private-examples') return `export default ${serialized}` },
}, privateDemoIsolation()], build: { outDir: resolve(paths.output, 'site'), emptyOutDir: false, sourcemap: false } })
const files = []
const scan = dir => { for (const entry of readdirSync(dir, { withFileTypes: true })) { const path = resolve(dir, entry.name); if (entry.isDirectory()) scan(path); else {
  const content = readFileSync(path, 'utf8')
  for (const privatePath of [repository, paths.r2, paths.r3, paths.wpa, paths.output]) assert.ok(!content.includes(privatePath), 'Private absolute path in emitted asset')
  assert.ok(!/\/home\/|[A-Z]:\\\\Users\\\\/.test(content), 'Personal source path in emitted asset')
  files.push({ file: path.slice(paths.output.length + 1), sha256: fileDigest(dir, entry.name) })
} } }
scan(resolve(paths.output, 'site'))
writeFileSync(resolve(paths.output, 'admission.json'), JSON.stringify({ status: 'PASS', profile: envelope.profile, sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: repository, encoding: 'utf8' }).trim(), node: process.version, npmLockDigest: fileDigest(web, 'package-lock.json'), receipts, identities: Object.values(envelope.examples).map(e => e.identity), files, publicRights: 'BLOCKED' }, null, 2))
console.log('PASS: verified private seven-page static build; Publication Rights BLOCKED')
