import { expect, it } from 'vitest'
import { spawnSync } from 'node:child_process'
import { existsSync, readFileSync } from 'node:fs'
it('rejects Demo builds without generating or reading retired data', () => {
  const result = spawnSync(process.execPath, ['scripts/demo_build_blocked.mjs'], { encoding: 'utf8' })
  expect(result.status).toBe(1)
  expect(result.stderr).toContain('BLOCKED:')
  for (const path of ['src/demo/futures_basis/report.v1.json', 'src/demo/public/examples/package.json', 'src/demo/futures_basis/rollback-v1.tar.gz', 'vite.demo.config.ts']) expect(existsSync(path)).toBe(false)
  const pkg = JSON.parse(readFileSync('package.json', 'utf8'))
  expect(Object.keys(pkg.scripts).filter(k => k.startsWith('demo:'))).toEqual(['demo:build'])
  const workflow = readFileSync('../.github/workflows/deploy-demo-pages.yml', 'utf8')
  expect(workflow).not.toMatch(/deploy-pages@|upload-pages-artifact@|rollback|recovery/)
  expect(workflow).toContain('exit 1')
})
