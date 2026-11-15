import { test } from 'node:test'
import assert from 'node:assert/strict'
import { prePushPolicy, checkedPush, verifyPublicFiles, cleanupCheckout } from './publish.mjs'
import { mkdtemp, rm, access } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'
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
  await assert.rejects(verifyPublicFiles({ files: [{ file: 'index.html', size: 8, sha256: '0'.repeat(64) }] }, async () => ({ size: 8, sha256: '1'.repeat(64) })), /hash mismatch/)
})
test('online acceptance rejects missing files and changed sizes', async () => {
  const receipt = { files: [{ file: 'index.html', size: 8, sha256: '0'.repeat(64) }] }
  await assert.rejects(verifyPublicFiles(receipt, async () => { throw Error('unavailable') }), /unavailable/)
  await assert.rejects(verifyPublicFiles(receipt, async () => ({ size: 7, sha256: '0'.repeat(64) })), /size mismatch/)
})
test('removes owned checkout before unregistering its real Git worktree', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'demo-cleanup-test-'))
  const git = args => execFileSync('git', args, { cwd: directory, stdio: 'pipe' })
  try {
    git(['init'])
    git(['-c', 'user.name=test', '-c', 'user.email=test@example.invalid', 'commit', '--allow-empty', '-m', 'test'])
    const checkout = join(directory, 'checkout')
    git(['worktree', 'add', '--detach', checkout])
    await cleanupCheckout(checkout, () => git(['worktree', 'remove', '--force', checkout]))
    await assert.rejects(access(checkout))
    assert.ok(!git(['worktree', 'list', '--porcelain']).toString().includes('/checkout'))
  } finally { await rm(directory, { recursive: true, force: true }) }
})
