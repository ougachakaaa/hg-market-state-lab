import { expect, it } from 'vitest'
import { admitPrivateEnvelope, exampleKeys, producers, validateIdentity, type ExampleIdentity, type PrivateEnvelope } from './admission'
// Explicitly synthetic contract probes; never a real-market Example or build input.
function identity(id: typeof exampleKeys[number]): ExampleIdentity {
  return { id, revision: 1, delivery: 'static', origin: 'real_market', execution: 'historical_embedded_result', rights: 'private', publicRights: 'BLOCKED', provider: id === 'catalog' ? 'formal_capability_facade' : 'Tushare', producer: producers[id], sourceRevision: 'a'.repeat(40), evidenceDigest: 'a'.repeat(64), resultDigest: 'a'.repeat(64), inputFingerprint: ['chain', 'premium', 'catalog'].includes(id) ? null : 'a'.repeat(64) }
}
it.each(exampleKeys)('checks the complete identity contract for %s', key => {
  expect(() => validateIdentity(identity(key), key)).not.toThrow()
  for (const mutation of [{ origin: 'synthetic' }, { rights: 'cleared_public' }, { publicRights: 'PASS' }, { producer: 'unreviewed' }, { revision: 2 }, { id: 'foreign' }, { sourceRevision: '' }, { evidenceDigest: '' }, { resultDigest: '' }]) {
    expect(() => validateIdentity({ ...identity(key), ...mutation } as ExampleIdentity, key)).toThrow()
  }
})
it('rejects incomplete inventories and stale digests before feature mounting', async () => {
  const envelope = { profile: 'wp-b-private-static-v1', examples: Object.fromEntries(exampleKeys.map(key => [key, { identity: identity(key), json: '{}' }])) } as PrivateEnvelope
  await expect(admitPrivateEnvelope(envelope)).rejects.toThrow('digest mismatch')
  delete (envelope.examples as Partial<PrivateEnvelope['examples']>).basis
  await expect(admitPrivateEnvelope(envelope)).rejects.toThrow('Invalid private static package')
})
