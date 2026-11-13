import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import assert from 'node:assert/strict'
import { inventory, sha } from './public_release.mjs'
import { assertPublicAsset } from './public_asset_safety.mjs'
const receipt = JSON.parse(readFileSync(new URL('../src/demo/futures_basis/rollback-inventory.json',import.meta.url)))
const root = resolve(process.argv[2])
const files=inventory(root)
assert.deepEqual(files,receipt.files)
for(const f of files) assertPublicAsset(readFileSync(resolve(root,f.file),'utf8'),f.file)
assert.equal(receipt.status,'PASS')
console.log(`PASS: reviewed V1 recovery artifact ${receipt.archiveDigest}; file inventory ${sha(JSON.stringify(files))}`)
