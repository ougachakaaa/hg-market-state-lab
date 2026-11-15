// Manual only: never invoke without an explicit user request.
import { configDefaults, defineConfig } from 'vitest/config'
import config from './vite.config.ts'

export default defineConfig({ ...config,
  test: { ...config.test,
    include: ['tests/isolation/**/*.test.ts', 'tests/tooling/public_release.test.ts'],
    exclude: configDefaults.exclude,
  },
})
