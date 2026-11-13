import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import assert from 'node:assert/strict'
import { output, verifyArtifact } from './public_release.mjs'
const receipt = JSON.parse(readFileSync(resolve(output, 'release.json'), 'utf8'))
if (process.argv[2]) assert.equal(receipt.sourceSha, process.argv[2], 'Wrong release SHA')
verifyArtifact(resolve(output, 'site'), receipt)
console.log(`PASS: immutable artifact ${receipt.artifactDigest}`)
