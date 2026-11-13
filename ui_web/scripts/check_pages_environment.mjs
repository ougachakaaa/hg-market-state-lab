import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const env = JSON.parse(readFileSync(process.argv[2])), policies = JSON.parse(readFileSync(process.argv[3]))
assert.equal(env.name, 'github-pages')
assert.equal(env.deployment_branch_policy?.custom_branch_policies, true, 'Pages Environment must restrict deployments to main')
assert.deepEqual(policies.branch_policies.map(p=>({name:p.name,type:p.type})), [{name:'main',type:'branch'}], 'Owner must review Pages deployment branch policy: allow only main')
console.log(JSON.stringify({ status:'PASS', environment:env.name, rules:env.protection_rules, branches:policies.branch_policies }))
