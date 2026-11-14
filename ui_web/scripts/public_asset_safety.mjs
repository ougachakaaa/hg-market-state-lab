import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
const repository = fileURLToPath(new URL('../../', import.meta.url))
const sha = value => createHash('sha256').update(value).digest('hex')
const reviewed = JSON.parse(readFileSync(new URL('./public_payload_inventory.json', import.meta.url)))
export function assertNoCredentials(text) {
  assert.ok(!/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/.test(text), 'Private key')
  assert.ok(!/\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{70,}|AKIA[A-Z0-9]{16})\b/.test(text), 'Credential token')
  assert.ok(!/(?:TUSHARE_TOKEN|LAB_AUTH_JWT_SECRET)\s*[=:]\s*["']?[A-Za-z0-9_-]{32,}/.test(text), 'Runtime credential literal')
}
export function assertPublicAsset(text, name) {
  assertNoCredentials(text)
  assert.ok(!/\.map$/.test(name) && !/sourceMappingURL\s*=/.test(text), 'Source map in public artifact')
  assert.ok(!/wp-b-private-static-v1|d3-r2-private-mo-v1|wp-a-private-example-index-v1|historical_embedded_result/.test(text), 'Private envelope in public artifact')
  assert.ok(!/\/home\/|\/Users\/|[A-Z]:\\Users\\/.test(text), 'Private machine path')
}
export function checkPublicSafety() {
  const tracked = execFileSync('git', ['ls-files', '-z'], { cwd: repository, encoding: 'utf8' }).split('\0').filter(Boolean)
  for (const path of tracked) {
    const bytes = readFileSync(resolve(repository, path))
    assertNoCredentials(bytes.toString('utf8'))
    if (/\.(?:jsonl?|csv|sqlite3?|db|parquet|zip|gz)$/.test(path)) {
      const specializedConfig = /^ui_web\/tests\/config\/tsconfig\.(?:shell|option-chain|premium|catalog|explorer|futures-basis|backtesting)\.json$/.test(path)
      const config = specializedConfig || path === 'ui_web/scripts/public_payload_inventory.json' || /^ui_web\/(?:package(?:-lock)?|tsconfig[^/]*|\.oxlintrc)\.json$/.test(path) || /\.openapi\.json$/.test(path)
      if (!config) assert.equal(sha(bytes), reviewed[path], `Unreviewed or changed payload: ${path}`)
    }
  }
  for (const path of Object.keys(reviewed)) assert.ok(tracked.includes(path), `Stale reviewed payload: ${path}`)
  console.log(JSON.stringify({ status: 'PASS', trackedFiles: tracked.length, reviewedPayloads: Object.keys(reviewed).length }))
}
if (process.argv[1] === fileURLToPath(import.meta.url)) checkPublicSafety()
