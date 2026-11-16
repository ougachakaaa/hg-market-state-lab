import { spawn } from 'node:child_process'
import { mkdir, writeFile, rename } from 'node:fs/promises'
import { resolve } from 'node:path'

export function execute(program, args, { cwd, timeout = 120000, label = program, inherit = false } = {}) {
  console.log(`START ${label}`)
  return new Promise((accept, reject) => {
    const child = spawn(program, args, { cwd, windowsHide: true, stdio: inherit ? 'inherit' : ['ignore', 'pipe', 'pipe'] })
    let stdout = '', stderr = '', expired = false
    child.stdout?.on('data', data => { stdout += data })
    child.stderr?.on('data', data => { stderr = (stderr + data).slice(-16384) })
    const heartbeat = setInterval(() => console.log(`WAIT ${label}`), 15000)
    const deadline = setTimeout(() => { expired = true; child.kill() }, timeout)
    const finish = () => { clearInterval(heartbeat); clearTimeout(deadline) }
    child.once('error', error => { finish(); reject(error) })
    child.once('close', code => {
      finish()
      if (code === 0 && !expired) { console.log(`PASS ${label}`); accept(stdout.trim()); return }
      const transient = expired || /timeout|timed out|connection reset|connection refused|TLS handshake|unexpected EOF|network is unreachable|temporary failure|HTTP 50[234]|connection closed|dial tcp|i\/o timeout/i.test(stderr)
      const error = new Error(`${label}: ${expired ? 'timeout' : transient ? 'network failure' : 'command failed'} (exit ${code})`)
      error.transient = transient; error.exitCode = code
      reject(error)
    })
  })
}
export function journal(web, initial = {}) {
  const state = { cleanupPending: false, ...initial }
  return {
    state,
    async save(patch = {}) {
      Object.assign(state, patch)
      const files = [resolve(web, '.build/demo-publish.json')]
      if (state.runId) files.push(resolve(web, `.build/demo-releases/${state.runId}/verification.json`))
      for (const file of files) {
        await mkdir(resolve(file, '..'), { recursive: true })
        const temp = `${file}.${process.pid}.tmp`
        await writeFile(temp, JSON.stringify(state, null, 2) + '\n')
        await rename(temp, file)
      }
    },
  }
}
