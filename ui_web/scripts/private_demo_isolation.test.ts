import { expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { resolve } from 'node:path'

it('rejects production execution dependencies before emitting a private artifact', () => {
  const result = spawnSync(process.execPath, ['--input-type=module'], { encoding: 'utf8', input: `
    import assert from 'node:assert/strict'
    import { resolve } from 'node:path'
    import { privateDemoIsolation } from './scripts/private_demo_isolation.mjs'
    for (const module of ['src/app/auth/api/auth.ts', 'src/shared/http/protectedRequest.ts', 'src/features/backtesting/hooks/useBacktesting.ts', 'src/features/research_catalog/api/catalog.ts', 'src/features/mo_option_chain/page/OptionChainPage.tsx']) {
      assert.throws(() => privateDemoIsolation().generateBundle.call({ getModuleIds: () => [resolve(module)], error: message => { throw new Error(message) }, emitFile: () => {} }), /Forbidden private static dependency/)
    }
  ` })
  expect(result.status, result.stdout + result.stderr).toBe(0)
})
it('keeps public V1 entry, output and Pages upload independent of private admission', () => {
  const config = readFileSync(resolve('vite.demo.config.ts'), 'utf8')
  expect(config).toContain('./src/demo/futures_basis')
  expect(config).toContain('./dist-demo')
  expect(config).not.toMatch(/private|process\.env/)
  const workflow = readFileSync(resolve('../.github/workflows/deploy-demo-pages.yml'), 'utf8')
  expect(workflow).toContain('ui_web/dist-demo')
  expect(workflow).not.toContain('demo:build:private')
})
