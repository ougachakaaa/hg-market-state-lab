import { it, expect, beforeAll, afterAll } from 'vitest'
import { rm, mkdir, writeFile, access, mkdtemp, readFile, rename, symlink, unlink } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { spawn } from 'node:child_process'
import { lock, buildDemo, readSnapshotBundles } from './build.mjs'
import { isolatedOutput, developerOutputDigest } from './output.fixture'
import { fixture } from './dataset.fixture'
import { registry } from './registry'
import { dependencyInventory } from './dependencyInventory.mjs'
let developerBefore: string
beforeAll(async () => { developerBefore = await developerOutputDigest() })
afterAll(async () => { expect(await developerOutputDigest()).toBe(developerBefore) })

it('coordinates Python Collector with Node in both directions', async () => {
  const isolated = await isolatedOutput()
  const work = isolated.work
  await mkdir(work, { recursive: true })
  const python = resolve(process.platform === 'win32' ? '../.venv/Scripts/python.exe' : '../.venv/bin/python')
  const script = `import sys; sys.path.insert(0, 'demo/build'); import collect; from pathlib import Path
with collect.dataset_lock(Path(sys.argv[1])):
 print('held', flush=True)
 sys.stdin.readline()`
  const child = spawn(python, ['-c', script, work], { windowsHide: true })
  let diagnostic = ''
  child.stderr.on('data', chunk => { diagnostic += chunk })
  try {
    await new Promise<void>((done, reject) => { child.once('error', reject); child.stdout.once('data', () => done()); child.once('exit', code => reject(new Error(diagnostic || String(code)))) })
    await expect(lock(join(work, 'dataset.lock'))).rejects.toThrow('busy')
    const exited = new Promise(done => child.once('exit', done))
    child.stdin.end('release\n'); await exited
    const release = await lock(join(work, 'dataset.lock'))
    try {
      const result = await new Promise<string>((done, reject) => {
        const probe = spawn(python, ['-c', script, work], { windowsHide: true }); let error = ''
        probe.stderr.on('data', chunk => { error += chunk }); probe.once('error', reject); probe.once('exit', () => done(error))
      })
      expect(result).toContain('busy_requires_explicit_recovery')
    } finally { await release() }
  } finally { child.kill(); await isolated.cleanup() }
}, 20000)

it('rejects pending transactions and removes stale successful output', async () => {
  const isolated = await isolatedOutput()
  const { work, output } = isolated
  await mkdir(work, { recursive: true })
  try {
    await writeFile(join(work, 'pending.json'), '{}')
    await mkdir(output, { recursive: true })
    await writeFile(join(output, 'index.html'), 'old')
    await expect(buildDemo({ ...isolated })).rejects.toThrow('pending_transaction')
    await expect(access(join(output, 'index.html'))).rejects.toThrow()
    const release = await lock(join(work, 'dataset.lock')); await release()
  } finally { await isolated.cleanup() }
})


it('keeps exclusion after a process is forcibly terminated', async () => {
  const isolated = await isolatedOutput()
  const work = isolated.work
  await mkdir(work, { recursive: true })
  const path = join(work, 'dataset.lock')
  const script = `import { lock } from './demo/build/build.mjs'; await lock(process.argv[1]); console.log('held'); setInterval(() => {}, 1000)`
  const child = spawn(process.execPath, ['--input-type=module', '-e', script, path], { windowsHide: true })
  try {
    await new Promise<void>((done, reject) => { child.once('error', reject); child.stdout.once('data', () => done()); child.once('exit', code => reject(new Error(String(code)))) })
    const exited = new Promise(done => child.once('exit', done)); child.kill('SIGKILL'); await exited
    await expect(lock(path)).rejects.toThrow('busy')
  } finally { child.kill(); await isolated.cleanup() }
}, 20000)


it('uses admitted Manifest order rather than directory enumeration', async () => {
  const data = await fixture()
  try {
    const bundles = await readSnapshotBundles(data.root)
    expect(bundles.map(bundle => bundle.bundle_id)).toEqual(registry.map(entry => entry.bundle_id))
    const files = await Promise.all(registry.map(async entry => ({ path: join(data.root, entry.path), bytes: await readFile(join(data.root, entry.path)) })))
    for (const file of files) await rm(file.path)
    for (const file of files.reverse()) await writeFile(file.path, file.bytes)
    expect(await readSnapshotBundles(data.root)).toEqual(bundles)
  } finally { await rm(data.root, { recursive: true, force: true }) }
})
it('normalizes and sorts module inventories independently of enumeration', () => {
  const ids = ['C:\\repo\\ui_web\\z.ts', 'C:/repo/ui_web/a.ts', '\0demo-data']
  expect(dependencyInventory(ids, 'C:/repo/')).toEqual(dependencyInventory([...ids].reverse(), 'C:\\repo\\'))
  expect(dependencyInventory(ids, 'C:/repo/')).toEqual(['\0demo-data', 'ui_web/a.ts', 'ui_web/z.ts'])
})
it('rejects output roots outside the owned build directory before touching output', async () => {
  await expect(buildDemo({ outputRoot: resolve('..') })).rejects.toThrow('unsafe_output_root')
  await expect(buildDemo({ outputRoot: resolve('.build/../../escape') })).rejects.toThrow('unsafe_output_root')
})

it('rejects existing redirected output roots before touching external output', async () => {
  const isolated = await isolatedOutput()
  const external = await mkdtemp(join(tmpdir(), 'ddb-linked-output-'))
  const linked = join(isolated.outputRoot, 'redirect')
  try {
    await mkdir(join(external, 'demo'))
    await writeFile(join(external, 'demo/index.html'), 'external-test-owned-sentinel')
    await symlink(external, linked, process.platform === 'win32' ? 'junction' : 'dir')
    await expect(buildDemo({ outputRoot: linked, work: isolated.work })).rejects.toThrow('linked_build_path')
    expect(await readFile(join(external, 'demo/index.html'), 'utf8')).toBe('external-test-owned-sentinel')
  } finally {
    await isolated.cleanup()
    await rm(external, { recursive: true, force: true })
  }
})

it('rejects a compiler artifact redirected outside the invocation', async () => {
  const data = await fixture()
  const isolated = await isolatedOutput()
  const external = await mkdtemp(join(tmpdir(), 'ddb-linked-artifact-'))
  try {
    await mkdir(join(external, 'assets'))
    await writeFile(join(external, 'index.html'), 'external-test-owned-sentinel')
    await expect(buildDemo({ ...isolated, dataset: data.root, compile: async (_snapshot: string, artifact: string) => {
      await symlink(external, artifact, process.platform === 'win32' ? 'junction' : 'dir')
    } })).rejects.toThrow('linked_build_path')
    await expect(access(join(external, 'build-complete.json'))).rejects.toThrow()
    expect(await readFile(join(external, 'index.html'), 'utf8')).toBe('external-test-owned-sentinel')
    await expect(access(isolated.output)).rejects.toThrow()
  } finally {
    await isolated.cleanup()
    await rm(data.root, { recursive: true, force: true })
    await rm(external, { recursive: true, force: true })
  }
}, 20000)

it('does not clean outside outputRoot when an ancestor is redirected after locking', async () => {
  const data = await fixture()
  const isolated = await isolatedOutput()
  const external = await mkdtemp(join(tmpdir(), 'ddb-cleanup-boundary-'))
  const held = isolated.outputRoot + '-held'
  let redirected = false
  try {
    await mkdir(join(external, 'demo'))
    await writeFile(join(external, 'demo/index.html'), 'external-test-owned-sentinel')
    await expect(buildDemo({ ...isolated, dataset: data.root, compile: async () => {
      await rename(isolated.outputRoot, held)
      try { await symlink(external, isolated.outputRoot, process.platform === 'win32' ? 'junction' : 'dir') }
      catch (error) { await rename(held, isolated.outputRoot); throw error }
      redirected = true
      throw new Error('controlled_redirect_failure')
    } })).rejects.toThrow()
    expect(redirected).toBe(true)
    expect(await readFile(join(external, 'demo/index.html'), 'utf8')).toBe('external-test-owned-sentinel')
    await expect(access(join(external, 'demo-output.lock'))).rejects.toThrow()
  } finally {
    if (redirected) { await unlink(isolated.outputRoot); await rename(held, isolated.outputRoot) }
    await isolated.cleanup()
    await rm(data.root, { recursive: true, force: true })
    await rm(external, { recursive: true, force: true })
  }
}, 20000)
