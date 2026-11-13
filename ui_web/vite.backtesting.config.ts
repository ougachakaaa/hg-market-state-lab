import { fileURLToPath } from 'node:url'
import { mergeConfig } from 'vite'
import { staticPresentationIsolation } from './scripts/staticPresentationIsolation.ts'
import demoConfig from './vite.demo.config.ts'

// Test-only artifact; public V1 entry/output and workflow are unchanged.
export default mergeConfig(demoConfig, {
  root: fileURLToPath(new URL('./src/features/backtesting/testing/static', import.meta.url)),
  plugins: [staticPresentationIsolation(
    'backtesting',
    /(api\/backtesting\.ts|hooks\/useBacktesting\.ts|hooks\/usePreflight\.ts|page\/BacktestingPage\.tsx)$/,
  )],
  build: { outDir: fileURLToPath(new URL('./.build/tests/backtesting', import.meta.url)) },
})
