import type { ExpiryGroup, OptionChain, OptionPoint } from '../api/moOptionChain'
import { ChainRequestError } from '../api/moOptionChain'
import type { ExpiryColors } from '../charts/expiryPalette'
import { missingPriceCount } from '../model/combinedChartData'
import { formatPrice } from '../model/priceDisplay'
import { ExpirySwatches } from './OptionChainControls'

const errorTitles: Partial<Record<ChainRequestError['kind'], string>> = {
  invalid_request: '请求日期或参数无效',
  unsupported_query: '当前不支持此查询',
  date_not_available: '该日期无可用数据',
  option_chain_unavailable: '当前无法生成完整期权链',
  service_not_wired: '数据服务尚未接线',
}

export function OptionChainError({ date, error }: { date: string; error: ChainRequestError }) {
  const title = error.kind === 'network' ? '无法连接数据服务'
    : error.kind === 'invalid_response' ? '数据服务响应异常'
      : errorTitles[error.kind] ?? '数据服务访问失败'
  return (
    <Alert type="error" showIcon role="alert" title={title}
      description={<Space orientation="vertical" size={0}>
        <span>观察日期：{date} · close</span>
        <span>请检查日期或数据服务；恢复后可清空日期并重新选择。</span>
        {error.kind !== 'network' && error.kind !== 'invalid_response' && <span>{error.message}</span>}
      </Space>} />
  )
}

export function OptionChainSummary({ chain }: { chain: OptionChain }) {
  return (
    <Card size="small" title={`${chain.target_trade_date} · ${chain.option_product}`}>
      <Descriptions size="small" column={{ xs: 1, sm: 2, lg: 4 }} items={[
        { key: 'price-type', label: '价格口径', children: chain.price_type },
        { key: 'underlying', label: '标的指数', children: chain.underlying.instrument_id },
        { key: 'reference', label: '参考价', children: formatPrice(chain.underlying.price) },
        { key: 'expiries', label: '到期日数量', children: chain.expiries.length },
      ]} />
    </Card>
  )
}

function OptionTable({ title, points }: { title: string; points: OptionPoint[] }) {
  const columns: TableColumnsType<OptionPoint> = [
    { title: '合约标识', dataIndex: 'instrument_id' },
    { title: '行权价', dataIndex: 'strike', render: formatPrice },
    { title: '价格', dataIndex: 'price', render: formatPrice },
  ]
  return (
    <section style={{ flex: '1 1 24rem', minWidth: 0 }}>
      <Typography.Title level={5}>{title}</Typography.Title>
      <Table size="small" columns={columns} dataSource={points} rowKey="instrument_id"
        pagination={false} scroll={{ x: 'max-content' }} />
    </section>
  )
}

function ExpirySummary({ group, colors }: { group: ExpiryGroup; colors: ExpiryColors }) {
  const missing = missingPriceCount(group)
  const allMissing = group.calls.every((point) => point.price === null)
    && group.puts.every((point) => point.price === null)
  return (
    <Card size="small" role="region" aria-label={`${group.expiry_date} 到期日`}
      title={<Space><ExpirySwatches colors={colors} hasFutures={group.futures !== null} />
        <Typography.Title level={3} style={{ margin: 0 }}>{group.expiry_date}</Typography.Title>
      </Space>}
      extra={<Typography.Text type="secondary">Call {group.calls.length} · Put {group.puts.length}</Typography.Text>}>
      <Space orientation="vertical" style={{ display: 'flex' }}>
        <Typography.Text type="secondary">{group.futures === null
          ? '无同到期 IM 合约'
          : `Futures：${group.futures.instrument_id} · ${formatPrice(group.futures.price)}`}</Typography.Text>
        {missing > 0 && <Alert type="warning" showIcon
          title={`${missing} 个合约缺少所选价格，未绘制为散点；可在合约明细中查看。`} />}
        {allMissing && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="该到期日没有可绘制的价格。" />}
        <Collapse size="small" items={[{
          key: 'contracts', label: '合约明细',
          children: <Flex gap="middle" wrap><OptionTable title="Calls" points={group.calls} /><OptionTable title="Puts" points={group.puts} /></Flex>,
        }]} />
      </Space>
    </Card>
  )
}

export function ExpiryDetails({ groups, palette }: {
  groups: ExpiryGroup[]
  palette: Record<string, ExpiryColors>
}) {
  return (
    <Space orientation="vertical" size="middle" style={{ display: 'flex' }}>
      <Typography.Title level={3}>所选到期日明细</Typography.Title>
      {groups.map((group) => <ExpirySummary key={group.expiry_date} group={group} colors={palette[group.expiry_date]} />)}
    </Space>
  )
}
import { Alert, Card, Collapse, Descriptions, Empty, Flex, Space, Table, Typography } from 'antd'
import type { TableColumnsType } from 'antd'
