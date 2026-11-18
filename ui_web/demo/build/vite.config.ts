import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { researchMapValidation } from '../../research-map/vite.ts'
import { fileURLToPath } from 'node:url'
import { dependencyInventory } from './dependencyInventory.mjs'
export default defineConfig({
  root: fileURLToPath(new URL('../runtime', import.meta.url)),
  base: '/hg-market-state-lab/', publicDir: false, envDir: false,
  cacheDir: fileURLToPath(new URL('../../.build/cache/demo', import.meta.url)),
  plugins: [researchMapValidation(), react(), {
    name: 'demo-runtime-isolation',
    generateBundle() {
      const modules = [...this.getModuleIds()].map(id => id.replaceAll('\\', '/'))
      for (const id of modules) {
        if (id.includes('/node_modules/')) continue
        if (/\/src\/features\/[^/]+\/api\//.test(id) && !/\/(validate[^/]*\.ts|[^/]+\.(openapi\.json|generated\.ts))$/.test(id)) this.error('Forbidden Demo API dependency: ' + id)
        if (/\/src\/features\/[^/]+\/page\//.test(id) && !/Presentation\.tsx$/.test(id)) this.error('Forbidden Demo page controller: ' + id)
        if (/\/(testing|tests)\/|\.fixture|\/src\/shared\/http\/|\/src\/app\/(auth|App\.)|\/api\/(auth|backtesting|futuresBasis|research|optionChain|premiumPlane)\.ts|\/hooks\/(useBacktesting|usePreflight|useFuturesBasisResearch|useResearchCatalog|useResearchExplorer)\.ts/.test(id)) this.error('Forbidden Demo dependency: ' + id)
      }
      this.emitFile({ type: 'asset', fileName: 'runtime-dependencies.json', source: JSON.stringify(dependencyInventory(modules, fileURLToPath(new URL('../../../', import.meta.url))), null, 2) })
    },
  }],
})
