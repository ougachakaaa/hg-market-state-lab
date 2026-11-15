import { defineConfig } from 'vitest/config'
export default defineConfig({
  cacheDir: '.build/cache/demo-tests',
  test: { environment: 'node', include: ['demo/build/*.test.ts'], maxWorkers: 1 },
})
