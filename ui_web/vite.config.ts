import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    proxy: {
      '/api/backtesting': {
        target: 'http://127.0.0.1:8011',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/api/research': {
        target: 'http://127.0.0.1:8011',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/auth': 'http://127.0.0.1:8011',
      '/mo-option-chain': 'http://127.0.0.1:8011',
      '/mo-option-premium-plane': 'http://127.0.0.1:8011',
    },
  },
  test: {
    // JSDOM + Ant Design integration tests are CPU-heavy. Bound scheduling,
    // retain per-file isolation and the default 5s regression deadline.
    maxWorkers: 1,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
