import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { readFileSync, readdirSync, lstatSync } from 'node:fs'
import { resolve, relative } from 'node:path'
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
  assert.ok(!/2026-11-11/.test(text), 'Uncleared V2 observation/window in V1 artifact')
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
      const config = path === 'ui_web/scripts/public_payload_inventory.json' || /^ui_web\/(?:package(?:-lock)?|tsconfig[^/]*|\.oxlintrc)\.json$/.test(path) || /\.openapi\.json$/.test(path)
      if (!config) assert.equal(sha(bytes), reviewed[path], `Unreviewed or changed payload: ${path}`)
    }
  }
  for (const path of Object.keys(reviewed)) assert.ok(tracked.includes(path), `Stale reviewed payload: ${path}`)
  const config = readFileSync(resolve(repository, 'ui_web/vite.demo.config.ts'), 'utf8')
  assert.ok(config.includes('./src/demo/futures_basis') && config.includes('publicDir: false'))
  assert.ok(!/private|process\.env/.test(config), 'Public build input boundary')
  const workflow = readFileSync(resolve(repository, '.github/workflows/deploy-demo-pages.yml'), 'utf8')
  assert.ok(workflow.includes('path: ui_web/dist-demo-public/site'))
  assert.ok(!/demo:build:private|private_demo|--r2|--wpa|TUSHARE_TOKEN/.test(workflow), 'Private deployment path')
  const root = resolve(repository, 'ui_web/dist-demo')
  const files = []
  function scan(dir) {
    for (const item of readdirSync(dir, { withFileTypes: true })) {
      const path = resolve(dir, item.name)
      assert.ok(!lstatSync(path).isSymbolicLink(), 'Artifact symlink')
      if (item.isDirectory()) scan(path)
      else { const text = readFileSync(path, 'utf8'); assertPublicAsset(text, path); files.push({ file: relative(root, path), sha256: sha(text), text }) }
    }
  }
  scan(root)
  const fixture = readFileSync(resolve(repository, 'ui_web/src/demo/futures_basis/report.v1.json'), 'utf8').trim()
  assert.ok(files.some(file => file.text.includes(fixture) || file.text.includes(JSON.stringify(fixture).slice(1, -1))), 'Original V1 synthetic fixture absent')
  assert.ok(files.some(file => file.text.includes('Synthetic Demo')), 'Synthetic disclosure absent')
  console.log(JSON.stringify({ status: 'PASS', trackedFiles: tracked.length, reviewedPayloads: Object.keys(reviewed).length, files: files.map(({text: _text, ...file}) => file) }, null, 2))
}
if (process.argv[1] === fileURLToPath(import.meta.url)) checkPublicSafety()
