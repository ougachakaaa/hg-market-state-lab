import { expect, it } from 'vitest'
import { spawnSync } from 'node:child_process'
it('rejects credentials, private envelopes, machine paths and source maps in the Node gate', () => {
  const result = spawnSync(process.execPath, ['--input-type=module'], { encoding: 'utf8', input: `
    import assert from 'node:assert/strict'
    import { assertNoCredentials, assertPublicAsset } from './scripts/public_asset_safety.mjs'
    for (const text of ['TUSHARE_TOKEN=' + 'x'.repeat(40), 'ghp_' + 'a'.repeat(40)]) assert.throws(() => assertNoCredentials(text))
    for (const [text, name] of [['wp-b-private-static-v1', 'app.js'], ['/home/test/private', 'app.js'], ['{}', 'app.js.map'], ['//# sourceMappingURL=app.map', 'app.js']]) assert.throws(() => assertPublicAsset(text, name))
    assert.doesNotThrow(() => assertPublicAsset('Synthetic Demo', 'app.js'))
  ` })
  expect(result.status, result.stdout + result.stderr).toBe(0)
})
