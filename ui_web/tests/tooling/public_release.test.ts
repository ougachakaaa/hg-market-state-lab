import { expect, it } from 'vitest'
import { spawnSync } from 'node:child_process'
it('rejects mutation, extra assets, symlinks, credentials and private contents', () => {
  const result = spawnSync(process.execPath, ['--input-type=module'], { encoding: 'utf8', input: `
    import assert from 'node:assert/strict'
    import { mkdtempSync, writeFileSync, rmSync, symlinkSync } from 'node:fs'
    import { tmpdir } from 'node:os'
    import { resolve } from 'node:path'
    import { inventory, sha, verifyArtifact, assertPublicV2Asset } from './scripts/artifact_integrity.mjs'
    const dir = mkdtempSync(resolve(tmpdir(), 'release-integrity-'))
    try {
      writeFileSync(resolve(dir,'index.html'), '<html>Public</html>')
      const files=inventory(dir), receipt={files, artifactDigest:sha(JSON.stringify(files))}
      verifyArtifact(dir,receipt)
      writeFileSync(resolve(dir,'index.html'),'mutated')
      assert.throws(()=>verifyArtifact(dir,receipt),/changed/)
      writeFileSync(resolve(dir,'index.html'),'<html>Public</html>')
      writeFileSync(resolve(dir,'extra.js'),'extra')
      assert.throws(()=>verifyArtifact(dir,receipt),/changed/)
      rmSync(resolve(dir,'extra.js')); symlinkSync(dir,resolve(dir,'alias'),'junction')
      assert.throws(()=>inventory(dir),/symlink/)
      for (const [text,name] of [['/home/user/private','app.js'],['wp-b-private-static-v1','app.js'],['{}','app.js.map'],['ghp_'+'a'.repeat(40),'app.js']]) assert.throws(()=>assertPublicV2Asset(Buffer.from(text),name))
      assert.doesNotThrow(()=>assertPublicV2Asset(Buffer.from('2026-11-11 Historical Real Market Data'),'app.js'))
    } finally { rmSync(dir,{recursive:true,force:true}) }
  ` })
  expect(result.status, result.stdout + result.stderr).toBe(0)
})
