import { useCallback, useMemo, useRef, useState, type CSSProperties } from 'react'
import { Background, BaseEdge, Controls, getNodesBounds, getViewportForBounds, ReactFlow, type EdgeProps, type OnInit } from '@xyflow/react'
import { Flex, theme, Typography } from 'antd'
import '@xyflow/react/dist/style.css'
import { isEvidenceReference, type ResearchMap } from '../../../research-map/definition'
import { edgeStyles, graphEdges, layoutNodes, projectStrategy, type FlowNode, type FlowEdge } from './graph'
import { layoutTree } from './treeLayout'
import { ResearchCard } from './ResearchCard'
import { Inspector, type MapNavigation } from './Inspector'
import './research-map.css'

const nodeTypes = { research: ResearchCard }
const labels = { 'controls.ariaLabel': '地图视图', 'controls.zoomIn.ariaLabel': '放大', 'controls.zoomOut.ariaLabel': '缩小', 'controls.fitView.ariaLabel': '适应视图' }
function RelationshipEdge({ id, data, markerEnd, style }: EdgeProps<FlowEdge>) {
  return <BaseEdge id={id} path={data!.path} markerEnd={markerEnd} style={style} />
}

const edgeTypes = { relationship: RelationshipEdge }
const fitOptions = { padding: '16px' } as const

export function StrategyResearchMap({ map, strategyId, navigate, href }: MapNavigation & { map: ResearchMap; strategyId: string }) {
  const { token } = theme.useToken()
  const [selectedId, select] = useState(strategyId)
  const canvas = useRef<HTMLDivElement>(null)
  const tree = useMemo(() => projectStrategy(map, strategyId), [map, strategyId])
  const byId = useMemo(() => new Map(tree.nodes.map(node => [node.id, node])), [tree])
  const layout = useMemo(() => layoutTree(tree, strategyId), [tree, strategyId])
  const positioned = useMemo(() => layoutNodes(tree, layout), [tree, layout])
  const canonicalNodes = useMemo(() => new Map(map.nodes.map(node => [node.id, node])), [map])
  const selected = byId.get(selectedId) ?? byId.get(strategyId)!
  const related = tree.edges.filter(edge => edge.from === selected.id || edge.to === selected.id)
  const findingsSources = selected.kind === 'finding' ? map.edges
    .filter(edge => edge.kind === 'derived_from' && edge.to === selected.id)
    .map(edge => {
      const study = canonicalNodes.get(edge.from)!
      return { id: study.id, title: study.title, references: study.references.filter(isEvidenceReference) }
    }) : []
  const nodes = positioned.map(node => ({
    ...node,
    selected: node.id === selected.id,
    domAttributes: { 'aria-pressed': node.id === selected.id },
    className: node.id !== selected.id && related.some(edge => edge.from === node.id || edge.to === node.id) ? 'research-map__node--related' : undefined,
  }))
  const edges = graphEdges(tree, layout, selected.id)

  const frameTree = useCallback<OnInit<FlowNode>>(flow => {
    const { clientWidth: width, clientHeight: height } = canvas.current!
    const fit = getViewportForBounds(getNodesBounds(positioned), width, height, 0.2, 1, fitOptions.padding)
    if (fit.zoom >= 0.8) {
      void flow.setViewport(fit)
      return
    }
    const root = positioned.find(node => node.id === strategyId)!
    const zoom = 0.8
    void flow.setViewport({
      x: width / 2 - (root.position.x + root.width! / 2) * zoom,
      y: 24 - root.position.y * zoom,
      zoom,
    })
  }, [positioned, strategyId])

  return <section aria-labelledby="strategy-research-map-title" className="research-map" style={{
    '--map-surface': token.colorBgContainer,
    '--map-card': token.colorBgElevated,
    '--map-border': token.colorBorderSecondary,
    '--map-selection': token.colorText,
  } as CSSProperties}>
    <div className="research-map__header">
      <Typography.Title id="strategy-research-map-title" level={1}>策略研究地图</Typography.Title>
    </div>
    <div className="research-map__workspace">
      <div className="research-map__graph">
        <Flex wrap gap="middle" className="research-map__legend" aria-label="关系图例">
          {Object.values(edgeStyles).map(({ label, color }) =>
            <Flex key={label} gap="small" align="center">
              <span aria-hidden="true" style={{ borderTop: `2px solid ${color}`, width: 24 }} />
              <Typography.Text type="secondary">{label}</Typography.Text>
            </Flex>)}
          {layout.primary.size < tree.edges.length && <Flex gap="small" align="center">
            <span aria-hidden="true" style={{ borderTop: `2px dashed ${token.colorTextSecondary}`, width: 24 }} />
            <Typography.Text type="secondary">次级关联</Typography.Text>
          </Flex>}
        </Flex>
        <div className="research-map__canvas" ref={canvas}>
          <ReactFlow<FlowNode, FlowEdge> nodes={nodes} edges={edges} nodeTypes={nodeTypes} edgeTypes={edgeTypes} colorMode="dark"
            aria-label="策略研究关系图" ariaLabelConfig={labels}
            onInit={frameTree} fitViewOptions={fitOptions} minZoom={0.2}
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
      <Inspector key={selected.id} node={selected} nodes={byId} related={related}
        findingSources={findingsSources} select={select} navigate={navigate} href={href} />
    </div>
  </section>
}
