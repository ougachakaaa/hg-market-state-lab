import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { mkdir, mkdtemp, rm, lstat, rmdir } from 'node:fs/promises'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { execute, journal } from './execution.mjs'
import { verifyRelease } from './verifyRelease.mjs'
const web = fileURLToPath(new URL('../../', import.meta.url))
const root = dirname(web.replace(/[\\/]$/, ''))
const releaseRef = 'refs/heads/release/demo-pages'
export function prePushPolicy({ candidate, main, release, ancestor, dirty, localMain, active }) {
  assert.match(candidate, /^[a-f0-9]{40}$/)
  assert.equal(candidate, main, 'Candidate must be remote main')
  assert.ok(!dirty, 'Uncommitted relevant changes')
  assert.ok(!localMain || localMain === main, 'Local/remote main drift')
  assert.ok(!release || ancestor, 'Non-fast-forward release')
  assert.ok(!active, 'Concurrent or uncertain release')
}
export async function checkedPush({ check, recheck, push }) {
  const evidence = await check()
  assert.equal(evidence.result, 'PASS', 'Release Gate failed')
  await recheck()
  await push()
  return evidence
}
export function assertCleanupPaths({ worktree, temporary, common }, paths = { resolve, dirname }) {
  const base = paths.resolve(common), parent = paths.resolve(temporary), child = paths.resolve(worktree)
  assert.equal(paths.dirname(parent), base, 'Unsafe temporary cleanup')
  assert.equal(paths.dirname(child), parent, 'Unsafe checkout cleanup')
  assert.ok(paths.dirname(parent) !== parent && /demo-publish-[^\\/]+$/.test(parent), 'Unowned temporary directory')
}
export async function finishCleanup(clean, report) {
  try { await clean() } catch (error) { report(error) }
}
export function checkoutArgs(worktree, candidate) {
  return ['-c', 'core.autocrlf=false', 'worktree', 'add', '--detach', worktree, candidate]
}
export async function cleanupCheckout(worktree, unregister) {
  // Node handles Windows file attributes/retries; Git then removes only registration.
  await rm(worktree, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })
  await unregister()
}
export { verifyPublicFiles, verifyOnline } from './onlineAcceptance.mjs'
export async function publish(args = process.argv.slice(2), { runCommand = execute, verifyDeployment = verifyRelease, createJournal = journal } = {}) {
  assert.ok(!args.length || (args.length === 2 && args[0] === '--remote'), 'Usage: demo:publish [--remote github]')
  const remote = args[1] ?? 'github'
  assert.match(remote, /^[a-zA-Z0-9_-]+$/)
  const git = args => runCommand('git', args, { cwd: root, label: `git ${args[0]}` })
  const remoteUrl = await git(['remote', 'get-url', remote])
  const match = /^(?:git@github\.com:|https:\/\/github\.com\/)([^/]+\/[^/]+?)(?:\.git)?$/.exec(remoteUrl)
  assert.ok(match, 'Remote must identify a GitHub repository')
  const repo = match[1]
  const gh = args => runCommand('gh', [...args, '--repo', repo], { cwd: root, label: `GitHub ${args.slice(0, 2).join(' ')}` })
  const api = async path => JSON.parse(await runCommand('gh', ['api', `repos/${repo}${path ? '/' + path : ''}`], { cwd: root, label: `GitHub ${path || 'permissions'}` }))
  const common = resolve(await git(['rev-parse', '--path-format=absolute', '--git-common-dir']))
  const lockPath = resolve(common, 'demo-publish.lock')
  await mkdir(lockPath)
  const record = createJournal(web, { repo, status: 'PREFLIGHT_FAILED_NOT_PUSHED' })
  const outcome = record.state
  let worktree, temporary, pushed = false
  try {
    await record.save({ stage: 'permissions' })
    await runCommand('gh', ['auth', 'status'], { cwd: root, label: 'GitHub authentication' })
    assert.ok((await api('')).permissions?.push, 'GitHub push permission required')
    assert.equal((await api('pages')).build_type, 'workflow', 'Pages source must be Actions')
    assert.equal((await api('actions/permissions')).enabled, true, 'Actions disabled')
    const environment = await api('environments/github-pages')
    assert.ok(environment.deployment_branch_policy?.custom_branch_policies, 'Explicit release environment policy required')
    const policies = (await api('environments/github-pages/deployment-branch-policies')).branch_policies
    assert.ok(policies.some(p => p.type === 'branch' && p.name === 'release/demo-pages'), 'Environment must permit release/demo-pages')
    const refs = async () => {
      const lines = (await git(['ls-remote', remote, 'refs/heads/main', releaseRef])).split('\n')
      const find = ref => lines.find(line => line.endsWith('\t' + ref))?.split('\t')[0]
      return { main: find('refs/heads/main'), release: find(releaseRef) }
    }
    await record.save({ stage: 'refs' })
    await git(['fetch', remote, '+refs/heads/main:refs/remotes/' + remote + '/main'])
    const initial = await refs(), candidate = initial.main
    await record.save({ sourceCommit: candidate, initialRefs: initial })
    if (initial.release) await git(['fetch', remote, releaseRef])
    let ancestor = !initial.release
    if (initial.release) { try { await git(['merge-base', '--is-ancestor', initial.release, candidate]); ancestor = true } catch { ancestor = false } }
    let localMain
    try { localMain = await git(['rev-parse', '--verify', 'refs/heads/main']) } catch { /* optional local main */ }
    const runs = async () => JSON.parse(await gh(['run', 'list', '--workflow', 'deploy-demo-pages.yml', '--branch', 'release/demo-pages', '--limit', '100', '--json', 'databaseId,headSha,status,conclusion,url,createdAt']))
    const beforeRuns = await runs()
    prePushPolicy({ candidate, ...initial, ancestor, localMain,
      dirty: await git(['status', '--porcelain', '--untracked-files=all', '--', 'ui_web', '.github', '.gitattributes', 'AGENTS.md']),
      active: beforeRuns.some(r => r.status !== 'completed') })
    if (initial.release !== candidate) {
      temporary = await mkdtemp(resolve(common, 'demo-publish-'))
      worktree = resolve(temporary, 'checkout')
      await record.save({ stage: 'checkout', temporary, worktree })
      await git(checkoutArgs(worktree, candidate))
      const candidateWeb = resolve(worktree, 'ui_web')
      await checkedPush({
        check: async () => {
          await record.save({ stage: 'dependencies' })
          const npm = args => process.platform === 'win32'
            ? runCommand('cmd.exe', ['/d', '/s', '/c', 'npm ' + args.join(' ')], { cwd: candidateWeb, inherit: true, timeout: 900000, label: `npm ${args.join(' ')}` })
            : runCommand('npm', args, { cwd: candidateWeb, inherit: true, timeout: 900000, label: `npm ${args.join(' ')}` })
          await npm(['ci'])
          await record.save({ stage: 'release-gate' })
          await npm(['run', 'demo:release-check'])
          const evidence = JSON.parse(readFileSync(resolve(candidateWeb, '.build/demo-release.json')))
          assert.equal(evidence.sourceCommit, candidate)
          await record.save({ gate: evidence })
          return evidence
        },
        recheck: async () => {
          await record.save({ stage: 'recheck' })
          assert.deepEqual(await refs(), initial, 'Remote refs changed during preflight')
          assert.ok(!(await runs()).some(r => r.status !== 'completed'), 'Concurrent deployment')
        },
        push: async () => {
          await record.save({ stage: 'push', pushAttempted: true })
          await git(['push', '--porcelain', remote, `${candidate}:${releaseRef}`])
          pushed = true
          await record.save({ pushed: true, status: 'PUSHED_DEPLOYMENT_FAILED' })
        },
      })
    }
    await record.save({ stage: 'actions' })
    const deadline = Date.now() + 25 * 60 * 1000
    let selected
    while (Date.now() < deadline) {
      selected = (await runs()).find(r => r.headSha === candidate)
      if (selected) await record.save({ runId: String(selected.databaseId), run: selected.url, recovery: `npm run demo:verify-release -- --run ${selected.databaseId} --remote ${remote}` })
      if (selected?.status === 'completed') break
      if (!pushed && !selected) throw new Error('Existing release has no deployment run; explicit rerun authorization required')
      console.log(`WAIT Pages ${candidate}: ${selected?.status ?? 'awaiting workflow'}`)
      await new Promise(done => setTimeout(done, 10000))
    }
    assert.equal(selected?.status, 'completed', 'Actions deadline exceeded')
    assert.equal(selected.conclusion, 'success', 'DEPLOYMENT FAILED; explicit recovery decision required')
    await verifyDeployment({ runId: String(selected.databaseId), remote, record, expectedSha: candidate })
    if (!pushed) await record.save({ alreadyPublished: true })
  } catch (error) {
    await finishCleanup(() => record.save({ error: error.message, verification: 'NOT_VERIFIED' }), () => {})
    throw error
  } finally {
    let owned = false
    await finishCleanup(async () => {
      if (worktree) {
        assertCleanupPaths({ worktree, temporary, common })
        for (const path of [common, temporary, worktree]) assert.ok(!(await lstat(path)).isSymbolicLink(), 'Linked cleanup path')
        const registered = (await git(['worktree', 'list', '--porcelain'])).split('\n')
          .filter(line => line.startsWith('worktree ')).map(line => resolve(line.slice(9)))
        assert.ok(registered.includes(resolve(worktree)), 'Unregistered cleanup checkout')
        owned = true
        await cleanupCheckout(worktree, () => git(['worktree', 'remove', '--force', worktree]))
      }
      if (temporary) await rm(temporary, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 })
    }, error => {
      outcome.cleanupPending = true; outcome.cleanupError = error.message
      if (owned) {
        const quote = value => "'" + value.replaceAll("'", "''") + "'"
        outcome.cleanupCommands = [
          `Remove-Item -LiteralPath ${quote(temporary)} -Recurse -Force`,
          `git -C ${quote(root)} worktree remove --force ${quote(worktree)}`,
        ]
      }
    })
    await finishCleanup(() => rmdir(lockPath), error => {
      outcome.cleanupPending = true; outcome.lockCleanupError = error.message
    })
    await finishCleanup(() => record.save(), error => { console.error(`Evidence save failed: ${error.message}`) })
    console.log(JSON.stringify(outcome))
  }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  publish().catch(error => { console.error(error.message); process.exitCode = 1 })
}
