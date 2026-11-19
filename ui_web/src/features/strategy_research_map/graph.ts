import type { Edge, Node } from '@xyflow/react'
import { edgeId, type EdgeKind, type NodeKind, type ResearchMap, type ResearchNode } from '../../../research-map/definition'

import { cardWidth, cardHeight, type layoutTree } from './treeLayout'

export const kindNames: Record<NodeKind, string> = {
  strategy: '策略', baseline: '基准回测', dimension: '研究维度', study: '专题研究', finding: '研究发现',
}

export const edgeStyles: Record<EdgeKind, { label: string; color: string }> = {
  branch: { label: '策略分支', color: '#a7b3c0' },
  attach: { label: '关联研究', color: '#b8a3dc' },
  derived_from: { label: '证据来源', color: '#8abfa3' },
}

export const planningLabels = { planned: '待开展', defined: '方向已定义', 'in-progress': '研究中' }
export const implementationLabels = { none: '待实施', partial: '部分能力可用', available: '已有实现' }
export const evidenceLabels = { pending: '待研究或验收', available: '已有证据材料', accepted: '已验收' }

export type FlowNode = Node<{ research: ResearchNode }, 'research'>
export type FlowEdge = Edge<{ path: string }, 'relationship'>

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

export function layoutNodes(map: ResearchMap, tree: ReturnType<typeof layoutTree>): FlowNode[] {
  return map.nodes.map(research => ({
    id: research.id, type: 'research', width: cardWidth, height: cardHeight, data: { research },
    ariaRole: 'button',
    ariaLabel: `${kindNames[research.kind]} ${research.title}`,
    position: tree.positions.get(research.id)!,
  }))
}

export function graphEdges(map: ResearchMap, tree: ReturnType<typeof layoutTree>, selected: string): FlowEdge[] {
  return map.edges.map(edge => {
    const { from, to, kind } = edge
    const { color, label } = edgeStyles[kind]
    const id = edgeId(edge)
    const primary = tree.primary.has(id)
    const path = tree.connector(edge).map(({ x, y }, index) => `${index ? 'L' : 'M'} ${x} ${y}`).join(' ')
    const active = from === selected || to === selected
    return {
      id, type: 'relationship', data: { path }, source: from, target: to, ariaLabel: `${from} → ${to} · ${label}`,
      markerEnd: { type: 'arrowclosed', color },
      style: { stroke: color, strokeDasharray: primary ? undefined : '5 5', strokeWidth: active ? 2.5 : primary ? 1.75 : 1.25, opacity: active ? 1 : primary ? 0.85 : 0.5 },
      className: active ? 'research-map__edge--active' : undefined,
      selectable: false, focusable: false, zIndex: active ? 1 : 0,
    }
  })
}
