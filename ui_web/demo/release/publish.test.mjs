import { test } from 'node:test'
import assert from 'node:assert/strict'
import { prePushPolicy, checkedPush, verifyOnline } from './publish.mjs'
const candidate = 'a'.repeat(40)
const valid = { candidate, main: candidate, release: 'b'.repeat(40), ancestor: true, dirty: '', localMain: candidate, active: false }
test('accept exact main and FF release', () => prePushPolicy(valid))
for (const [name, changes] of Object.entries({ nonMain: { main: 'c'.repeat(40) }, divergent: { ancestor: false }, dirty: { dirty: ' M ui_web/a' }, drift: { localMain: 'c'.repeat(40) }, concurrent: { active: true } })) {
  test(`reject ${name}`, () => assert.throws(() => prePushPolicy({ ...valid, ...changes })))
}
test('no push on gate, evidence or remote recheck failure', async () => {
  for (const failure of ['gate', 'evidence', 'remote']) {
    let pushes = 0
    await assert.rejects(checkedPush({ check: async () => { if (failure === 'gate') throw Error('failed'); return { result: failure === 'evidence' ? 'FAIL' : 'PASS' } }, recheck: async () => { if (failure === 'remote') throw Error('changed') }, push: async () => { pushes++ } }))
    assert.equal(pushes, 0)
  }
})
test('push follows successful gate and remote recheck', async () => {
  const order = []
  await checkedPush({ check: async () => { order.push('gate'); return { result: 'PASS' } }, recheck: async () => { order.push('refs') }, push: async () => { order.push('push') } })
  assert.deepEqual(order, ['gate', 'refs', 'push'])
})
test('online acceptance rejects tampered bytes', async () => {
  const original = globalThis.fetch
  globalThis.fetch = async () => new Response('tampered')
  try { await assert.rejects(verifyOnline('https://example.com/', { files: [{ file: 'index.html', size: 8, sha256: '0'.repeat(64) }] }), /hash mismatch/) }
  finally { globalThis.fetch = original }
})
