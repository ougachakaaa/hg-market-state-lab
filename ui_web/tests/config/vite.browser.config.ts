// Browser regression startup only: scan the Online graph, not Demo virtual entries.
import { fileURLToPath } from 'node:url'
import { mergeConfig } from 'vite'
import onlineConfig from '../../vite.config.ts'

export default mergeConfig(onlineConfig, {
  optimizeDeps: { entries: [fileURLToPath(new URL('../../index.html', import.meta.url))] },
  // Only the isolated acceptance runners set this; other suites keep Online defaults.
  ...(process.env.LAB_BROWSER_API_ORIGIN ? {
    server: { proxy: Object.fromEntries(Object.entries(onlineConfig.server!.proxy!).map(([path, proxy]) => [
      path, typeof proxy === 'string' ? process.env.LAB_BROWSER_API_ORIGIN : {
        ...proxy, target: process.env.LAB_BROWSER_API_ORIGIN,
      },
    ])) },
  } : {}),
})
