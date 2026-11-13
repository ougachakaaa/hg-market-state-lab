import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Independent static surface: no app entry, auth gate or backend proxy.
export default defineConfig({
  root: fileURLToPath(new URL('./src/demo/futures_basis', import.meta.url)),
  base: '/hg-market-state-lab/',
  publicDir: false,
  plugins: [react()],
  server: { host: '127.0.0.1' },
  preview: { host: '127.0.0.1' },
  build: {
    outDir: fileURLToPath(new URL('./dist-demo', import.meta.url)),
    emptyOutDir: true,
  },
})
