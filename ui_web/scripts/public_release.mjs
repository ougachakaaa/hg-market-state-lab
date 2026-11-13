import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, lstatSync, existsSync } from 'node:fs'
import { resolve, relative } from 'node:path'
import { fileURLToPath } from 'node:url'
import { assertNoCredentials } from './public_asset_safety.mjs'
export const web = fileURLToPath(new URL('../', import.meta.url))
export const repository = resolve(web, '..')
export const packageRoot = resolve(web, 'src/demo/public/examples')
export const output = resolve(web, 'dist-demo-public')
export const sha = bytes => createHash('sha256').update(bytes).digest('hex')
export function inventory(root) {
  const files = []
  function visit(dir) {
    for (const name of readdirSync(dir).sort()) {
      const path = resolve(dir, name), stat = lstatSync(path)
      assert.ok(!stat.isSymbolicLink(), 'Artifact/input symlink')
      if (stat.isDirectory()) visit(path)
      else { assert.ok(stat.isFile(), 'Nonregular file'); const bytes = readFileSync(path); files.push({ file: relative(root, path).replaceAll('\\', '/'), size: bytes.length, sha256: sha(bytes) }) }
    }
  }
  visit(root)
  return files.sort((a,b) => a.file.localeCompare(b.file, 'en'))
}
export function assertPublicV2Asset(bytes, name) {
  const text = bytes.toString('utf8')
  assertNoCredentials(text)
  assert.ok(!/\.map$|\.(?:sqlite3?|db|parquet)$/.test(name), 'Source map/database')
  assert.ok(!/sourceMappingURL\s*=|\/home\/|\/Users\/|[A-Z]:\\Users\\/.test(text), 'Source map/private path')
  assert.ok(!/wp-b-private-static-v1|d3-r2-private-mo-v1|wp-a-private-example-index-v1/.test(text), 'Private package')
  assert.ok(!/TUSHARE_TOKEN|LAB_AUTH_JWT_SECRET|LAB_RESEARCH_PUBLICATION_ROOT/.test(text), 'Runtime configuration')
}
export function loadPublicPackage() {
  const path = resolve(packageRoot, 'package.json')
  assert.ok(existsSync(path), 'BLOCKED: no independently reviewed public V2 package; existing V1 remains live')
  const tracked = new Set(execFileSync('git', ['ls-files', '-z'], { cwd: repository, encoding: 'utf8' }).split('\0'))
  const envelope = JSON.parse(readFileSync(path, 'utf8'))
  const expected = new Set(['README.md', 'package.json'])
  for (const record of Object.values(envelope.examples ?? {})) {
    for (const gate of Object.values(record.review?.gates ?? {})) {
      assert.ok(/^evidence\/[a-zA-Z0-9_/-]+\.md$/.test(gate.evidence) && !gate.evidence.includes('..'), 'Unsafe evidence path')
      expected.add(gate.evidence)
      assert.equal(sha(readFileSync(resolve(packageRoot, gate.evidence))), gate.evidenceDigest, 'Review evidence digest mismatch')
    }
  }
  const files = inventory(packageRoot)
  assert.deepEqual(files.map(f=>f.file).sort(), [...expected].sort(), 'Unreviewed package file')
  for (const file of files) {
    assert.ok(tracked.has(relative(repository, resolve(packageRoot, file.file))), 'Public input must be tracked')
    assertPublicV2Asset(readFileSync(resolve(packageRoot, file.file)), file.file)
  }
  return { envelope, files }
}
export function verifyArtifact(root, receipt) {
  const files = inventory(root)
  assert.deepEqual(files, receipt.files, 'Artifact changed after scan')
  assert.equal(sha(JSON.stringify(files)), receipt.artifactDigest, 'Artifact digest mismatch')
  for (const file of files) assertPublicV2Asset(readFileSync(resolve(root, file.file)), file.file)
}
