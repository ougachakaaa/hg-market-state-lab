import { mkdir, mkdtemp, readdir, lstat, cp, rm, rename, writeFile, access, rmdir } from 'node:fs/promises'
import { resolve, dirname, relative, isAbsolute } from 'node:path'
import { fileURLToPath } from 'node:url'
import { execFileSync, spawn } from 'node:child_process'
import { build } from 'vite'
import { readFile } from 'node:fs/promises'
import { sha } from '../../scripts/artifact_integrity.mjs'

export const web = fileURLToPath(new URL('../../', import.meta.url))
export async function lock(path) {
  let current = resolve(path)
  while (true) {
    try { if ((await lstat(current)).isSymbolicLink()) throw new Error('linked_lock_path') }
    catch (error) { if (error.code !== 'ENOENT') throw error }
    const parent = dirname(current)
    if (parent === current) break
    current = parent
  }
  await mkdir(dirname(path), { recursive: true })
  try { await mkdir(path) } catch { throw new Error('busy_requires_explicit_recovery') }
  return () => rmdir(path)
}
export function preflight(snapshot) {
  return new Promise((accept, reject) => {
    const child = spawn(process.execPath, [resolve(web, 'scripts/demo_check.mjs'), '--dir', snapshot], { cwd: web, stdio: 'inherit', windowsHide: true })
    child.once('error', reject)
    child.once('exit', code => code === 0 ? accept() : reject(new Error('snapshot_admission_failed')))
  })
}
async function removeOwned(path) {
  const boundary = resolve(web, '.build')
  const child = relative(boundary, path)
  if (!child || child.startsWith('..') || isAbsolute(child)) throw new Error('unsafe_cleanup')
  await rm(path, { recursive: true, force: true })
}
export async function buildDemo({ dataset = resolve(web, 'demo/bundles'), work = resolve(web, '.build/demo-collection'), compile = compileDemo } = {}) {
  const output = resolve(web, '.build/demo')
  const releaseOutput = await lock(resolve(web, '.build/demo-output.lock'))
  let staging
  try {
    await removeOwned(output)
    staging = await mkdtemp(resolve(web, '.build/demo-invocation-'))
    const snapshot = resolve(staging, 'snapshot')
    const releaseDataset = await lock(resolve(work, 'dataset.lock'))
    try {
      try { await lstat(resolve(work, 'pending.json')); throw new Error('pending_transaction') }
      catch (error) { if (error.code !== 'ENOENT') throw error }
      // Admit source paths before copying so redirection cannot disappear in staging.
      await preflight(dataset)
      await mkdir(snapshot)
      for (const name of await readdir(dataset)) {
        const source = resolve(dataset, name)
        if (!(await lstat(source)).isFile()) throw new Error('unsafe_dataset_entry')
        await cp(source, resolve(snapshot, name), { dereference: false })
      }
      await preflight(snapshot)
    } finally { await releaseDataset() }
    const artifact = resolve(staging, 'artifact')
    await compile(snapshot, artifact)
    await access(resolve(artifact, 'index.html'))
    await access(resolve(artifact, 'assets'))
    await writeFile(resolve(artifact, 'build-complete.json'), JSON.stringify({ format: 'ddb04_static_build_v1', sourceCommit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: web, encoding: 'utf8' }).trim(), manifestSha256: sha(await readFile(resolve(snapshot, 'manifest.json'))) }) + '\n')
    await rename(artifact, output)
  } catch (error) {
    await removeOwned(output)
    throw error
  } finally {
    try { if (staging) await removeOwned(staging) }
    catch (error) { await removeOwned(output); throw error }
    finally { await releaseOutput() }
  }
}
async function compileDemo(snapshot, artifact) {
  await build({ configFile: resolve(web, 'demo/build/vite.config.ts'),
    plugins: [{ name: 'demo-snapshot', resolveId(id) { if (id === 'virtual:demo-data') return '\0demo-data' },
      async load(id) {
        if (id !== '\0demo-data') return
        const { readFile } = await import('node:fs/promises')
        const files = (await readdir(snapshot)).filter(name => name !== 'manifest.json')
        const bundles = await Promise.all(files.map(async name => JSON.parse(await readFile(resolve(snapshot, name), 'utf8'))))
        return `export default ${JSON.stringify(bundles)}`
      } }], build: { outDir: artifact, emptyOutDir: true } })
}
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { await buildDemo(); console.log('PASS static Demo built') }
  catch (error) {
    const reason = ['busy_requires_explicit_recovery', 'pending_transaction'].includes(error.message)
      ? error.message : 'admission_or_build_failed'
    console.error('FAIL demo build ' + reason)
    process.exitCode = 1
  }
}
