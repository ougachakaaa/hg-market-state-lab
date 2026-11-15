import { expect, it } from 'vitest'
import { spawnSync } from 'node:child_process'

it('rejects production execution dependencies before emitting a private artifact', () => {
  const result = spawnSync(process.execPath, ['--input-type=module'], { encoding: 'utf8', input: `
    import assert from 'node:assert/strict'
    import { resolve } from 'node:path'
    import { staticRuntimeIsolation } from './scripts/static_runtime_isolation.mjs'
    for (const module of ['src/app/auth/api/auth.ts', 'src/shared/http/protectedRequest.ts', 'src/features/backtesting/hooks/useBacktesting.ts', 'src/features/research_catalog/api/catalog.ts', 'src/features/mo_option_chain/page/OptionChainPage.tsx']) {
      assert.throws(() => staticRuntimeIsolation().generateBundle.call({ getModuleIds: () => [resolve(module)], error: message => { throw new Error(message) }, emitFile: () => {} }), /Forbidden static dependency/)
    }
  ` })
  expect(result.status, result.stdout + result.stderr).toBe(0)
})
