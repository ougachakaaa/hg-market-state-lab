import { spawnSync } from 'node:child_process'
import { describe, expect, it } from 'vitest'

function rejectedBuild(target: string, appended: string, reason: RegExp) {
  // Load the actual config in Node, outside Vitest's browser module transforms.
  // Injection stays in memory; production files and build artifacts are untouched.
  const script = `
    import { build, loadConfigFromFile } from 'vite'
    const loaded = await loadConfigFromFile({ command: 'build', mode: 'production' }, 'tests/config/vite.catalog.config.ts')
    const injection = {
      name: 'test-forbidden-catalog-import', enforce: 'pre',
      transform(code, id) { if (id.endsWith(${JSON.stringify(target)})) return code + '\\n' + ${JSON.stringify(appended)} },
    }
    await build({
      ...loaded.config, configFile: false, logLevel: 'silent',
      plugins: [injection, ...loaded.config.plugins],
      build: { ...loaded.config.build, write: false },
    })
  `
  const result = spawnSync(process.execPath, ['--input-type=module'], {
    input: script, encoding: 'utf8', timeout: 20000,
  })
  expect(result.error).toBeUndefined()
  expect(result.status).toBe(1)
  expect(result.stdout + result.stderr).toMatch(reason)
}

describe('static Research Overview build isolation rejects reachable runtime imports', () => {
  it('rejects a direct Auth import even when none of its exports are used', () => {
    rejectedBuild('/tests/static/research_catalog/main.tsx', "import '../../../src/app/auth/useAuthentication'", /Forbidden static presentation dependency/)
  }, 25000)
  it('rejects the production catalog controller even when tree shaking could discard it', () => {
    rejectedBuild('/tests/static/research_catalog/main.tsx', "import '../../../src/features/research_catalog/hooks/useCatalog'", /Forbidden static presentation dependency/)
  }, 25000)
  it('rejects the production catalog HTTP client', () => {
    rejectedBuild('/tests/static/research_catalog/main.tsx', "import '../../../src/features/research_catalog/api/catalog'", /Forbidden static presentation dependency/)
  }, 25000)
  it('rejects a sibling Research Explorer runtime import', () => {
    rejectedBuild('/tests/static/research_catalog/main.tsx', "import '../../../src/features/research_explorer/page/ResearchExplorerPage'", /Forbidden static presentation dependency/)
  }, 25000)
  it('rejects an indirect dynamic HTTP import through the shared provider', () => {
    rejectedBuild('/src/app/AppUiProvider.tsx', "void import('../shared/http/protectedRequest')", /Forbidden static presentation dependency/)
  }, 25000)
  it('rejects unresolvable dynamic runtime imports rather than trusting tree shaking', () => {
    rejectedBuild('/tests/static/research_catalog/main.tsx', 'const runtimeModule = window.location.search; void import(runtimeModule)', /Unresolved static presentation import/)
  }, 25000)
})
