import { fileURLToPath } from 'node:url'
import { mergeConfig } from 'vite'
import { staticPresentationIsolation } from '../../scripts/staticPresentationIsolation.ts'
import demoConfig from './vite.static-base.ts'

// Test-only artifact; public V1 entry/output and workflow are unchanged.
export default mergeConfig(demoConfig, {
  root: fileURLToPath(new URL('../static/research_catalog', import.meta.url)),
  plugins: [staticPresentationIsolation(
    'research_catalog',
    /(api\/catalog\.ts|hooks\/useCatalog\.ts|page\/ResearchWorkspacePage\.tsx)$/,
    ['src/app/routeInventory.ts', 'src/demo/shell/hashRoutes.ts'],
  )],
  build: { outDir: fileURLToPath(new URL('../../.build/tests/catalog', import.meta.url)) },
})
