import { mkdir, mkdtemp, readdir, readFile, rm } from 'node:fs/promises'
import { resolve } from 'node:path'
import { createHash } from 'node:crypto'

export async function isolatedOutput() {
  await mkdir('.build', { recursive: true })
  const outputRoot = await mkdtemp(resolve('.build/ddb-build-test-'))
  return {
    outputRoot, work: resolve(outputRoot, 'demo-collection'),
    output: resolve(outputRoot, 'demo'),
    cleanup: () => rm(outputRoot, { recursive: true, force: true }),
  }
}

// Read existing developer output without creating or replacing any sentinel there.
export async function developerOutputDigest() {
  const hash = createHash('sha256')
  async function visit(path: string) {
    let entries
    try { entries = await readdir(path, { withFileTypes: true }) }
    catch (error: any) { if (error.code === 'ENOENT') { hash.update('absent'); return }; throw error }
    for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
      hash.update(entry.name)
      if (entry.isDirectory()) await visit(resolve(path, entry.name))
      else if (entry.isFile()) hash.update(await readFile(resolve(path, entry.name)))
      else throw new Error('unexpected developer output entry')
    }
  }
  await visit(resolve('.build/demo'))
  return hash.digest('hex')
}
