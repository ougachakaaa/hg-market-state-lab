import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Typography } from 'antd'
import { evidenceLabels, kindNames, type FlowNode } from './graph'

export function ResearchCard({ data: { research }, selected }: NodeProps<FlowNode>) {
  const topic = research.topics?.[0]?.name ?? research.metrics[0]?.name ?? research.questions[0]
  return <div className={`research-map__card${selected ? ' research-map__card--selected' : ''}`}>
    <Handle type="target" position={Position.Left} isConnectable={false} />
    <Typography.Text type="secondary">{research.id} · {kindNames[research.kind]} · {evidenceLabels[research.evidence]}</Typography.Text>
    <Typography.Text strong className="research-map__node-title">{research.title}</Typography.Text>
    <Typography.Text className="research-map__node-purpose">{research.purpose}</Typography.Text>
    {topic && <Typography.Text type="secondary" ellipsis>{topic}</Typography.Text>}
    <Handle type="source" position={Position.Right} isConnectable={false} />
  </div>
}
