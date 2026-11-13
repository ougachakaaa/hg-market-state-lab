// Browser regression startup only: scan the Online graph, not Demo virtual entries.
import { fileURLToPath } from 'node:url'
import { mergeConfig } from 'vite'
import onlineConfig from '../../vite.config.ts'

export default mergeConfig(onlineConfig, {
  optimizeDeps: { entries: [fileURLToPath(new URL('../../index.html', import.meta.url))] },
})
