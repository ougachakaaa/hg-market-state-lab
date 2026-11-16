import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, writeFile, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createHash } from 'node:crypto'
import { acceptRelease, assertReleaseRun, parseVerifyArgs, downloadArtifact, assertArtifacts } from './verifyRelease.mjs'
import { execute, journal } from './execution.mjs'
import { publish } from './publish.mjs'
const sha = 'a'.repeat(40), repo = 'owner/repo'
const run = { id: 123, repository: {full_name:repo}, path: '.github/workflows/deploy-demo-pages.yml', head_branch:'release/demo-pages', status:'completed', conclusion:'success', head_sha:sha, run_attempt:2, html_url:'https://github.com/owner/repo/actions/runs/123' }
const bytes = Buffer.from('{}\n'), hash = createHash('sha256').update(bytes).digest('hex')
const gate = { result:'PASS', sourceCommit:sha, manifestSha256:hash, requirementsSha256:hash }

test('requires explicit numeric run and rejects ambiguous CLI flags', () => {
 assert.deepEqual(parseVerifyArgs(['--run','123']), {runId:'123',remote:'github'})
 for (const args of [[],['--run','latest'],['--run','123','--run','456'],['--run','123','--source','develop']]) assert.throws(() => parseVerifyArgs(args))
})
test('rejects another repository, workflow, branch, failed/incomplete run and wrong ID', () => {
 for(const patch of [{repository:{full_name:'other/repo'}},{path:'other.yml'},{head_branch:'develop'},{conclusion:'failure'},{status:'in_progress'},{id:456}]) assert.throws(() => assertReleaseRun({...run,...patch},repo,123))
})
async function setup(work) {
 const directory=await mkdtemp(join(tmpdir(),'release-verify-test-'))
 try {
  for(const [name,data] of [['release-evidence',gate],['demo-receipt',{sourceCommit:sha}]]) {
   await mkdir(join(directory,name)); await writeFile(join(directory,name,name==='release-evidence'?'demo-release.json':'demo-receipt.json'),JSON.stringify(data))
  }
  const stages=[], calls=[]
  const options={run,repo,runId:123,
   api:async path => path.includes('/jobs?') ? {jobs:[{html_url:run.html_url+'/job/2'}]} : path.startsWith('deployments?') ? [{id:7,sha}] : [{state:'success',environment_url:'https://example.test/',log_url:run.html_url+'/job/2'}],
   download:async name => {calls.push(name); return join(directory,name)},
   committed:async () => bytes, checkpoint:async patch => {stages.push(patch)},
   artifact:async () => {calls.push('artifact')},online:async () => {calls.push('online')},browser:async () => {calls.push('browser')},
  }
  await work({directory,options,calls,stages})
 } finally {await rm(directory,{recursive:true,force:true})}
}
test('existing deployment verification uses only CI artifacts and online acceptance, saving all stages', async () => setup(async ({options,calls,stages}) => {
 await acceptRelease(options)
 assert.deepEqual(calls,['release-evidence','demo-receipt','verified-demo','artifact','online','browser'])
 assert.equal(stages.at(-1).status,'RELEASED_AND_VERIFIED')
 assert.equal(stages[0].runAttempt,2)
}))
test('rejects gate identity mismatch without continuing to site or online acceptance', async () => setup(async ({directory,options,calls}) => {
 await writeFile(join(directory,'release-evidence/demo-release.json'),JSON.stringify({...gate,sourceCommit:'b'.repeat(40)}))
 await assert.rejects(acceptRelease(options),/SHA mismatch/)
 assert.ok(!calls.includes('verified-demo'))
}))
test('rejects changed Requirements, failed artifact verification and overwritten public version without retry', async () => setup(async ({options,calls}) => {
 await assert.rejects(acceptRelease({...options,committed:async()=>Buffer.from('changed')}),/Requirements/)
 calls.length=0
 await assert.rejects(acceptRelease({...options,artifact:async()=>{throw Error('bad receipt')}}),/bad receipt/)
 assert.ok(!calls.includes('online'))
 calls.length=0
 await assert.rejects(acceptRelease({...options,online:async()=>{throw Error('public SHA mismatch')}}),/public SHA mismatch/)
 assert.ok(!calls.includes('browser'))
}))
test('rejects a successful deployment from another run attempt', async () => setup(async ({options}) => {
 await assert.rejects(acceptRelease({...options,api:async path=>path.includes('/jobs?')?{jobs:[]}:await options.api(path)}),/deployment/)
}))
test('download retries only network failure into a fresh directory and checkpoints each attempt', async () => {
 const parent=await mkdtemp(join(tmpdir(),'release-download-test-'))
 try {
  const attempts=[]
  const result=await downloadArtifact({runId:123,name:'verified-demo',parent,checkpoint:async patch=>attempts.push(patch),gh:async()=>{if(attempts.length===1)throw Object.assign(Error('timeout'),{transient:true})}})
  assert.equal(attempts.length,2); assert.notEqual(attempts[0].downloadDirectory,result)
  let count=0
  await assert.rejects(downloadArtifact({runId:123,name:'verified-demo',parent,checkpoint:async()=>{},gh:async()=>{count++;throw Error('permission denied')}}),/permission denied/)
  assert.equal(count,1)
  count=0
  await assert.rejects(downloadArtifact({runId:123,name:'verified-demo',parent,checkpoint:async()=>{},gh:async()=>{count++;throw Object.assign(Error('timeout'),{transient:true})}}),/timeout/)
  assert.equal(count,2)
 } finally {await rm(parent,{recursive:true,force:true})}
})
test('async execution identifies real timeout without blocking the event loop', async () => {
 await assert.rejects(execute(process.execPath,['-e','setTimeout(()=>{},10000)'],{timeout:30,label:'test timeout'}),error=>error.transient && /timeout/.test(error.message))
})
test('journal persists failure and cleanup state by run without trusting prior PASS', async () => {
 const directory=await mkdtemp(join(tmpdir(),'release-journal-test-'))
 try {
  const record=journal(directory,{runId:'123'})
  await record.save({status:'RELEASED_AND_VERIFIED'})
  await record.save({status:'NOT_VERIFIED',error:'download failed',cleanupPending:true})
  const saved=JSON.parse(await readFile(join(directory,'.build/demo-releases/123/verification.json')))
  assert.equal(saved.status,'NOT_VERIFIED');assert.equal(saved.cleanupPending,true)
 } finally {await rm(directory,{recursive:true,force:true})}
})
test('Publisher already-released path does not install, build, create worktree, push or rerun', async () => {
 const common=await mkdtemp(join(tmpdir(),'release-publisher-test-'))
 const calls=[]
 const record={state:{},async save(patch){Object.assign(this.state,patch)}}
 try {
  const command=async (program,args)=>{
   calls.push([program,...args])
   if(program==='git') {
    if(args[0]==='remote')return 'git@github.com:owner/repo.git'
    if(args.includes('--git-common-dir'))return common
    if(args[0]==='ls-remote')return `${sha}\trefs/heads/main\n${sha}\trefs/heads/release/demo-pages`
    if(args[0]==='rev-parse')return sha
    return ''
   }
   if(args[0]==='auth')return ''
   if(args[0]==='run')return JSON.stringify([{databaseId:123,headSha:sha,status:'completed',conclusion:'success',url:run.html_url}])
   const path=args[1]
   return JSON.stringify(path.endsWith('/pages')?{build_type:'workflow'}:path.endsWith('/actions/permissions')?{enabled:true}:path.endsWith('/deployment-branch-policies')?{branch_policies:[{type:'branch',name:'release/demo-pages'}]}:path.endsWith('/github-pages')?{deployment_branch_policy:{custom_branch_policies:true}}:{permissions:{push:true}})
  }
  let verified=0
  await publish([], {runCommand:command,createJournal:()=>record,verifyDeployment:async options=>{verified++;assert.equal(options.expectedSha,sha);await options.record.save({status:'RELEASED_AND_VERIFIED'})}})
  assert.equal(verified,1)
  assert.ok(!calls.some(call=>call.includes('push')||call.includes('worktree')||call.includes('cmd.exe')||call.includes('npm')||call.includes('rerun')))
 } finally {await rm(common,{recursive:true,force:true})}
})

test('missing, expired and ambiguous CI evidence cannot be replaced with local output', () => {
 const artifacts=['release-evidence','demo-receipt','verified-demo'].map(name=>({name,expired:false}))
 assertArtifacts({artifacts})
 assert.throws(()=>assertArtifacts({artifacts:artifacts.slice(1)}),/Missing/)
 assert.throws(()=>assertArtifacts({artifacts:artifacts.map(a=>({...a,expired:true}))}),/expired/)
 assert.throws(()=>assertArtifacts({artifacts:[...artifacts,artifacts[0]]}),/ambiguous/)
})
test('run-attempt change during verification prevents final PASS', async () => setup(async ({options,stages}) => {
 await assert.rejects(acceptRelease({...options,confirm:async()=>{throw Error('Run attempt changed')}}),/attempt changed/)
 assert.ok(!stages.some(stage=>stage.status==='RELEASED_AND_VERIFIED'))
}))
