import { Collapse, Flex, Typography } from 'antd'
import { RelativeValuePresentation, validateResult, type Query } from '../../../src/features/calendar_spread_relative_value/presentation'
import { disclose, type Bundle } from '../dataAdapter'
import { AsyncContent } from '../AsyncContent'
import type { StaticPageProps } from './types'
const adapt = (b: Bundle) => validateResult(b.result, b.request as Query)
export default function CalendarSpread({ store }: StaticPageProps) {
  return <AsyncContent resource={store.get('calendar_spread_relative_value', adapt)}>{({ data, identity }) => <Flex vertical gap="middle">
    <Typography.Title level={2}>Calendar Spread Historical Relative Value</Typography.Title>
    <Typography.Text type="secondary">静态快照不会获取实时行情；描述性研究不构成收益预测，历史元数据不保证在当时已知。</Typography.Text>
    <RelativeValuePresentation result={data} />
    <Collapse items={[{ key: 'source', label: '静态快照来源', children: <Typography.Paragraph style={{ overflowWrap: 'anywhere' }}>{disclose(identity)}</Typography.Paragraph> }]} />
  </Flex>}</AsyncContent>
}
