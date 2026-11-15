import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readdirSync, lstatSync, readFileSync } from 'node:fs'
import { resolve, relative } from 'node:path'
import { assertNoCredentials } from './public_asset_safety.mjs'
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
  assert.ok(lstatSync(root).isDirectory() && !lstatSync(root).isSymbolicLink(), 'Artifact root symlink/non-directory')
  visit(root)
  return files.sort((a,b) => a.file.localeCompare(b.file, 'en'))
}
export function assertDemoAsset(bytes, name) {
  const text = bytes.toString('utf8')
  assertNoCredentials(text)
  assert.ok(!name.split('/').some(part => part.startsWith('.')), 'Hidden artifact file')
  assert.ok(/\.(?:html|js|css|json|svg|png|ico|woff2?|ttf)$/.test(name), 'Illegal artifact file type')
  assert.ok(!/(?:^|\/)(?:tests?|fixtures?)(?:\/|\.)|\.fixture\./i.test(name), 'Test fixture')
  assert.ok(!/\.map$|\.(?:sqlite3?|db|parquet)$/.test(name), 'Source map/database')
  assert.ok(!/sourceMappingURL\s*=|\/home\/|\/Users\/|[A-Z]:\\Users\\/.test(text), 'Source map/private path')
  assert.ok(!/TUSHARE_TOKEN|LAB_AUTH_JWT_SECRET|LAB_RESEARCH_PUBLICATION_ROOT/.test(text), 'Runtime configuration')
}
export function verifyArtifact(root, receipt) {
  const files = inventory(root)
  assert.deepEqual(files, receipt.files, 'Artifact changed after scan')
  assert.equal(sha(JSON.stringify(files)), receipt.artifactDigest, 'Artifact digest mismatch')
  for (const file of files) assertDemoAsset(readFileSync(resolve(root, file.file)), file.file)
}
