import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync, mkdirSync, rmSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { resolve } from 'node:path'
import { scanDemo, verifyDemo } from './demo_artifact.mjs'
const identity = { sourceCommit: 'a'.repeat(40), manifestSha256: 'b'.repeat(64) }
test('Demo receipt binds identity, references, isolation and every artifact byte', () => {
  const root = mkdtempSync(resolve(tmpdir(), 'ddb05-'))
  try {
    mkdirSync(resolve(root, 'assets'))
    const original = {
      'index.html': '<script src="/hg-market-state-lab/assets/app.js"></script>',
      'assets/app.js': 'console.log("study")',
      'build-complete.json': JSON.stringify({ format: 'ddb04_static_build_v1', ...identity }),
      'runtime-dependencies.json': JSON.stringify(['ui_web/demo/runtime/main.tsx']),
    }
    const reset = () => { for (const [name, bytes] of Object.entries(original)) writeFileSync(resolve(root, name), bytes) }
    reset()
    const receipt = scanDemo(root, identity)
    verifyDemo(root, receipt, identity)
    assert.throws(() => verifyDemo(root, receipt, { ...identity, sourceCommit: 'c'.repeat(40) }))
    assert.throws(() => verifyDemo(root, receipt, { ...identity, manifestSha256: 'c'.repeat(64) }))
    for (const [name, bytes] of [
      ['assets/app.js', 'mutation'],
      ['assets/app.js', 'ghp_' + 'a'.repeat(40)],
      ['assets/app.js', '/home/user/private'],
      ['index.html', '<script src="/wrong/app.js"></script>'],
      ['index.html', '<script src="/hg-market-state-lab/assets/missing.js"></script>'],
      ['runtime-dependencies.json', JSON.stringify(['ui_web/src/features/backtesting/api/client.ts'])],
      ['runtime-dependencies.json', JSON.stringify(['ui_web/tests/fixture.ts'])],
      ['build-complete.json', '{}'],
    ]) {
      reset(); writeFileSync(resolve(root, name), bytes)
      assert.throws(() => verifyDemo(root, receipt, identity))
      if (name !== 'assets/app.js' || bytes !== 'mutation') assert.throws(() => scanDemo(root, identity))
    }
    reset()
    for (const name of ['extra.js', 'app.js.map', 'fixture.json', 'private.sqlite']) {
      writeFileSync(resolve(root, name), '{}')
      assert.throws(() => verifyDemo(root, receipt, identity))
      if (name !== 'extra.js') assert.throws(() => scanDemo(root, identity))
      rmSync(resolve(root, name))
    }
    rmSync(resolve(root, 'assets/app.js'))
    assert.throws(() => verifyDemo(root, receipt, identity))
  } finally { rmSync(root, { recursive: true, force: true }) }
})
