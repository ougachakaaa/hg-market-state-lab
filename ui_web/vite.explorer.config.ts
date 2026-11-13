import { fileURLToPath } from 'node:url'
import { mergeConfig } from 'vite'
import { staticPresentationIsolation } from './scripts/staticPresentationIsolation.ts'
import demoConfig from './vite.demo.config.ts'

// Test-only artifact; public V1 entry/output and workflow are unchanged.
export default mergeConfig(demoConfig, {
  root: fileURLToPath(new URL('./src/features/research_explorer/testing/static', import.meta.url)),
  plugins: [staticPresentationIsolation(
    'research_explorer',
    /(api\/research\.ts|hooks\/useExplorer\.ts|page\/ResearchExplorerPage\.tsx)$/,
    ['../market_research/tests/fixtures/publication_visualization_v1.json'],
  )],
  build: { outDir: fileURLToPath(new URL('./.build/tests/explorer', import.meta.url)) },
})
