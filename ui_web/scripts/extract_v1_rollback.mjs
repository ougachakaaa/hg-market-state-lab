import { readFileSync } from 'node:fs'
import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { resolve } from 'node:path'
import { sha } from './public_release.mjs'
const archive = new URL('../src/demo/futures_basis/rollback-v1.tar.gz',import.meta.url)
const receipt = JSON.parse(readFileSync(new URL('../src/demo/futures_basis/rollback-inventory.json',import.meta.url)))
assert.equal(sha(readFileSync(archive)),receipt.archiveDigest)
// Digest binds the reviewed archive before tar can touch the destination.
execFileSync('tar',['-xzf',archive.pathname,'-C',resolve(process.argv[2])])
