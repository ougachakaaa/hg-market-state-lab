import { Alert, Descriptions, Flex, Typography } from 'antd'
import { localCases } from '../model/localCases'
import { STATIC_LOCAL_CASE_NOTE, type ResearchOverviewMode } from '../model/catalogPresentation'

export function LocalCaseDetails({ item, mode }: {
  item: (typeof localCases)[number]
  mode: ResearchOverviewMode
}) {
  return <Flex vertical gap="middle">
    <Descriptions size="small" column={{ xs: 1, lg: 2 }} items={[
      { key: 'id', label: '研究 ID', children: item.id },
      { key: 'purpose', label: '用途', children: item.purpose },
      { key: 'readiness', label: '实现与可用性', children: item.readiness },
      { key: 'planned', label: '在线应用', children: item.planned ?? '未发布在线应用。' },
      { key: 'scope', label: '支持范围与输入', children: item.scope },
      { key: 'output', label: '分析结果', children: item.output },
      { key: 'access', label: '访问路径', children: item.access },
    ]} />
    {mode === 'static' && <Typography.Paragraph type="secondary" role="note" style={{ marginBottom: 0 }}>{STATIC_LOCAL_CASE_NOTE}</Typography.Paragraph>}
    <Alert type="info" title="可用性说明" description={item.note} showIcon />
  </Flex>
}
