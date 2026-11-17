import { Flex, Typography } from 'antd'
import { DailyPresentation, validateResult, type Query } from '../../../src/features/futures_calendar_spread/presentation'
import { disclose, type Bundle } from '../dataAdapter'
import { AsyncContent } from '../AsyncContent'
import type { StaticPageProps } from './types'
const adapt = (b: Bundle) => validateResult(b.result, b.request as Query)
export default function DailySpread({ store }: StaticPageProps) {
  return <AsyncContent resource={store.get('calendar_spread_daily', adapt)}>{({ data, identity }) => <Flex vertical gap="middle">
    <Typography.Title level={2}>Futures Calendar Spread</Typography.Title>
    <Typography.Paragraph>{disclose(identity)} 静态快照不会获取实时行情；历史元数据不保证在当时已知。</Typography.Paragraph>
    <DailyPresentation result={data} />
  </Flex>}</AsyncContent>
}
