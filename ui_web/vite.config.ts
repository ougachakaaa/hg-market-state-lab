import react from '@vitejs/plugin-react'
import { researchMapValidation } from './research-map/vite.ts'
import { configDefaults, defineConfig } from 'vitest/config'

const localHost = '127.0.0.1'
const localPort = 5173
// Local access validates the browser-facing Host against Origin or Referer.
const backendProxy = { target: 'http://127.0.0.1:8011', changeOrigin: false }

// https://vite.dev/config/
export default defineConfig({
  cacheDir: '.build/cache/vite',
  build: { outDir: '.build/online' },
  plugins: [{
    name: 'online-loopback',
    apply: 'serve',
    configResolved({ server, preview }) {
      if (server.host !== localHost || server.port !== localPort || !server.strictPort) {
        throw new Error('The online development server requires 127.0.0.1:5173 and a fixed port.')
      }
      if (preview.host !== localHost) {
        throw new Error('The online preview server requires a loopback listener.')
      }
    },
  }, researchMapValidation(), react()],
  server: {
    host: localHost,
    port: localPort,
    strictPort: true,
    proxy: {
      '/api/data': {
        ...backendProxy,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/api/backtesting': {
        ...backendProxy,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/api/research': {
        ...backendProxy,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/auth': backendProxy,
      '/mo-option-chain': backendProxy,
      '/mo-option-premium-plane': backendProxy,
    },
  },
  test: {
    // Manual diagnostics never run through npm test.
    exclude: [...configDefaults.exclude, 'tests/isolation/**', 'tests/tooling/public_release.test.ts', 'demo/build/build.test.ts', 'demo/build/runtime.test.ts'],
    // JSDOM + Ant Design integration tests are CPU-heavy. Bound scheduling,
    // retain per-file isolation and the default 5s regression deadline.
    maxWorkers: 1,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
