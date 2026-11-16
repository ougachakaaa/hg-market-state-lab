import { Alert, Card, Collapse, Descriptions, Flex, Table, Typography } from 'antd'
import type { Result } from '../api/validateResult'
import { metricLabels, number, count } from '../model/format'

export function DailyPresentation({ result }: { result: Result }) {
  const labels = { valid: '有效', not_applicable: '不适用', excluded: '已排除' }
  return <Flex vertical gap="middle">
    <Card title="已查询数据">
      <Descriptions items={[{ key: 'product', label: 'Product', children: result.request.product_code }, { key: 'date', label: 'Trade Date', children: result.request.trade_date }]} />
      {result.day.status === 'closed' ? <Alert type="info" title="休市日（non_trading_day）" description="该日无跨期观察，不回退到其他交易日。" /> : <Table rowKey={o => `${o.near_slot}/${o.far_slot}`} pagination={false} scroll={{ x: 1700 }} dataSource={result.day.observations} columns={[
        { title: 'Pair', render: (_, o) => `${o.near_slot}/${o.far_slot}`, fixed: 'left' },
        ...(['near', 'far'] as const).flatMap(side => [
          { title: `${side === 'near' ? 'Near' : 'Far'} Real Contract`, render: (_, o: Result['day']['observations'][number]) => o[side]?.contract_code ?? '未提供' },
          { title: `${side === 'near' ? 'Near' : 'Far'} Close`, render: (_, o: Result['day']['observations'][number]) => number(o[side]?.close) },
          { title: `${side === 'near' ? 'Near' : 'Far'} Last Trading Date`, render: (_, o: Result['day']['observations'][number]) => o[side]?.delist_date ?? '未提供' },
        ]),
        ...(['signed_spread', 'annualized_point_spread', 'annualized_spread_ratio'] as const).map(metric => ({ title: metricLabels[metric], render: (_, o: Result['day']['observations'][number]) => number(o.metrics?.[metric].value, metric === 'annualized_spread_ratio') })),
        { title: 'Delta Days', render: (_, o) => count(o.delta_days) },
        { title: 'Near DTE / Expiry Stage', render: (_, o) => `${count(o.near_dte_days)} / ${o.expiry_stage ?? '未提供'}` },
        { title: 'Outcome / Reason', render: (_, o) => `${labels[o.outcome]} / ${o.reason ?? '—'}` },
      ]} />}
      {result.day.observations.some(o => o.reason === 'no_active_contract') && <Alert type="info" title="已证明没有活跃合约（no_active_contract）" />}
      {result.day.observations.some(o => o.reason === 'nonpositive_close') && <Alert type="warning" title="非正价格观察已排除（nonpositive_close）" />}
      <Typography.Paragraph type="secondary">合法零价差显示为 0；未提供的数值不会补零。</Typography.Paragraph>
    </Card>
    <Collapse items={[{ key: 'about', label: '关于本数据', children: <>
      <Typography.Paragraph>计算使用真实合约同日 Close 和两合约最后交易日间隔。年化价差是价格关系，不代表实际收益率或交易指令。</Typography.Paragraph>
      <Typography.Paragraph>{result.source_context.provider} / {result.source_context.exchange} / {result.source_context.price_field}</Typography.Paragraph>
      {result.source_context.limitations.map((text, i) => <Typography.Paragraph key={i}>{text}</Typography.Paragraph>)}
    </> }]} />
  </Flex>
}
