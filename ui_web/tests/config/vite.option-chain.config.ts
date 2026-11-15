import { fileURLToPath } from 'node:url'
import { mergeConfig } from 'vite'
import { staticPresentationIsolation } from '../../scripts/staticPresentationIsolation.ts'
import demoConfig from './vite.static-base.ts'

// Test-only artifact; public V1 entry/output and workflow are unchanged.
export default mergeConfig(demoConfig, {
  root: fileURLToPath(new URL('../static/mo_option_chain', import.meta.url)),
  plugins: [staticPresentationIsolation('mo_option_chain', /(api\/moOptionChain\.ts|hooks\/useOptionChain\.ts|page\/OptionChainPage\.tsx|\/index\.ts)$/)],
  build: { outDir: fileURLToPath(new URL('../../.build/tests/option-chain', import.meta.url)) },
})
