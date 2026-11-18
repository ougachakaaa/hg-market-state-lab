// @vitest-environment node
import { describe, expect, it } from 'vitest'
import definition from './map.json'
import type { ResearchMap } from './definition'
import { validateResearchMap } from './validate'

const graph = () => structuredClone(definition) as ResearchMap

describe('Strategy Research Map validation', () => {
  it('admits the initial document and feedback cycle', () => {
    const map = validateResearchMap(definition)
    expect(map.nodes.map(({ id }) => id)).toEqual(['S0', 'D0', 'B0', 'E0', 'AT0', 'A1', 'H1', 'O1', 'V1'])
    expect(map.edges).toContainEqual({ from: 'V1', to: 'H1', kind: 'feedback' })
  })

  it('requires document fields and rejects duplicate node IDs', () => {
    const map = graph()
    expect(() => validateResearchMap({ nodes: [{ id: 'A2' }], edges: [] })).toThrow(/required property/)
    map.nodes.push(map.nodes[0])
    expect(() => validateResearchMap(map)).toThrow(/duplicate node S0/)
  })

  it.each([
    [{ from: 'S0', to: 'Z99', kind: 'motivates' }, /dangling edge/],
    [{ from: 'S0', to: 'S0', kind: 'feedback' }, /self edge/],
    [{ from: 'S0', to: 'D0', kind: 'dependency' }, /duplicate edge/],
    [{ from: 'AT0', to: 'S0', kind: 'dependency' }, /dependency cycle/],
  ] as const)('rejects invalid edge %j', (edge, message) => {
    const map = graph()
    map.edges.push(edge)
    expect(() => validateResearchMap(map)).toThrow(message)
  })

  it.each([
    [{ kind: 'navigation', target: 'workspace', value: '/research/does-not-exist' }, /unknown shared workspace/],
    [{ kind: 'navigation', target: 'workspace', value: '/research/futures-basis?run_id=private' }, /must match pattern/],
    [{ kind: 'source', target: 'repository', value: 'docs/../README.md' }, /must match pattern/],
    [{ kind: 'source', target: 'repository', value: 'market_research/DOES_NOT_EXIST.md' }, /missing or linked/],
    [{ kind: 'report', target: 'repository', value: 'market_research/ARCHITECTURE.md' }, /invalid report reference/],
    [{ kind: 'result', target: 'repository', value: 'ui_web/demo/bundles/manifest.json' }, /unregistered Demo Bundle/],
  ] as const)('rejects invalid reference %j', (reference, message) => {
    const map = graph()
    const input = { ...map, nodes: [{ ...map.nodes[0], references: [{ ...reference, label: '测试引用' }] }, ...map.nodes.slice(1)] }
    expect(() => validateResearchMap(input)).toThrow(message)
  })

  it('rejects claiming a conclusion from a page link or unreviewed result', () => {
    const map = graph()
    const strategy = map.nodes[0]
    strategy.evidence = 'accepted'
    strategy.conclusion = { status: 'supported', summary: '测试', review: '测试验收说明' }
    expect(() => validateResearchMap(map)).toThrow(/needs a concrete result or report/)

    const study = map.nodes.find(({ id }) => id === 'A1')!
    const conclusion = { status: 'supported', summary: '测试' } as const
    const studiesOnly = { nodes: [{ ...study, conclusion }], edges: [] }
    expect(() => validateResearchMap(studiesOnly)).toThrow(/only record a reviewed conclusion/)
    studiesOnly.nodes[0].evidence = 'accepted'
    expect(() => validateResearchMap(studiesOnly)).toThrow(/needs a conclusion and review/)
  })

  it.each(['rejected', 'inconclusive'] as const)('allows a reviewed %s conclusion with locatable evidence', status => {
    const map = graph()
    const study = map.nodes.find(({ id }) => id === 'A1')!
    study.evidence = 'accepted'
    study.conclusion = { status, summary: '合成测试结论', review: '合成验收说明' }
    expect(validateResearchMap(map)).toBe(map)
  })
})
