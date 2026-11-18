import { useMemo, useState, type CSSProperties } from 'react'
import { Background, Controls, ReactFlow } from '@xyflow/react'
import { Flex, theme, Typography } from 'antd'
import '@xyflow/react/dist/style.css'
import definition from '../../../research-map/map.json'
import type { ResearchMap } from '../../../research-map/definition'
import { edgeStyles, graphEdges, layoutNodes } from './graph'
import { ResearchCard } from './ResearchCard'
import { Inspector, type MapNavigation } from './Inspector'
import './research-map.css'

// Both Vite configurations validate the document before the JSON module is produced.
const map = definition as ResearchMap
const nodeTypes = { research: ResearchCard }
const labels = { 'controls.ariaLabel': '地图视图', 'controls.zoomIn.ariaLabel': '放大', 'controls.zoomOut.ariaLabel': '缩小', 'controls.fitView.ariaLabel': '适应视图' }

export function StrategyResearchMap({ navigate, href }: MapNavigation) {
  const { token } = theme.useToken()
  const [selectedId, select] = useState(map.nodes[0].id)
  const byId = useMemo(() => new Map(map.nodes.map(node => [node.id, node])), [])
  const positioned = useMemo(() => layoutNodes(map), [])
  const selected = byId.get(selectedId) ?? map.nodes[0]
  const dependencies = map.edges.filter(edge => edge.kind === 'dependency' && (edge.from === selected.id || edge.to === selected.id))
  const nodes = positioned.map(node => ({
    ...node,
    selected: node.id === selected.id,
    domAttributes: { 'aria-pressed': node.id === selected.id },
    className: node.id !== selected.id && dependencies.some(edge => edge.from === node.id || edge.to === node.id) ? 'research-map__node--dependency' : undefined,
  }))
  const edges = graphEdges(map, selected.id)

  return <section aria-labelledby="strategy-research-map-title" className="research-map" style={{
    '--map-surface': token.colorBgContainer,
    '--map-border': token.colorBorderSecondary,
    '--map-selection': token.colorTextSecondary,
  } as CSSProperties}>
    <Typography.Title id="strategy-research-map-title" level={1}>策略研究地图</Typography.Title>
    <div className="research-map__workspace">
      <div className="research-map__graph">
        <Flex wrap gap="middle" className="research-map__legend" aria-label="关系图例">
          {Object.values(edgeStyles).map(({ label, color, dash }) =>
            <Flex key={label} gap="small" align="center">
              <span aria-hidden="true" style={{ borderTop: `2px ${dash === '2 5' ? 'dotted' : dash ? 'dashed' : 'solid'} ${color}`, width: 24 }} />
              <Typography.Text type="secondary">{label}</Typography.Text>
            </Flex>)}
        </Flex>
        <div className="research-map__canvas">
          <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} colorMode="dark"
            aria-label="策略研究关系图" ariaLabelConfig={labels}
            fitView fitViewOptions={{ padding: 0.14 }} minZoom={0.2}
            nodesDraggable={false} nodesConnectable={false} edgesReconnectable={false}
            deleteKeyCode={null} multiSelectionKeyCode={null} panActivationKeyCode={null}
            onNodeClick={(_, node) => select(node.id)}
            onNodesChange={changes => {
              const change = changes.find(change => change.type === 'select' && change.selected)
              if (change?.type === 'select') select(change.id)
            }}>
            <Background />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
      </div>
      <Inspector node={selected} nodes={byId} edges={map.edges} select={select} navigate={navigate} href={href} />
    </div>
  </section>
}
