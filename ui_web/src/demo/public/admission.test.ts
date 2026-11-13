import { expect, it } from 'vitest'
import { admitPublicEnvelope, validatePublicRecord, gates, categories, type PublicEnvelope, type PublicIdentity, type PublicReview } from './admission'
import { producers } from '../static/results'
const identity: PublicIdentity = { id: 'chain', revision: 1, delivery: 'static', origin: 'real_market', execution: 'historical_embedded_result', provider: 'Tushare', producer: producers.chain, sourceRevision: 'a'.repeat(40), inputFingerprint: null, evidenceDigest: 'a'.repeat(64), resultDigest: 'b'.repeat(64), rights: 'user_directed_public', publicRights: 'USER_DIRECTED', disclosure: 'Historical source and coverage' }
const review: PublicReview = { resultDigest: identity.resultDigest, channels: ['github_repository', 'github_pages'], categories: [...categories], licenseBasis: 'Repository owner explicitly directs publication; third-party permission unverified', conditions: 'Keep source truthful; exclude private evidence', expiresAt: null, gates: Object.fromEntries(gates.map(g=>[g,{status:g === 'publicationRights' ? 'USER_DIRECTED' : 'PASS', reviewer:'Codex',reviewedAt:'2026-11-13T00:00:00+08:00',reason:'Bound evidence',evidence:'evidence/review.md',evidenceDigest:'c'.repeat(64)}])) as PublicReview['gates'] }
it('binds explicit distribution decision without fabricating third-party clearance', () => {
  expect(()=>validatePublicRecord(identity,review,'chain')).not.toThrow()
  for(const mutation of [{rights:'private'},{publicRights:'PASS'},{origin:'synthetic'},{producer:'fake'},{resultDigest:'x'},{sourceRevision:''}]) expect(()=>validatePublicRecord({...identity,...mutation} as PublicIdentity,review,'chain')).toThrow()
  for(const mutation of [{resultDigest:'a'.repeat(64)},{channels:['github_pages']},{categories:[]},{expiresAt:'2020-01-01'},{gates:{...review.gates,publicationRights:{...review.gates.publicationRights,status:'PASS'}}}]) expect(()=>validatePublicRecord(identity,{...review,...mutation} as PublicReview,'chain')).toThrow()
  for(const gate of gates) expect(()=>validatePublicRecord(identity,{...review,gates:{...review.gates,[gate]:{...review.gates[gate],evidence:'../private.md'}}},'chain')).toThrow()
})
it('rejects private envelope and incomplete public inventories before mounting', async()=>{
  await expect(admitPublicEnvelope({profile:'wp-b-private-static-v1',examples:{}} as unknown as PublicEnvelope)).rejects.toThrow()
  await expect(admitPublicEnvelope({profile:'portfolio-public-v2-v1',examples:{chain:{identity,json:'{}',review}}} as PublicEnvelope)).rejects.toThrow()
})
