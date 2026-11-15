import assert from 'node:assert/strict'
import { execFileSync, spawn } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises'
import { resolve, dirname } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { sha } from '../../scripts/artifact_integrity.mjs'
import { verifyDemo } from '../../scripts/demo_artifact.mjs'
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
function command(program, args, cwd = root) {
  return execFileSync(program, args, { cwd, encoding: 'utf8', windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] }).trim()
}
function run(program, args, cwd) {
  return new Promise((accept, reject) => {
    const child = spawn(program, args, { cwd, stdio: 'inherit', windowsHide: true })
    child.once('error', reject)
    child.once('exit', code => code === 0 ? accept() : reject(new Error(`${program} failed (${code})`)))
  })
}
const npm = (args, cwd) => process.platform === 'win32'
  ? run('cmd.exe', ['/d', '/s', '/c', 'npm ' + args.join(' ')], cwd)
  : run('npm', args, cwd)
export async function verifyOnline(base, receipt) {
  const url = new URL(base)
  assert.equal(url.protocol, 'https:')
  for (const item of receipt.files) {
    const response = await fetch(new URL(item.file, url), { cache: 'no-store', signal: AbortSignal.timeout(30000) })
    assert.ok(response.ok, `Public file unavailable: ${item.file}`)
    const bytes = Buffer.from(await response.arrayBuffer())
    assert.equal(bytes.length, item.size, `Public size mismatch: ${item.file}`)
    assert.equal(sha(bytes), item.sha256, `Public hash mismatch: ${item.file}`)
  }
}
export async function publish(args = process.argv.slice(2)) {
  assert.ok(!args.length || (args.length === 2 && args[0] === '--remote'), 'Usage: demo:publish [--remote github]')
  const remote = args[1] ?? 'github'
  assert.match(remote, /^[a-zA-Z0-9_-]+$/)
  const git = args => command('git', args)
  const remoteUrl = git(['remote', 'get-url', remote])
  const match = /^(?:git@github\.com:|https:\/\/github\.com\/)([^/]+\/[^/]+?)(?:\.git)?$/.exec(remoteUrl)
  assert.ok(match, 'Remote must identify a GitHub repository')
  const repo = match[1]
  const gh = args => command('gh', [...args, '--repo', repo])
  const api = path => JSON.parse(command('gh', ['api', `repos/${repo}/${path}`]))
  const common = git(['rev-parse', '--path-format=absolute', '--git-common-dir'])
  const lockPath = resolve(common, 'demo-publish.lock')
  await mkdir(lockPath) // Existing ownership requires explicit operator recovery.
  let worktree, temporary, pushed = false, deployed = false
  try {
    command('gh', ['auth', 'status'])
    const permission = api('').permissions
    assert.ok(permission?.push, 'GitHub push permission required')
    const pages = api('pages')
    assert.equal(pages.build_type, 'workflow', 'Pages source must be Actions')
    assert.equal(api('actions/permissions').enabled, true, 'Actions disabled')
    const environment = api('environments/github-pages')
    assert.ok(environment.deployment_branch_policy?.custom_branch_policies, 'Explicit release environment policy required')
    const policies = api('environments/github-pages/deployment-branch-policies').branch_policies
    assert.ok(policies.some(p => p.type === 'branch' && p.name === 'release/demo-pages'), 'Environment must permit release/demo-pages')
    const refs = () => {
      const lines = git(['ls-remote', remote, 'refs/heads/main', releaseRef]).split('\n')
      const find = ref => lines.find(line => line.endsWith('\t' + ref))?.split('\t')[0]
      return { main: find('refs/heads/main'), release: find(releaseRef) }
    }
    git(['fetch', remote, '+refs/heads/main:refs/remotes/' + remote + '/main'])
    const initial = refs(), candidate = initial.main
    if (initial.release) git(['fetch', remote, releaseRef])
    let ancestor = !initial.release
    if (initial.release) { try { git(['merge-base', '--is-ancestor', initial.release, candidate]); ancestor = true } catch { ancestor = false } }
    let localMain
    try { localMain = git(['rev-parse', '--verify', 'refs/heads/main']) } catch { /* no local main */ }
    const runs = () => JSON.parse(gh(['run', 'list', '--workflow', 'deploy-demo-pages.yml', '--branch', 'release/demo-pages', '--limit', '100', '--json', 'databaseId,headSha,status,conclusion,url,createdAt']))
    // Before DDB-06 reaches main the existing workflow still has its DDB-05 name/file.
    const beforeRuns = runs()
    prePushPolicy({ candidate, ...initial, ancestor, localMain,
      dirty: git(['status', '--porcelain', '--untracked-files=all', '--', 'ui_web', '.github', '.gitattributes', 'AGENTS.md']),
      active: beforeRuns.some(r => r.status !== 'completed') })
    temporary = await mkdtemp(resolve(common, 'demo-publish-'))
    worktree = resolve(temporary, 'checkout')
    git(['worktree', 'add', '--detach', worktree, candidate])
    const candidateWeb = resolve(worktree, 'ui_web')
    const evidence = await checkedPush({
      check: async () => {
        await npm(['ci'], candidateWeb)
        await npm(['run', 'demo:release-check'], candidateWeb)
        const result = JSON.parse(readFileSync(resolve(candidateWeb, '.build/demo-release.json')))
        assert.equal(result.sourceCommit, candidate)
        return result
      },
      recheck: async () => {
        assert.deepEqual(refs(), initial, 'Remote refs changed during preflight')
        assert.ok(!runs().some(r => r.status !== 'completed'), 'Concurrent deployment')
      },
      push: async () => {
        if (initial.release !== candidate) {
          git(['push', '--porcelain', remote, `${candidate}:${releaseRef}`])
          pushed = true
        }
      },
    })
    await writeFile(resolve(web, '.build/demo-publish.json'), JSON.stringify({ ...evidence, repo }, null, 2) + '\n')
    const deadline = Date.now() + 25 * 60 * 1000
    let selected
    while (Date.now() < deadline) {
      selected = runs().find(r => r.headSha === candidate)
      if (selected?.status === 'completed') break
      if (!pushed && !selected) throw new Error('Existing release has no deployment run; explicit rerun authorization required')
      console.log(`Waiting for Pages ${candidate}: ${selected?.status ?? 'awaiting workflow'}`)
      await new Promise(done => setTimeout(done, 10000))
    }
    assert.equal(selected?.status, 'completed', 'Actions deadline exceeded')
    console.log(selected.url)
    assert.equal(selected.conclusion, 'success', 'DEPLOYMENT FAILED')
    const deployments = api(`deployments?sha=${candidate}&environment=github-pages&per_page=20`)
    let base
    for (const deployment of deployments) {
      const statuses = api(`deployments/${deployment.id}/statuses`)
      if (statuses[0]?.state === 'success') { base = statuses[0].environment_url; break }
    }
    assert.ok(base, 'Successful Pages deployment URL unavailable')
    deployed = true
    const artifacts = resolve(temporary, 'artifacts')
    await mkdir(artifacts)
    gh(['run', 'download', String(selected.databaseId), '--name', 'demo-receipt', '--dir', artifacts])
    const receipt = JSON.parse(readFileSync(resolve(artifacts, 'demo-receipt.json')))
    assert.equal(receipt.sourceCommit, candidate)
    assert.equal(receipt.manifestSha256, evidence.manifestSha256)
    const site = resolve(artifacts, 'site')
    await mkdir(site)
    gh(['run', 'download', String(selected.databaseId), '--name', 'verified-demo', '--dir', site])
    verifyDemo(site, receipt, { sourceCommit: candidate, manifestSha256: evidence.manifestSha256 })
    await verifyOnline(base, receipt)
    const { verifyBrowser } = await import(pathToFileURL(resolve(candidateWeb, 'demo/build/browserAcceptance.mjs')).href)
    await verifyBrowser(base)
    console.log(JSON.stringify({ status: 'RELEASED_AND_VERIFIED', sourceCommit: candidate, run: selected.url, url: base }))
  } catch (error) {
    console.error(deployed ? 'DEPLOYED_BUT_ONLINE_ACCEPTANCE_NOT_VERIFIED' : pushed ? 'PUSHED_DEPLOYMENT_FAILED' : 'PREFLIGHT_FAILED_NOT_PUSHED')
    throw error
  } finally {
    if (worktree) git(['worktree', 'remove', '--force', worktree])
    if (temporary) await rm(temporary, { recursive: true, force: true })
    await rm(lockPath, { recursive: true })
  }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  publish().catch(error => { console.error(error.message); process.exitCode = 1 })
}
