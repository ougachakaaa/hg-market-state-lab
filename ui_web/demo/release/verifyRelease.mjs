import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { mkdir, mkdtemp, rmdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { createHash } from 'node:crypto'
import { execute, journal } from './execution.mjs'
import { verifyDemo } from '../../scripts/demo_artifact.mjs'
import { verifyOnline } from './onlineAcceptance.mjs'
import { verifyBrowser } from '../build/browserAcceptance.mjs'
const web = fileURLToPath(new URL('../../', import.meta.url))
const root = resolve(web, '..')
export function parseVerifyArgs(args) {
  const values = {}
  for (let index = 0; index < args.length; index += 2) {
    const key = args[index]
    assert.ok(['--run', '--remote'].includes(key) && args[index + 1] && !values[key], 'Usage: demo:verify-release -- --run ID [--remote github]')
    values[key] = args[index + 1]
  }
  assert.match(values['--run'] ?? '', /^[1-9][0-9]*$/, 'Explicit numeric run ID required')
  assert.match(values['--remote'] ?? 'github', /^[a-zA-Z0-9_-]+$/)
  return { runId: values['--run'], remote: values['--remote'] ?? 'github' }
}
export function assertReleaseRun(run, repo, runId) {
  assert.equal(String(run.id), String(runId), 'Run ID mismatch')
  assert.equal(run.repository.full_name, repo, 'Run repository mismatch')
  assert.equal(run.path, '.github/workflows/deploy-demo-pages.yml', 'Unexpected release workflow')
  assert.equal(run.head_branch, 'release/demo-pages', 'Unexpected release branch')
  assert.equal(run.status, 'completed', 'Run is not completed; verify it after completion')
  assert.equal(run.conclusion, 'success', 'Release run did not succeed; explicit recovery decision required')
  assert.match(run.head_sha, /^[a-f0-9]{40}$/)
}
export async function downloadArtifact({ runId, name, parent, gh, checkpoint }) {
  for (let attempt = 1; attempt <= 2; attempt++) {
    const directory = await mkdtemp(resolve(parent, `${name}-`))
    await checkpoint({ stage: `download:${name}`, downloadAttempt: attempt, downloadDirectory: directory })
    try {
      await gh(['run', 'download', String(runId), '--name', name, '--dir', directory], { timeout: 300000, label: `download ${name} attempt ${attempt}/2` })
      return directory
    } catch (error) {
      if (!error.transient || attempt === 2) throw error
      console.log(`RETRY download ${name}: ${error.message}`)
    }
  }
}
export async function acceptRelease({ run, repo, runId, api, download, committed, checkpoint, artifact = verifyDemo, online = verifyOnline, browser = verifyBrowser, confirm = async () => {} }) {
  assertReleaseRun(run, repo, runId)
  await checkpoint({ sourceCommit: run.head_sha, runAttempt: run.run_attempt, run: run.html_url, stage: 'deployment', status: 'VERIFYING' })
  const deployments = await api(`deployments?sha=${run.head_sha}&environment=github-pages&per_page=100`)
  const jobs = await api(`actions/runs/${runId}/attempts/${run.run_attempt}/jobs?per_page=100`)
  let url, deploymentId
  for (const deployment of deployments) {
    if (deployment.sha !== run.head_sha) continue
    const statuses = await api(`deployments/${deployment.id}/statuses`)
    const status = statuses[0]
    if (status?.state === 'success' && jobs.jobs.some(job => job.html_url === status.log_url)) {
      url = status.environment_url; deploymentId = deployment.id; break
    }
  }
  assert.ok(url && new URL(url).protocol === 'https:', 'Successful deployment for selected run unavailable')
  await checkpoint({ url, deploymentId, stage: 'ci-evidence', status: 'DEPLOYED_BUT_ONLINE_ACCEPTANCE_NOT_VERIFIED' })
  const evidenceDirectory = await download('release-evidence')
  const evidence = JSON.parse(await readFile(resolve(evidenceDirectory, 'demo-release.json')))
  const receiptDirectory = await download('demo-receipt')
  const receipt = JSON.parse(await readFile(resolve(receiptDirectory, 'demo-receipt.json')))
  assert.equal(evidence.result, 'PASS', 'CI Release Gate not PASS')
  assert.equal(evidence.sourceCommit, run.head_sha, 'CI evidence SHA mismatch')
  const hash = bytes => createHash('sha256').update(bytes).digest('hex')
  assert.equal(evidence.requirementsSha256, hash(await committed(run.head_sha, 'ui_web/demo/release/requirements.json')), 'Requirements identity mismatch')
  assert.equal(evidence.manifestSha256, hash(await committed(run.head_sha, 'ui_web/demo/bundles/manifest.json')), 'Manifest identity mismatch')
  await checkpoint({ requirementsSha256: evidence.requirementsSha256, manifestSha256: evidence.manifestSha256, receipt, stage: 'ci-artifact' })
  const site = await download('verified-demo')
  await artifact(site, receipt, { sourceCommit: run.head_sha, manifestSha256: evidence.manifestSha256 })
  await checkpoint({ stage: 'public-bytes', ciArtifact: 'PASS' })
  await online(url, receipt)
  await checkpoint({ stage: 'browser', publicBytes: 'PASS' })
  await browser(url)
  await confirm()
  await checkpoint({ stage: 'complete', browser: 'PASS', status: 'RELEASED_AND_VERIFIED' })
}
export function assertArtifacts(metadata) {
  for (const name of ['release-evidence', 'demo-receipt', 'verified-demo']) {
    const matches = metadata.artifacts.filter(item => item.name === name && !item.expired)
    assert.equal(matches.length, 1, `Missing, expired or ambiguous CI artifact: ${name}`)
  }
}
export async function verifyRelease({ runId, remote = 'github', record = journal(web, { runId }), expectedSha } = {}) {
  assert.match(String(runId), /^[1-9][0-9]*$/)
  const git = args => execute('git', args, { cwd: root, label: `git ${args[0]}` })
  const remoteUrl = await git(['remote', 'get-url', remote])
  const match = /^(?:git@github\.com:|https:\/\/github\.com\/)([^/]+\/[^/]+?)(?:\.git)?$/.exec(remoteUrl)
  assert.ok(match, 'Remote must identify a GitHub repository')
  const repo = match[1]
  const gh = (args, options = {}) => execute('gh', [...args, '--repo', repo], { cwd: root, ...options })
  const api = async path => JSON.parse(await execute('gh', ['api', `repos/${repo}/${path}`], { cwd: root, label: `GitHub ${path.split('?')[0]}` }))
  const parent = resolve(web, `.build/demo-releases/${runId}`)
  await mkdir(parent, { recursive: true })
  const lock = resolve(parent, 'verify.lock')
  await mkdir(lock) // An existing lock is not automatically removed.
  try {
    await record.save({ repo, runId, stage: 'run', status: 'NOT_VERIFIED', recovery: `npm run demo:verify-release -- --run ${runId} --remote ${remote}` })
    const run = await api(`actions/runs/${runId}`)
    if (expectedSha) assert.equal(run.head_sha, expectedSha, 'Selected release SHA changed')
    const metadata = await api(`actions/runs/${runId}/artifacts?per_page=100`)
    assertReleaseRun(run, repo, runId)
    assertArtifacts(metadata)
    await acceptRelease({ run, repo, runId, api,
      confirm: async () => {
        const latest = await api(`actions/runs/${runId}`)
        assertReleaseRun(latest, repo, runId)
        assert.equal(latest.head_sha, run.head_sha, 'Run SHA changed during acceptance')
        assert.equal(latest.run_attempt, run.run_attempt, 'Run attempt changed during acceptance')
      },
      checkpoint: patch => record.save(patch),
      download: name => downloadArtifact({ runId, name, parent, gh, checkpoint: patch => record.save(patch) }),
      committed: async (sha, path) => {
        const response = await api(`contents/${path}?ref=${sha}`)
        assert.equal(response.encoding, 'base64', 'Committed identity bytes unavailable')
        return Buffer.from(response.content, 'base64')
      },
    })
    return record.state
  } catch (error) {
    try { await record.save({ error: error.message, verification: 'NOT_VERIFIED' }) } catch { console.error('Unable to save failed verification evidence') }
    throw error
  } finally {
    try { await rmdir(lock) } catch (error) {
      record.state.cleanupPending = true; record.state.lockCleanupError = error.message
      try { await record.save() } catch { console.error('Unable to save cleanup evidence') }
    }
    console.log(JSON.stringify(record.state))
  }
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  Promise.resolve().then(() => verifyRelease(parseVerifyArgs(process.argv.slice(2)))).catch(error => { console.error(error.message); process.exitCode = 1 })
}
