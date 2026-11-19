import { Button, Flex, Typography } from 'antd'
import type { MouseEvent } from 'react'
import type { ResearchEdge, ResearchNode, ResearchReference } from '../../../research-map/definition'
import type { WorkspaceDestination } from '../../app/routeInventory'
import { edgeStyles, evidenceLabels, implementationLabels, planningLabels } from './graph'

const conclusionLabels = { pending: '待研究或验收', supported: '支持假设', rejected: '否定假设', inconclusive: '无定论' }
const referenceLabels = { navigation: '页面', source: '来源', result: '结果', report: '报告' }
const repository = 'https://github.com/ougachakaaa/hg-market-state-lab/blob/develop/'

export type MapNavigation = {
  navigate: (path: WorkspaceDestination) => void
  href: (path: WorkspaceDestination) => string
}

function followWorkspace(event: MouseEvent<HTMLElement>, path: WorkspaceDestination, navigate: MapNavigation['navigate']) {
  if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  event.preventDefault()
  navigate(path)
}

export function Inspector({ node, nodes, related, findingSources, select, navigate, href }: MapNavigation & {
  node: ResearchNode
  nodes: Map<string, ResearchNode>
  related: ResearchEdge[]
  findingSources: { id: string; title: string; references: ResearchReference[] }[]
  select: (id: string) => void
}) {
  return <section aria-labelledby="research-map-inspector" className="research-map__inspector">
    <Flex vertical gap="middle">
      <div>
        <Typography.Title level={2} id="research-map-inspector">研究详情</Typography.Title>
        <Typography.Title level={3}>{node.title}</Typography.Title>
        <Typography.Text type="secondary" className="research-map__identifier">{node.id}</Typography.Text>
        <Typography.Paragraph>{node.purpose}</Typography.Paragraph>
        <Typography.Text type="secondary">{planningLabels[node.planning]} · {implementationLabels[node.implementation]} · {evidenceLabels[node.evidence]}</Typography.Text>
      </div>
      {node.questions.length > 0 && <div>
        <Typography.Title level={4}>研究问题</Typography.Title>
        <ul>{node.questions.map((question, index) => <li key={index}>{question}</li>)}</ul>
      </div>}
      {node.analyses?.length ? <div>
        <Typography.Title level={4}>统计分析计划</Typography.Title>
        <ul>{node.analyses.map(({ name, availability, note }, index) =>
          <li key={index}>{name} · {availability === 'available' ? '已有材料可参考' : '待研究'} · {note}</li>)}</ul>
      </div> : null}
      {node.parameters?.length ? <div>
        <Typography.Title level={4}>策略参数</Typography.Title>
        <dl>{node.parameters.map(({ name, note }, index) => <div key={index}><dt>{name}</dt><dd>{note}</dd></div>)}</dl>
      </div> : null}
      {related.length > 0 && <div>
        <Typography.Title level={4}>研究关系</Typography.Title>
        <ul>{related.map(({ from, to, kind, label }) => {
          const outgoing = from === node.id
          const other = nodes.get(outgoing ? to : from)!
          return <li key={`${from}:${to}:${kind}`}>
            {outgoing ? '指向' : '来自'} · {edgeStyles[kind].label} ·{' '}
            <Button type="link" size="small" onClick={() => select(other.id)}>{other.title}</Button>
            {label && <Typography.Text type="secondary">{label}</Typography.Text>}
          </li>
        })}</ul>
      </div>}
      {node.references.length > 0 && <div>
        <Typography.Title level={4}>来源与证据</Typography.Title>
        <ReferenceList references={node.references} navigate={navigate} href={href} />
      </div>}
      {findingSources.length > 0 && <div>
        <Typography.Title level={4}>来源 Study 的证据</Typography.Title>
        {findingSources.map(study => <div key={study.id}>
          <Typography.Text strong>{study.title}</Typography.Text>
          <ReferenceList references={study.references} navigate={navigate} href={href} />
        </div>)}
      </div>}
      <div>
        <Typography.Title level={4}>研究结论</Typography.Title>
        <Typography.Text strong>{conclusionLabels[node.conclusion.status]}</Typography.Text>
        <Typography.Paragraph>{node.conclusion.summary}</Typography.Paragraph>
        {node.conclusion.review && <Typography.Paragraph>{node.conclusion.review}</Typography.Paragraph>}
      </div>
    </Flex>
  </section>
}

function ReferenceList({ references, navigate, href }: MapNavigation & { references: ResearchReference[] }) {
  return <ul>{references.map((reference, index) => <li key={index}>
    {referenceLabels[reference.kind]} · {reference.target === 'workspace'
      ? <Typography.Link href={href(reference.value)} onClick={event => followWorkspace(event, reference.value, navigate)}>{reference.label}</Typography.Link>
      : <Typography.Link href={repository + reference.value} target="_blank" rel="noreferrer">{reference.label}</Typography.Link>}
  </li>)}</ul>
}
