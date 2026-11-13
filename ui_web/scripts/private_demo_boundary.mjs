import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { realpathSync, existsSync, lstatSync, readdirSync } from 'node:fs'
import { isAbsolute, resolve, relative, sep, dirname, basename } from 'node:path'
import { fileURLToPath } from 'node:url'
export const web = fileURLToPath(new URL('..', import.meta.url))
export const repository = realpathSync(resolve(web, '..'))
const within = (parent, path) => { const r = relative(parent, path); return !r || (!r.startsWith('..' + sep) && !isAbsolute(r)) }
export function externalPath(path, { fresh = false } = {}) {
  assert.ok(path && isAbsolute(path), 'Explicit absolute external path required')
  const requested = resolve(path)
  const resolved = fresh ? resolve(realpathSync(dirname(requested)), basename(requested)) : realpathSync(requested)
  const worktrees = execFileSync('git', ['worktree', 'list', '--porcelain'], { cwd: repository, encoding: 'utf8' }).split('\n').filter(l => l.startsWith('worktree ')).map(l => realpathSync(l.slice(9)))
  for (const root of worktrees) {
    assert.ok(!within(root, resolved) && !within(resolved, root), 'Private path overlaps a repository worktree')
    const inspect = dir => {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        if (['.git', 'node_modules', '.venv', '_temp_docs'].includes(entry.name)) continue
        const candidate = resolve(dir, entry.name)
        if (lstatSync(candidate).isSymbolicLink()) {
          let target
          try { target = realpathSync(candidate) } catch { continue }
          assert.ok(!within(target, resolved) && !within(resolved, target), 'Private path accessible through repository symlink')
        } else if (entry.isDirectory()) inspect(candidate)
      }
    }
    inspect(root)
  }
  if (fresh) assert.ok(!existsSync(resolved), 'Output must be new; retained artifacts are never overwritten')
  return resolved
}
export function parsePrivateArgs(args) {
  const parsed = {}
  for (let i = 0; i < args.length; i += 2) {
    assert.ok(['--r2', '--r3', '--wpa', '--output'].includes(args[i]) && args[i + 1] && !parsed[args[i]], 'Expected --r2 --r3 --wpa --output exactly once')
    parsed[args[i]] = args[i + 1]
  }
  assert.equal(Object.keys(parsed).length, 4, 'All three private packages and output are required')
  const result = Object.fromEntries(Object.entries(parsed).map(([key, value]) => [key.slice(2), externalPath(value, { fresh: key === '--output' })]))
  const locations = Object.values(result)
  for (let i = 0; i < locations.length; i++) for (let j = i + 1; j < locations.length; j++) assert.ok(!within(locations[i], locations[j]) && !within(locations[j], locations[i]), 'Private inputs and output must not overlap')
  return result
}
