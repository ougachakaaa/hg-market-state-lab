import { it, expect } from 'vitest'
import { mkdtemp, rm, mkdir, writeFile, access } from 'node:fs/promises'
import { join, resolve } from 'node:path'
import { spawn } from 'node:child_process'
import { lock, buildDemo } from './build.mjs'

it('coordinates Python Collector with Node in both directions', async () => {
  const work = await mkdtemp(resolve('.build/ddb04-lock-'))
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
  } finally { child.kill(); await rm(work, { recursive: true, force: true }) }
}, 20000)

it('rejects pending transactions and removes stale successful output', async () => {
  const work = await mkdtemp(resolve('.build/ddb04-pending-'))
  try {
    await writeFile(join(work, 'pending.json'), '{}')
    await mkdir('.build/demo', { recursive: true })
    await writeFile('.build/demo/index.html', 'old')
    await expect(buildDemo({ work })).rejects.toThrow('pending_transaction')
    await expect(access('.build/demo/index.html')).rejects.toThrow()
    const release = await lock(join(work, 'dataset.lock')); await release()
  } finally { await rm(work, { recursive: true, force: true }) }
})


it('keeps exclusion after a process is forcibly terminated', async () => {
  const work = await mkdtemp(resolve('.build/ddb04-killed-'))
  const path = join(work, 'dataset.lock')
  const script = `import { lock } from './demo/build/build.mjs'; await lock(process.argv[1]); console.log('held'); setInterval(() => {}, 1000)`
  const child = spawn(process.execPath, ['--input-type=module', '-e', script, path], { windowsHide: true })
  try {
    await new Promise<void>((done, reject) => { child.once('error', reject); child.stdout.once('data', () => done()); child.once('exit', code => reject(new Error(String(code)))) })
    const exited = new Promise(done => child.once('exit', done)); child.kill('SIGKILL'); await exited
    await expect(lock(path)).rejects.toThrow('busy')
  } finally { child.kill(); await rm(work, { recursive: true, force: true }) }
}, 20000)
