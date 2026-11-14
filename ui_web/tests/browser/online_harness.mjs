// Lifecycle and diagnostics shared only by the two Online acceptance scripts.
import { spawn, spawnSync } from 'node:child_process'
import { createServer } from 'node:net'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

export async function unusedPort() {
  const server = createServer()
  await new Promise((done, reject) => server.once('error', reject).listen(0, '127.0.0.1', done))
  const port = server.address().port
  await new Promise(done => server.close(done))
  return port
}

export function onlineHarness(env, root, output) {
  const children = []
  const logs = []
  const errors = []
  function start(command, args, cwd = root) {
    const child = spawn(command, args, {
      cwd, env, detached: process.platform !== 'win32', stdio: ['ignore', 'pipe', 'pipe'],
    })
    children.push(child)
    const record = { command, args, output: '' }
    logs.push(record)
    child.stdout.on('data', chunk => { record.output += chunk })
    child.stderr.on('data', chunk => { record.output += chunk })
    child.on('error', error => { errors.push(String(error)) })
    return child
  }
  async function ready(url, child, expected) {
    for (let attempt = 0; attempt < 120; attempt++) {
      if (errors.length || child.exitCode !== null || child.signalCode !== null) {
        throw new Error(`Server startup failed: ${errors.join('; ')} exit=${child.exitCode}`)
      }
      try {
        // Require our own child's listening log before probing the chosen port.
        // A bind race must fail, never attach to another server.
        if (logs[children.indexOf(child)].output.includes(new URL(url).origin)) {
          const response = await fetch(url, { signal: AbortSignal.timeout(1000) })
          if (response.status === expected) return
        }
      } catch { /* starting */ }
      await new Promise(done => setTimeout(done, 250))
    }
    throw new Error(`Timed out waiting for ${url}`)
  }
  async function save(evidence, browserErrors) {
    await mkdir(output, { recursive: true })
    // No request headers, bodies, environment or browser storage are captured.
    const redact = value => value.replaceAll(env.LAB_AUTH_JWT_SECRET, '[secret]')
      .replace(/eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+/g, '[jwt]')
      .replace(/(lab_access_token=)[^;\s]+/g, '$1[redacted]')
    await writeFile(resolve(output, 'diagnostics.json'), redact(JSON.stringify({ evidence, browserErrors, errors, logs }, null, 2)))
  }
  async function stop() {
    for (const child of children.reverse()) {
      if (!child.pid) continue
      if (process.platform === 'win32') {
        spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { stdio: 'ignore' })
      } else {
        const signal = name => { try { process.kill(-child.pid, name) } catch (error) { if (error.code !== 'ESRCH') throw error } }
        signal('SIGTERM')
        await new Promise(done => {
          const timer = setTimeout(done, 1000)
          if (child.exitCode !== null || child.signalCode !== null) { clearTimeout(timer); done() }
          else child.once('exit', () => { clearTimeout(timer); done() })
        })
        signal('SIGKILL')
      }
    }
  }
  return { start, ready, save, stop }
}

export function observe(page, evidence, states, errors) {
  const pending = new Set()
  page.on('pageerror', error => errors.push(String(error)))
  page.on('requestfailed', request => evidence.push(`${request.method()} ${new URL(request.url()).pathname} FAILED ${request.failure()?.errorText}`))
  page.on('response', response => {
    const path = new URL(response.url()).pathname
    if (!path.startsWith('/auth/') && !path.startsWith('/api/')) return
    evidence.push(`${response.request().method()} ${path} ${response.status()}`)
    if (response.status() === 401) {
      const task = response.request().allHeaders().then(headers => {
        const token = headers.cookie?.match(/(?:^|;\s*)lab_access_token=([^;]+)/)?.[1]
        let issued, expires
        try {
          const claims = JSON.parse(Buffer.from(token.split('.')[1], 'base64url').toString())
          issued = claims.iat; expires = claims.exp
        } catch { /* absent or malformed; never log the token */ }
        evidence.push(`${path} AUTH_DIAGNOSTIC ${JSON.stringify({ cookiePresent: Boolean(token), issued, expires, now: Date.now() / 1000 })}`)
      }).catch(() => {}).finally(() => pending.delete(task))
      pending.add(task)
    }
    if (!/\/runs\/[a-f0-9]+$/.test(path) || response.status() !== 200) return
    const task = response.json().then(body => { states.push(body.status) })
      .catch(error => { evidence.push(`${path} BODY_UNAVAILABLE ${error.message.split('\n')[0]}`) })
      .finally(() => pending.delete(task))
    pending.add(task)
  })
  return () => Promise.all([...pending])
}
