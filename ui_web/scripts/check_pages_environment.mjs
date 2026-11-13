import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const env = JSON.parse(readFileSync(process.argv[2])), policies = JSON.parse(readFileSync(process.argv[3]))
assert.equal(env.name, 'github-pages')
assert.equal(env.deployment_branch_policy?.custom_branch_policies, true, 'Pages Environment must use reviewed custom deployment branch rules')
assert.ok(env.protection_rules.some(rule => rule.type === 'branch_policy'), 'Pages branch protection absent')
assert.ok(policies.branch_policies.some(p => p.name === 'main' && p.type === 'branch'), 'Protected Pages Environment must permit main')
console.log(JSON.stringify({ status:'PASS', environment:env.name, rules:env.protection_rules, branches:policies.branch_policies }))
