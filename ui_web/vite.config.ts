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
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
  },
})
