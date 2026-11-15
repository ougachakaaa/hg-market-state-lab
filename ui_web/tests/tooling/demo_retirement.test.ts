import { expect, it } from 'vitest'
import { existsSync, readFileSync } from 'node:fs'
it('keeps one formal build entry and retired data absent', () => {
  for (const path of ['src/demo/futures_basis/report.v1.json', 'src/demo/public/examples/package.json', 'src/demo/futures_basis/rollback-v1.tar.gz', 'vite.demo.config.ts']) expect(existsSync(path)).toBe(false)
  const pkg = JSON.parse(readFileSync('package.json', 'utf8'))
  expect(pkg.scripts['demo:build']).toBe('node demo/build/build.mjs')
  expect(pkg.scripts['demo:preview']).toBe('node demo/build/preview.mjs')
  const workflow = readFileSync('../.github/workflows/deploy-demo-pages.yml', 'utf8')
  expect(workflow).not.toMatch(/deploy-pages@|upload-pages-artifact@|rollback|recovery/)
  expect(workflow).toContain('exit 1')
})
