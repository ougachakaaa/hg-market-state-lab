import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Typography } from 'antd'
import { kindNames, type FlowNode } from './graph'

export function ResearchCard({ data: { research }, selected }: NodeProps<FlowNode>) {
  return <div className={`research-map__card${selected ? ' research-map__card--selected' : ''}`} data-kind={research.kind}>
    {research.kind !== 'strategy' && <Handle type="target" position={Position.Top} isConnectable={false} />}
    <Typography.Text className="research-map__node-kind">{kindNames[research.kind]}</Typography.Text>
    <Typography.Text strong className="research-map__node-title">{research.title}</Typography.Text>
    {research.kind !== 'finding' && <Handle type="source" position={Position.Bottom} isConnectable={false} />}
  </div>
}
