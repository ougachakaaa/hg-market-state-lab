import { edgeId, type ResearchEdge, type ResearchMap } from '../../../research-map/definition'

export const cardWidth = 124
export const cardHeight = 82
const siblingGap = 18
const layerGap = 53
const secondaryLaneGap = 12

type Point = { x: number; y: number }
type Branch = { id: string; children: Branch[]; width: number }

export function layoutTree(map: ResearchMap, strategyId: string) {
  const primary = new Set<string>()
  const assigned = new Set<string>()
  const children = new Map<string, string[]>()
  for (const edge of map.edges) {
    if (assigned.has(edge.to)) continue
    primary.add(edgeId(edge))
    assigned.add(edge.to)
    const siblings = children.get(edge.from) ?? []
    siblings.push(edge.to)
    children.set(edge.from, siblings)
  }

  function measure(id: string): Branch {
    const branches = (children.get(id) ?? []).map(measure)
    const width = branches.reduce((sum, child) => sum + child.width, 0) + (branches.length - 1) * siblingGap
    return { id, children: branches, width: Math.max(cardWidth, width) }
  }

  const root = measure(strategyId)
  const depths = new Map<string, number>()
  const positions = new Map<string, Point>()
  function place(branch: Branch, left: number, depth: number) {
    depths.set(branch.id, depth)
    positions.set(branch.id, { x: left + (branch.width - cardWidth) / 2, y: 0 })
    for (const child of branch.children) {
      place(child, left, depth + 1)
      left += child.width + siblingGap
    }
  }
  place(root, 0, 0)

  // The validated edge kinds always connect consecutive depths. Allocate extra
  // space for cross-branch connectors inside the affected gap only.
  const secondaryCounts: number[] = []
  const lanes = new Map<string, number>()
  for (const edge of map.edges) {
    const id = edgeId(edge)
    if (!primary.has(id)) {
      const depth = depths.get(edge.from)!
      const lane = secondaryCounts[depth] ?? 0
      lanes.set(id, lane)
      secondaryCounts[depth] = lane + 1
    }
  }

  const layerTop = [0]
  for (let depth = 0; depth < Math.max(...depths.values()); depth++) {
    layerTop.push(layerTop[depth] + cardHeight + layerGap + (secondaryCounts[depth] ?? 0) * secondaryLaneGap)
  }
  for (const [id, point] of positions) point.y = layerTop[depths.get(id)!]

  function connector(edge: ResearchEdge): Point[] {
    const source = positions.get(edge.from)!
    const target = positions.get(edge.to)!
    const from = { x: source.x + cardWidth / 2, y: source.y + cardHeight }
    const to = { x: target.x + cardWidth / 2, y: target.y }
    const lane = lanes.get(edgeId(edge))
    const y = from.y + layerGap / 2 + (lane === undefined ? 0 : (lane + 1) * secondaryLaneGap)
    return [from, { x: from.x, y }, { x: to.x, y }, to]
  }

  return { positions, primary, connector }
}
