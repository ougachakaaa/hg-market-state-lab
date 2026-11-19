import { graphlib, layout } from '@dagrejs/dagre'
import type { Edge, Node } from '@xyflow/react'
import { edgeId, type EdgeKind, type NodeKind, type ResearchMap, type ResearchNode } from '../../../research-map/definition'

export const kindNames: Record<NodeKind, string> = {
  strategy: '策略', baseline: '基准回测', dimension: '研究维度', study: '专题研究', finding: '研究发现',
}

export const edgeStyles: Record<EdgeKind, { label: string; color: string; dash?: string }> = {
  branch: { label: '策略分支', color: '#a7b3c0' },
  attach: { label: '关联研究', color: '#b8a3dc', dash: '7 5' },
  derived_from: { label: '证据来源', color: '#8abfa3', dash: '2 5' },
}

export const planningLabels = { planned: '待开展', defined: '方向已定义', 'in-progress': '研究中' }
export const implementationLabels = { none: '待实施', partial: '部分能力可用', available: '已有实现' }
export const evidenceLabels = { pending: '待研究或验收', available: '已有证据材料', accepted: '已验收' }

const width = 164
const height = 76
const gap = 22
const rankHeight = height + 53
const ranks: Record<NodeKind, number> = { strategy: 0, baseline: 1, dimension: 2, study: 3, finding: 4 }
export type FlowNode = Node<{ research: ResearchNode }, 'research'>

export function projectStrategy(map: ResearchMap, strategyId: string): ResearchMap {
  const outgoing = new Map<string, ResearchMap['edges']>()
  for (const edge of map.edges) {
    const edges = outgoing.get(edge.from)
    if (edges) edges.push(edge)
    else outgoing.set(edge.from, [edge])
  }

  const visible = new Set([strategyId])
  for (const id of visible) {
    for (const edge of outgoing.get(id) ?? []) visible.add(edge.to)
  }
  return {
    nodes: map.nodes.filter(node => visible.has(node.id)),
    edges: map.edges.filter(edge => visible.has(edge.from) && visible.has(edge.to)),
  }
}

export function layoutNodes(map: ResearchMap): FlowNode[] {
  const graph = new graphlib.Graph().setGraph({ rankdir: 'TB', nodesep: gap })
  for (const node of map.nodes) graph.setNode(node.id, { width, height })
  for (const { from, to } of map.edges) graph.setEdge(from, to, {})
  layout(graph)

  // Keep Dagre's crossing-aware order and compact each semantic rank. Holding a
  // slot for every descendant makes a row of several short branches too wide.
  const rows = Object.keys(ranks).map(kind => map.nodes.filter(node => node.kind === kind))
  const centers = map.nodes.map(node => graph.node(node.id).x as number)
  const left = Math.min(...centers) - width / 2
  const layoutWidth = Math.max(...centers) + width / 2 - left
  const graphWidth = Math.max(...rows.map(row => row.length)) * (width + gap) - gap
  const positions = new Map<string, { x: number; y: number }>()
  for (const [rank, row] of rows.entries()) {
    if (!row.length) continue
    row.sort((a, b) => graph.node(a.id).x - graph.node(b.id).x)
    const rowWidth = row.length * (width + gap) - gap
    const center = (graph.node(row[0].id).x + graph.node(row[row.length - 1].id).x) / 2
    const preferredOffset = (center - left) * graphWidth / layoutWidth - rowWidth / 2
    const offset = rank <= ranks.baseline && row.length === 1
      ? (graphWidth - rowWidth) / 2
      : Math.max(0, Math.min(preferredOffset, graphWidth - rowWidth))
    row.forEach((node, index) => positions.set(node.id, { x: offset + index * (width + gap), y: rank * rankHeight }))
  }

  return map.nodes.map(research => {
    return {
      id: research.id, type: 'research', width, height, data: { research },
      ariaRole: 'button',
      ariaLabel: `${kindNames[research.kind]} ${research.title}`,
      position: positions.get(research.id)!,
    }
  })
}

export function graphEdges(map: ResearchMap, selected: string): Edge[] {
  return map.edges.map(edge => {
    const { from, to, kind } = edge
    const { color, dash, label } = edgeStyles[kind]
    const active = from === selected || to === selected
    return {
      id: edgeId(edge), source: from, target: to, ariaLabel: `${from} → ${to} · ${label}`,
      markerEnd: { type: 'arrowclosed', color },
      style: { stroke: color, strokeDasharray: dash, strokeWidth: active ? 2.5 : 1.5, opacity: active ? 1 : 0.75 },
      className: active ? 'research-map__edge--active' : undefined,
      selectable: false, focusable: false, zIndex: active ? 1 : 0,
    }
  })
}
