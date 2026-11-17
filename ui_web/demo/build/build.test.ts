import { it, expect, beforeAll, afterAll } from 'vitest'
import { rm, mkdir, writeFile, access } from 'node:fs/promises'
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
  } finally { await rm(data.root, { recursive: true, force: true }) }
})
it('normalizes and sorts module inventories independently of enumeration', () => {
  const ids = ['C:\\repo\\ui_web\\z.ts', 'C:/repo/ui_web/a.ts', '\0demo-data']
  expect(dependencyInventory(ids, 'C:/repo/')).toEqual(dependencyInventory([...ids].reverse(), 'C:\\repo\\'))
  expect(dependencyInventory(ids, 'C:/repo/')).toEqual(['\0demo-data', 'ui_web/a.ts', 'ui_web/z.ts'])
})
it('rejects output roots outside the owned build directory before touching output', async () => {
  await expect(buildDemo({ outputRoot: resolve('..') })).rejects.toThrow('unsafe_output_root')
})
