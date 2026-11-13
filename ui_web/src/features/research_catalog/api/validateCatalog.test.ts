import { describe, expect, it } from 'vitest'
import descriptor from './catalog.fixture.json'
import {
  matchesCapabilityDetail,
  matchesCapabilityList,
  validateCapabilityDetail,
  validateCapabilityList,
  validateEmbeddedCatalog,
} from './validateCatalog'

describe('Research Capability generated-contract validation', () => {
  it('accepts the formal list and detail success responses unchanged', () => {
    const list = [descriptor]
    expect(matchesCapabilityList(list)).toBe(true)
    expect(validateCapabilityList(list)).toBe(list)
    expect(matchesCapabilityDetail(descriptor)).toBe(true)
    expect(validateCapabilityDetail(descriptor)).toBe(descriptor)
  })

  it('rejects malformed success payloads and altered readiness facts', () => {
    const malformedDetail = structuredClone(descriptor)
    Reflect.deleteProperty(malformedDetail, 'purpose')
    expect(matchesCapabilityDetail(malformedDetail)).toBe(false)
    expect(() => validateCapabilityDetail(malformedDetail)).toThrow()
    expect(() => validateCapabilityList([{ id: 'fabricated' }])).toThrow()
    expect(matchesCapabilityList({ ...descriptor, live_readiness: 'available' })).toBe(false)
    expect(matchesCapabilityDetail({ ...descriptor, status: 'available' })).toBe(false)
  })

  it('validates embedded list/detail association and exposes details by ID', () => {
    const result = validateEmbeddedCatalog({ list: [descriptor], details: [structuredClone(descriptor)] })
    expect(result.capabilities).toEqual([descriptor])
    expect(result.details.get(descriptor.id)).toEqual(descriptor)
  })

  it('rejects duplicate list identities', () => {
    expect(() => validateEmbeddedCatalog({ list: [descriptor, descriptor], details: [] }))
      .toThrow(/Duplicate embedded capability id/)
  })

  it('rejects duplicate detail identities', () => {
    expect(() => validateEmbeddedCatalog({ list: [descriptor], details: [descriptor, descriptor] }))
      .toThrow(/Duplicate embedded capability detail/)
  })

  it('rejects a detail that does not belong to the embedded list', () => {
    expect(() => validateEmbeddedCatalog({
      list: [descriptor],
      details: [{ ...descriptor, id: 'not_in_list' }],
    })).toThrow(/not listed/)
  })

  it('allows a list item with no embedded detail instead of fabricating one', () => {
    const result = validateEmbeddedCatalog({ list: [descriptor], details: [] })
    expect(result.details.size).toBe(0)
  })

  it('rejects an invalid or duplicate detection payload rather than accepting a partial catalog', () => {
    expect(() => validateEmbeddedCatalog({ list: [descriptor], details: {} as unknown as readonly unknown[] }))
      .toThrow(/Invalid embedded Research catalog/)
    expect(() => validateEmbeddedCatalog({
      list: [descriptor],
      details: [{ id: 'broken' }],
    })).toThrow()
  })
})
