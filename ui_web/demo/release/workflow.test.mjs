import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const workflow = readFileSync(new URL('../../../.github/workflows/deploy-demo-pages.yml', import.meta.url), 'utf8')
test('Pages trigger is dedicated release push only', () => {
  const trigger = workflow.slice(workflow.indexOf('on:'), workflow.indexOf('permissions:'))
  assert.match(trigger, /push:\s+branches:\s+- release\/demo-pages/)
  assert.doesNotMatch(trigger, /workflow_dispatch|main|develop|pull_request/)
})
test('CI independently gates main ancestry and exact triggering checkout', () => {
  assert.match(workflow, /ref: \$\{\{ github.sha \}\}/)
  assert.match(workflow, /merge-base --is-ancestor "\$RELEASE_SHA" refs\/remotes\/origin\/main/)
  assert.match(workflow, /npm run demo:release-check/)
})
test('deploy verifies transferred bytes without build and confines write permissions', () => {
  const [build, deploy] = workflow.split('\n  deploy:')
  assert.doesNotMatch(build, /pages: write|id-token: write/)
  assert.match(deploy, /needs: build/)
  assert.match(deploy, /demo_artifact.mjs verify/)
  assert.doesNotMatch(deploy, /npm ci|demo:build|demo:release-check/)
  assert.match(deploy, /pages: write/)
})
