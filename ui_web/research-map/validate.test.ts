// @vitest-environment node
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { layoutNodes, projectStrategy } from '../src/features/strategy_research_map/graph'
import type { ResearchEdge, ResearchMap, ResearchNode } from './definition'
import { mapPath, validateResearchMap } from './validate'

const graph = (): ResearchMap => JSON.parse(readFileSync(mapPath, 'utf8'))
const strategy = 'strategy-futures-long'
const baseline = 'baseline-futures-long'
const index = 'dimension-futures-long-index'
const basis = 'dimension-futures-long-basis'
const basisStudy = 'study-basis-historical'
const findingId = 'finding-basis-market-regime'
const proposedReview = { status: 'supported', summary: '测试结论', review: '测试审阅说明' } as const

function acceptedFinding(): ResearchNode {
  return {
    id: findingId, kind: 'finding', title: '测试发现', purpose: '测试 Finding 的证据引用。',
    questions: [], planning: 'defined', implementation: 'available', evidence: 'accepted',
    conclusion: proposedReview, references: [],
  }
}

describe('Strategy Research Map validation and projection', () => {
  it('admits the exact initial Strategy tree', () => {
    const map = validateResearchMap(graph())
    expect(map.nodes.map(({ id }) => id)).toEqual([
      strategy, baseline, index, basis,
      'dimension-futures-long-trading-cost', 'dimension-futures-long-drawdown', 'dimension-futures-long-margin',
      'study-index-return-distribution', 'study-market-regime', basisStudy, 'study-basis-realization',
    ])
    expect(map.edges).toEqual([
      { from: strategy, to: baseline, kind: 'branch' },
      ...map.nodes.filter(node => node.kind === 'dimension').map(node => ({ from: baseline, to: node.id, kind: 'branch' })),
      { from: index, to: 'study-index-return-distribution', kind: 'attach' },
      { from: index, to: 'study-market-regime', kind: 'attach' },
      { from: basis, to: basisStudy, kind: 'attach' },
      { from: basis, to: 'study-basis-realization', kind: 'attach' },
    ])
    expect(projectStrategy(map, strategy)).toEqual(map)
    const positionsByKind = Map.groupBy(layoutNodes(map), node => node.data.research.kind)
    const rows = [...positionsByKind.values()].map(nodes => {
      const rows = new Set(nodes.map(node => node.position.y))
      expect(rows.size).toBe(1)
      const sorted = [...nodes].sort((a, b) => a.position.x - b.position.x)
      for (let i = 1; i < sorted.length; i++) {
        expect(sorted[i].position.x).toBeGreaterThan(sorted[i - 1].position.x + sorted[i - 1].width!)
      }
      return nodes[0].position.y
    })
    expect(rows).toEqual([...rows].sort((a, b) => a - b))
  })

  it('admits an independent Study and a planned Strategy with no Baseline', () => {
    const map = graph()
    const planned = { ...map.nodes[0], id: 'strategy-planned-example', planning: 'planned', implementation: 'none', references: [] } as const
    const study = map.nodes.find(node => node.id === basisStudy)!
    const draft = { ...study, id: 'study-draft-example', evidence: 'pending', references: [] } as const
    map.nodes.push(planned, draft)
    validateResearchMap(map)
    expect(projectStrategy(map, planned.id)).toEqual({ nodes: [planned], edges: [] })
    expect(projectStrategy(map, strategy).nodes).not.toContain(draft)
    map.edges.push({ from: basis, to: draft.id, kind: 'attach' })
    validateResearchMap(map)
    expect(projectStrategy(map, strategy).nodes).toContain(draft)
  })

  it('reuses one canonical Study across multiple dimensions and strategies', () => {
    const map = graph()
    const secondary = 'strategy-secondary-example'
    const secondaryBaseline = 'baseline-secondary-example'
    const secondaryDimension = 'dimension-secondary-example'
    map.nodes.push(
      { ...map.nodes[0], id: secondary },
      { ...map.nodes[1], id: secondaryBaseline },
      { ...map.nodes[2], id: secondaryDimension },
    )
    map.edges.push(
      { from: index, to: basisStudy, kind: 'attach' },
      { from: secondary, to: secondaryBaseline, kind: 'branch' },
      { from: secondaryBaseline, to: secondaryDimension, kind: 'branch' },
      { from: secondaryDimension, to: basisStudy, kind: 'attach' },
    )
    validateResearchMap(map)
    const definition = map.nodes.find(node => node.id === basisStudy)
    const primaryTree = projectStrategy(map, strategy)
    expect(primaryTree.nodes.filter(node => node.id === basisStudy)).toEqual([definition])
    expect(primaryTree.nodes.find(node => node.id === basisStudy)).toBe(definition)
    expect(primaryTree.edges.filter(edge => edge.to === basisStudy)).toHaveLength(2)
    const secondaryTree = projectStrategy(map, secondary)
    expect(secondaryTree.nodes.map(node => node.id)).toEqual([basisStudy, secondary, secondaryBaseline, secondaryDimension])
    expect(secondaryTree.nodes[0]).toBe(definition)
    expect(secondaryTree.edges).toHaveLength(3)
  })

  it('rejects malformed fields, short IDs, wrong prefixes and duplicate IDs', () => {
    expect(() => validateResearchMap({ nodes: [{ id: 'ST001' }], edges: [] })).toThrow(/required property/)
    const map = graph()
    const study = map.nodes.find(node => node.id === basisStudy)!
    const analyses = study.analyses
    delete study.analyses
    expect(() => validateResearchMap(map)).toThrow(/required property 'analyses'/)
    study.analyses = analyses
    study.questions = []
    expect(() => validateResearchMap(map)).toThrow(/fewer than 1 items/)
    study.questions = ['测试问题']
    study.id = 'ST001'
    expect(() => validateResearchMap(map)).toThrow(/must match pattern/)
    study.id = 'baseline-test-study'
    expect(() => validateResearchMap(map)).toThrow(/must start with study-/)
    study.id = basisStudy
    map.nodes.push(map.nodes[0])
    expect(() => validateResearchMap(map)).toThrow(/duplicate node strategy-futures-long/)
  })

  it.each([
    [{ from: index, to: 'study-missing', kind: 'attach' }, /dangling edge/],
    [{ from: strategy, to: strategy, kind: 'branch' }, /self edge/],
    [{ from: strategy, to: baseline, kind: 'branch' }, /duplicate edge/],
    [{ from: index, to: baseline, kind: 'branch' }, /invalid branch direction/],
    [{ from: strategy, to: basisStudy, kind: 'attach' }, /invalid attach direction/],
    [{ from: basisStudy, to: strategy, kind: 'derived_from' }, /invalid derived_from direction/],
  ] satisfies [ResearchEdge, RegExp][])('rejects invalid edge %j', (edge, message) => {
    const map = graph()
    map.edges.push(edge)
    expect(() => validateResearchMap(map)).toThrow(message)
  })

  it('rejects orphaned dimensions and multiple branch parents', () => {
    const map = graph()
    const parent = { ...map.nodes[1], id: 'baseline-secondary-example' }
    map.nodes.push(parent)
    map.edges.push(
      { from: strategy, to: parent.id, kind: 'branch' },
      { from: parent.id, to: index, kind: 'branch' },
    )
    expect(() => validateResearchMap(map)).toThrow(/has multiple branch parents/)
    map.edges = map.edges.filter(edge => edge.to !== index)
    expect(() => validateResearchMap(map)).toThrow(/needs a branch parent/)
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

  it('rejects accepted evidence claims based on navigation or missing a review', () => {
    const map = graph()
    const study = map.nodes.find(node => node.id === basisStudy)!
    const references = study.references
    study.references = references.filter(reference => reference.kind === 'navigation')
    study.evidence = 'accepted'
    study.conclusion = proposedReview
    expect(() => validateResearchMap(map)).toThrow(/needs a concrete result or report/)
    study.references = references
    study.conclusion = { status: 'supported', summary: '无审阅' }
    expect(() => validateResearchMap(map)).toThrow(/needs a conclusion and review/)
  })

  it('requires an independent Finding to have its own review and an accepted source Study', () => {
    const map = graph()
    const finding = acceptedFinding()
    const study = map.nodes.find(node => node.id === basisStudy)!
    map.nodes.push(finding)
    expect(() => validateResearchMap(map)).toThrow(/needs an accepted source Study/)
    map.edges.push({ from: basisStudy, to: findingId, kind: 'derived_from' })
    expect(() => validateResearchMap(map)).toThrow(/needs accepted evidence from/)
    study.evidence = 'accepted'
    study.conclusion = { ...proposedReview, status: 'inconclusive' }
    expect(validateResearchMap(map)).toBe(map)
    expect(projectStrategy(map, strategy).nodes).toContain(finding)
    finding.evidence = 'available'
    expect(() => validateResearchMap(map)).toThrow(/must be accepted/)
    finding.evidence = 'accepted'
    finding.conclusion = { status: 'pending', summary: '未审阅' }
    expect(() => validateResearchMap(map)).toThrow(/needs a conclusion and review/)
  })
})
