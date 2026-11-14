import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { fileURLToPath } from 'node:url'
export default defineConfig({
  cacheDir: fileURLToPath(new URL('../../.build/cache/vite-static', import.meta.url)),
  base: '/hg-market-state-lab/', publicDir: false, envDir: false,
  plugins: [react()], server: { host: '127.0.0.1' }, preview: { host: '127.0.0.1' },
  build: { emptyOutDir: true },
})
