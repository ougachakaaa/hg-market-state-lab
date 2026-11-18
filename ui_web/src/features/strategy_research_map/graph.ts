import { graphlib, layout } from '@dagrejs/dagre'
import type { Edge, Node } from '@xyflow/react'
import { edgeId, type EdgeKind, type NodeKind, type ResearchMap, type ResearchNode } from '../../../research-map/definition'

export const kindNames: Record<NodeKind, string> = {
  strategy: '策略', 'strategy-definition': '策略定义', baseline: '基准', evaluation: '评价',
  attribution: '归因', study: '研究', hypothesis: '假设', optimization: '优化', validation: '验证',
}

export const edgeStyles: Record<EdgeKind, { label: string; color: string; dash?: string }> = {
  dependency: { label: '前置依赖', color: '#a7b3c0' },
  motivates: { label: '研究动机', color: '#90bde5', dash: '7 5' },
  feedback: { label: '验证反馈', color: '#d5a876', dash: '2 5' },
}

export const planningLabels = { planned: '待规划', defined: '方向已定义', 'in-progress': '研究中' }
export const implementationLabels = { none: '待实施', partial: '部分能力可用', available: '已有实现' }
export const evidenceLabels = { pending: '待验收', available: '已有证据材料', accepted: '已验收' }

const width = 216
const height = 148
export type FlowNode = Node<{ research: ResearchNode }, 'research'>

export function layoutNodes(map: ResearchMap): FlowNode[] {
  const graph = new graphlib.Graph().setGraph({ rankdir: 'LR', ranksep: 48, nodesep: 34 })
  for (const node of map.nodes) graph.setNode(node.id, { width, height })
  for (const edge of map.edges) {
    if (edge.kind === 'dependency') graph.setEdge(edge.from, edge.to, {})
  }
  layout(graph)
  return map.nodes.map(research => {
    const { x, y } = graph.node(research.id)
    return {
      id: research.id, type: 'research', width, height, data: { research },
      ariaRole: 'button',
      ariaLabel: `${research.id} ${research.title}`,
      position: { x: x - width / 2, y: y - height / 2 },
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
      style: { stroke: color, strokeDasharray: dash, strokeWidth: active ? 2.5 : 1.5, opacity: active ? 1 : 0.62 },
      className: active ? 'research-map__edge--active' : undefined,
      selectable: false, focusable: false, zIndex: active ? 1 : 0,
    }
  })
}
