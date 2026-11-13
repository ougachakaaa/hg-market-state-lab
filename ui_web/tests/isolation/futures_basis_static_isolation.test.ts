import { spawnSync } from 'node:child_process'
import { describe, expect, it } from 'vitest'

function rejectedBuild(target: string, appended: string, reason: RegExp) {
  // Load the actual config in Node, outside Vitest's browser module transforms.
  // Injection stays in memory; production files and build artifacts are untouched.
  const script = `
    import { build, loadConfigFromFile } from 'vite'
    const loaded = await loadConfigFromFile({ command: 'build', mode: 'production' }, 'tests/config/vite.futures-basis.config.ts')
    const injection = {
      name: 'test-forbidden-futures-basis-import', enforce: 'pre',
      transform(code, id) { if (id.endsWith(${JSON.stringify(target)})) return code + '\\n' + ${JSON.stringify(appended)} },
    }
    await build({
      ...loaded.config, configFile: false, logLevel: 'silent',
      plugins: [injection, ...loaded.config.plugins],
      build: { ...loaded.config.build, write: false },
    })
  `
  const result = spawnSync(process.execPath, ['--input-type=module'], {
    input: script, encoding: 'utf8', timeout: 30000,
  })
  expect(result.error).toBeUndefined()
  expect(result.status).toBe(1)
  expect(result.stdout + result.stderr).toMatch(reason)
}

describe('static Futures Basis build isolation rejects reachable runtime imports', () => {
  it('rejects a direct Auth import even when none of its exports are used', () => {
    rejectedBuild('/tests/static/futures_basis_research/main.tsx', "import '../../../src/app/auth/useAuthentication'", /Forbidden static presentation dependency/)
  }, 35000)
  it('rejects the Production Run lifecycle controller', () => {
    rejectedBuild('/tests/static/futures_basis_research/main.tsx', "import '../../../src/features/futures_basis_research/hooks/useFuturesBasis'", /Forbidden static presentation dependency/)
  }, 35000)
  it('rejects the Production preflight controller', () => {
    rejectedBuild('/tests/static/futures_basis_research/main.tsx', "import '../../../src/features/futures_basis_research/hooks/usePreflight'", /Forbidden static presentation dependency/)
  }, 35000)
  it('rejects the Production HTTP client', () => {
    rejectedBuild('/tests/static/futures_basis_research/main.tsx', "import '../../../src/features/futures_basis_research/api/futuresBasis'", /Forbidden static presentation dependency/)
  }, 35000)
  it('rejects the Production Page composition root', () => {
    rejectedBuild('/tests/static/futures_basis_research/main.tsx', "import '../../../src/features/futures_basis_research/page/FuturesBasisPage'", /Forbidden static presentation dependency/)
  }, 35000)
  it('rejects an indirect dynamic HTTP import through the shared provider', () => {
    rejectedBuild('/src/app/AppUiProvider.tsx', "void import('../shared/http/protectedRequest')", /Forbidden static presentation dependency/)
  }, 35000)
  it('rejects unresolvable dynamic runtime imports rather than trusting tree shaking', () => {
    rejectedBuild('/tests/static/futures_basis_research/main.tsx', 'const runtimeModule = window.location.search; void import(runtimeModule)', /Unresolved static presentation import/)
  }, 35000)
})
