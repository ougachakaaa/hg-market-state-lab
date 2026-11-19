// @vitest-environment node
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { projectStrategy } from '../src/features/strategy_research_map/graph'
import { cardHeight, cardWidth, layoutTree } from '../src/features/strategy_research_map/treeLayout'
import { edgeId } from './definition'
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
    verifyGeometry(map)
    const tree = layoutTree(map, strategy)
    const center = (id: string) => tree.positions.get(id)!.x + cardWidth / 2
    expect(center(index)).toBe((center('study-index-return-distribution') + center('study-market-regime')) / 2)
    expect(center(basis)).toBe((center(basisStudy) + center('study-basis-realization')) / 2)
  })

  it('admits an independent Study and a planned Strategy with no Baseline', () => {
    const map = graph()
    const planned = { ...map.nodes[0], id: 'strategy-planned-example', planning: 'planned', implementation: 'none', references: [] } as const
    const study = map.nodes.find(node => node.id === basisStudy)!
    const draft = { ...study, id: 'study-draft-example', evidence: 'pending', references: [] } as const
    map.nodes.push(planned, draft)
    validateResearchMap(map)
    const projection = projectStrategy(map, planned.id)
    expect(projection).toEqual({ nodes: [planned], edges: [] })
    expect([...layoutTree(projection, planned.id).positions]).toEqual([[planned.id, { x: 0, y: 0 }]])
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

function verifyGeometry(map: ResearchMap) {
  const tree = layoutTree(map, strategy)
  const cards = [...tree.positions]
  expect(cards).toHaveLength(map.nodes.length)
  for (const [position, [id, card]] of cards.entries()) {
    for (const [other, neighbor] of cards.slice(position + 1)) {
      const overlaps = Math.abs(card.x - neighbor.x) < cardWidth && Math.abs(card.y - neighbor.y) < cardHeight
      expect(overlaps, `${id} overlaps ${other}`).toBe(false)
    }
  }
  for (const edge of map.edges) {
    const points = tree.connector(edge)
    expect(tree.positions.get(edge.to)!.y).toBeGreaterThan(tree.positions.get(edge.from)!.y + cardHeight)
    for (const [id, card] of cards) {
      if (id === edge.from || id === edge.to) continue
      for (let i = 1; i < points.length; i++) {
        const [a, b] = [points[i - 1], points[i]]
        const intersects = Math.max(a.x, b.x) > card.x && Math.min(a.x, b.x) < card.x + cardWidth
          && Math.max(a.y, b.y) > card.y && Math.min(a.y, b.y) < card.y + cardHeight
        expect(intersects, `${edgeId(edge)} intersects ${id}`).toBe(false)
      }
    }
  }
  return tree
}

it('allocates unequal child subtrees in stable order when adding ordinary Studies', () => {
  const map = graph()
  const dimensions = map.nodes.filter(node => node.kind === 'dimension')
  const order = (tree: ReturnType<typeof layoutTree>) => [...dimensions]
    .sort((a, b) => tree.positions.get(a.id)!.x - tree.positions.get(b.id)!.x).map(node => node.id)
  const before = verifyGeometry(map)
  const sample = map.nodes.find(node => node.id === basisStudy)!
  for (const [i, parent] of [index, basis].entries()) {
    const study = { ...sample, id: `study-extra-${i}`, evidence: 'pending', references: [] } as const
    map.nodes.push({ ...study, references: [] })
    map.edges.push({ from: parent, to: study.id, kind: 'attach' })
  }
  const extended = verifyGeometry(validateResearchMap(map))
  expect(order(extended)).toEqual(order(before))

  for (const [i, parent] of dimensions.entries()) {
    for (let j = 0; j < i; j++) {
      const study: ResearchNode = { ...sample, id: `study-synthetic-${i}-${j}`, evidence: 'pending', references: [] }
      map.nodes.push(study)
      map.edges.push({ from: parent.id, to: study.id, kind: 'attach' })
    }
  }
  const expanded = verifyGeometry(validateResearchMap(map))
  const ranges = dimensions.map(parent => {
    const childIds = map.edges.filter(edge => edge.from === parent.id).map(edge => edge.to)
    const xs = [parent.id, ...childIds].map(id => expanded.positions.get(id)!.x)
    return [Math.min(...xs), Math.max(...xs) + cardWidth]
  })
  ranges.slice(1).forEach(([left], i) => expect(left).toBeGreaterThan(ranges[i][1]))
})

it('uses the first projected parent for shared Studies and Findings and retains collision-free cross-branch edges', () => {
  const map = graph()
  const source = map.nodes.find(node => node.id === basisStudy)!
  const other = map.nodes.find(node => node.id === 'study-market-regime')!
  for (const study of [source, other]) {
    study.evidence = 'accepted'
    study.conclusion = proposedReview
    study.references = source.references
  }
  const finding = acceptedFinding()
  map.nodes.push(finding)
  const related: ResearchEdge[] = [
    { kind: 'attach', from: index, to: source.id },
    { kind: 'derived_from', from: source.id, to: finding.id },
    { kind: 'derived_from', from: other.id, to: finding.id },
  ]
  map.edges.push(...related)
  const projected = projectStrategy(validateResearchMap(map), strategy)
  const layout = verifyGeometry(projected)
  expect(projected.nodes.filter(node => node.id === source.id)).toHaveLength(1)
  expect(layout.primary.has(edgeId({ kind: 'attach', from: basis, to: source.id }))).toBe(true)
  expect(related.map(edge => layout.primary.has(edgeId(edge)))).toEqual([false, true, false])
  expect(layout.positions.get(finding.id)!.x).toBe(layout.positions.get(source.id)!.x)
  expect(layout.positions.get(finding.id)!.y).toBeGreaterThan(layout.positions.get(source.id)!.y)
})
