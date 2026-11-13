import { fileURLToPath } from 'node:url'
import { mergeConfig } from 'vite'
import { staticPresentationIsolation } from './scripts/staticPresentationIsolation.ts'
import demoConfig from './vite.demo.config.ts'

// Test-only artifact; public V1 entry/output and workflow are unchanged.
export default mergeConfig(demoConfig, {
  root: fileURLToPath(new URL('./src/features/futures_basis_research/testing/static', import.meta.url)),
  plugins: [staticPresentationIsolation(
    'futures_basis_research',
    /(api\/futuresBasis\.ts|hooks\/useFuturesBasis\.ts|hooks\/usePreflight\.ts|page\/FuturesBasisPage\.tsx)$/,
    ['src/app/routeInventory.ts', 'src/demo/shell/hashRoutes.ts', 'src/demo/futures_basis/report.v1.json'],
  )],
  build: { outDir: fileURLToPath(new URL('./.build/tests/futures-basis', import.meta.url)) },
})
