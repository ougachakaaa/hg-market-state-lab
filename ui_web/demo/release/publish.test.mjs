import { test } from 'node:test'
import assert from 'node:assert/strict'
import { prePushPolicy, checkedPush, verifyPublicFiles, cleanupCheckout, assertCleanupPaths, finishCleanup, checkoutArgs } from './publish.mjs'
import { mkdtemp, rm, access } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, win32 } from 'node:path'
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

test('normalizes Windows separators but rejects cleanup outside its invocation', () => {
  assertCleanupPaths({ common: 'C:/repo/.git', temporary: 'C:\\repo\\.git\\demo-publish-test', worktree: 'C:/repo/.git/demo-publish-test/checkout' }, win32)
  assert.throws(() => assertCleanupPaths({ common: 'C:/repo/.git', temporary: 'C:/outside/demo-publish-test', worktree: 'C:/outside/demo-publish-test/checkout' }, win32))
  assert.throws(() => assertCleanupPaths({ common: 'C:/repo/.git', temporary: 'C:/repo/.git/demo-publish-test', worktree: 'C:/repo/user-work' }, win32))
})
test('cleanup reports independently without replacing an original failure or successful acceptance', async () => {
  let warning
  const primary = new Error('download timed out')
  await assert.rejects(async () => {
    try { throw primary } finally { await finishCleanup(async () => { throw Error('cleanup denied') }, error => { warning = error.message }) }
  }, error => error === primary)
  assert.equal(warning, 'cleanup denied')
  await finishCleanup(async () => { throw Error('cleanup denied') }, () => {})
})
test('isolated checkout preserves blob bytes under autocrlf=true without changing repository configuration', async () => {
 const directory = await mkdtemp(join(tmpdir(), 'demo-lf-test-'))
 const git = args => execFileSync('git', args, { cwd: directory, stdio: 'pipe' })
 try {
  git(['init']); git(['config', 'core.autocrlf', 'true'])
  const { writeFile, readFile } = await import('node:fs/promises')
  await writeFile(join(directory, 'payload.json'), '{}\n')
  git(['add', 'payload.json']); git(['-c','user.name=test','-c','user.email=test@example.invalid','commit','-m','test'])
  const checkout = join(directory, 'with spaces')
  git(checkoutArgs(checkout, 'HEAD'))
  assert.deepEqual(await readFile(join(checkout, 'payload.json')), git(['show','HEAD:payload.json']))
  assert.equal(git(['config','core.autocrlf']).toString().trim(), 'true')
  await cleanupCheckout(checkout, () => git(['worktree','remove','--force',checkout]))
 } finally { await rm(directory,{recursive:true,force:true}) }
})
