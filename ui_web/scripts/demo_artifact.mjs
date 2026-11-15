import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { inventory, sha, verifyArtifact } from './artifact_integrity.mjs'
const web = fileURLToPath(new URL('../', import.meta.url))
export function checkoutIdentity() {
  const git = args => execFileSync('git', args, { cwd: web })
  const sourceCommit = git(['rev-parse', 'HEAD']).toString().trim()
  assert.equal(git(['diff', 'HEAD', '--', 'ui_web']).length, 0, 'Source differs from Git')
  const tracked = git(['show', `${sourceCommit}:ui_web/demo/bundles/manifest.json`])
  assert.equal(sha(readFileSync(resolve(web, 'demo/bundles/manifest.json'))), sha(tracked), 'Manifest differs from Git')
  assert.equal(git(['diff', 'HEAD', '--', 'ui_web/demo/bundles', 'ui_web/demo/build/presets.json']).length, 0, 'Dataset differs from Git')
  return { sourceCommit, manifestSha256: sha(tracked) }
}
export function validateDemo(root, expected) {
  assert.match(expected.sourceCommit, /^[a-f0-9]{40}$/)
  assert.match(expected.manifestSha256, /^[a-f0-9]{64}$/)
  const marker = JSON.parse(readFileSync(resolve(root, 'build-complete.json')))
  assert.deepEqual(marker, { format: 'ddb04_static_build_v1', ...expected }, 'Build identity mismatch')
  const files = inventory(root)
  const known = new Set(files.map(file => file.file))
  const html = readFileSync(resolve(root, 'index.html'), 'utf8')
  const refs = [...html.matchAll(/(?:src|href)=["']([^"']+)["']/g)].map(match => match[1])
  assert.ok(refs.length, 'No referenced assets')
  for (const ref of refs) {
    assert.ok(ref.startsWith('/hg-market-state-lab/'), 'Invalid asset base/external reference')
    const path = decodeURIComponent(ref.slice('/hg-market-state-lab/'.length))
    assert.ok(!path.split('/').includes('..') && known.has(path), 'Missing or unsafe referenced asset')
  }
  const dependencies = JSON.parse(readFileSync(resolve(root, 'runtime-dependencies.json')))
  assert.ok(Array.isArray(dependencies) && dependencies.length > 0, 'Missing dependency inventory')
  for (const id of dependencies) {
    assert.equal(typeof id, 'string')
    if (id.includes('node_modules/')) continue
    assert.ok(!/(?:^|\/)(?:tests?|testing|fixtures?)\/|\.fixture|collect(?:or)?|src\/shared\/http\/|src\/app\/(?:auth|App\.)/.test(id), 'Forbidden runtime dependency')
    assert.ok(!/src\/features\/[^/]+\/api\//.test(id) || /\/(validate[^/]*\.ts|[^/]+\.(openapi\.json|generated\.ts))$/.test(id), 'Business HTTP dependency')
    assert.ok(!/src\/features\/[^/]+\/page\//.test(id) || /Presentation\.tsx$/.test(id), 'Online page controller')
    assert.ok(!/\/api\/(auth|backtesting|futuresBasis|research|optionChain|premiumPlane)\.ts|\/hooks\/(useBacktesting|usePreflight|useFuturesBasisResearch|useResearchCatalog|useResearchExplorer)\.ts/.test(id), 'Online controller')
  }
  return files
}
export function scanDemo(root, expected) {
  const files = validateDemo(root, expected)
  const receipt = { format: 'demo_artifact_receipt_v1', ...expected, files, artifactDigest: sha(JSON.stringify(files)) }
  verifyDemo(root, receipt, expected)
  return receipt
}
export function verifyDemo(root, receipt, expected) {
  assert.equal(receipt.format, 'demo_artifact_receipt_v1')
  assert.equal(receipt.sourceCommit, expected.sourceCommit, 'Receipt commit mismatch')
  assert.equal(receipt.manifestSha256, expected.manifestSha256, 'Receipt Manifest mismatch')
  validateDemo(root, expected)
  verifyArtifact(root, receipt)
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [mode, directory, receiptPath] = process.argv.slice(2)
  assert.ok(['scan', 'verify'].includes(mode) && directory && receiptPath, 'Usage: demo_artifact.mjs scan|verify DIRECTORY RECEIPT')
  const root = resolve(directory), receiptFile = resolve(receiptPath)
  assert.ok(!receiptFile.startsWith(root + '/') && !receiptFile.startsWith(root + '\\') && receiptFile !== root, 'Receipt must be outside artifact')
  const expected = checkoutIdentity()
  if (mode === 'scan') {
    const receipt = scanDemo(root, expected)
    mkdirSync(dirname(receiptFile), { recursive: true })
    writeFileSync(receiptFile, JSON.stringify(receipt, null, 2) + '\n')
  } else verifyDemo(root, JSON.parse(readFileSync(receiptFile)), expected)
  console.log(`PASS Demo artifact ${mode}`)
}
