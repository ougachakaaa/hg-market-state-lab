import { Alert, Card, Collapse, Descriptions, Flex, Table, Typography } from 'antd'
import type { Result } from '../api/validateResult'
import { metricLabels, number, count, expiryLabels, indexStatusLabels, sourceNote } from '../model/format'
import { historicalReferenceNote } from '../model/export'
import { ExportActions } from './ExportActions'

type Observation = Result['day']['observations'][number]
export function DailyPresentation({ result }: { result: Result }) {
  const labels = { valid: '有效', not_applicable: '不适用', excluded: '已排除' }
  const reasons = { no_active_contract: '没有活跃合约', nonpositive_close: '收盘价非正' }
  const ref = result.underlying_index
  return <Flex vertical gap="middle">
    <Card title="已查询数据">
      <Flex vertical gap="middle">
        <ExportActions key={JSON.stringify(result)} result={result} />
        <Descriptions items={[{ key: 'product', label: '品种', children: result.request.product_code }, { key: 'date', label: '查询日期', children: result.request.trade_date }]} />
        <Card size="small" title="标的指数参考">
          {ref ? <Descriptions size="small" items={[
            { key: 'code', label: '标的指数代码', children: ref.index_code },
            { key: 'date', label: '查询日期', children: ref.trade_date },
            { key: 'close', label: '指数收盘价', children: number(ref.close) },
            { key: 'state', label: '数据状态', children: ref.reason_code ? indexStatusLabels[ref.reason_code] : indexStatusLabels.available },
          ]} /> : <Typography.Text>{historicalReferenceNote}</Typography.Text>}
        </Card>
        {result.day.status === 'closed' ? <Alert type="info" title="休市日" description="该日无跨期观察，不回退到其他交易日。" /> : <Table<Observation> size="small" rowKey={o => `${o.near_slot}/${o.far_slot}`} pagination={false} scroll={{ x: 1660 }} dataSource={result.day.observations} columns={[
          { title: '跨期组合', width: 90, render: (_, o) => `${o.near_slot}/${o.far_slot}`, fixed: 'left' },
          ...(['near', 'far'] as const).flatMap(side => [
            { title: `${side === 'near' ? '近端' : '远端'}合约`, width: 125, render: (_: unknown, o: Observation) => o[side]?.contract_code ?? '未提供' },
            { title: `${side === 'near' ? '近端' : '远端'}收盘价`, width: 100, render: (_: unknown, o: Observation) => number(o[side]?.close) },
            { title: `${side === 'near' ? '近端' : '远端'}最后交易日`, width: 115, render: (_: unknown, o: Observation) => o[side]?.delist_date ?? '未提供' },
          ]),
          ...(['signed_spread', 'annualized_point_spread', 'annualized_spread_ratio'] as const).map(metric => ({ title: metricLabels[metric], width: metric === 'annualized_point_spread' ? 140 : 105, render: (_: unknown, o: Observation) => number(o.metrics?.[metric].value, metric === 'annualized_spread_ratio') })),
          { title: '期限差（自然日）', width: 95, render: (_, o) => count(o.delta_days) },
          { title: '近端剩余到期天数', width: 100, render: (_, o) => count(o.near_dte_days) },
          { title: '到期阶段', width: 110, render: (_, o) => o.expiry_stage ? expiryLabels[o.expiry_stage] : '未提供' },
          { title: '结果状态', width: 80, render: (_, o) => labels[o.outcome] },
          { title: '原因', width: 100, render: (_, o) => o.reason ? reasons[o.reason] : '—' },
        ]} />}
        {result.day.observations.some(o => o.reason === 'no_active_contract') && <Alert type="info" title="已证明没有活跃合约" />}
        {result.day.observations.some(o => o.reason === 'nonpositive_close') && <Alert type="warning" title="非正价格观察已排除" />}
        <Typography.Paragraph type="secondary">合法零价差显示为 0.00；未提供的数值不会补零。</Typography.Paragraph>
      </Flex>
    </Card>
    <Collapse items={[{ key: 'about', label: '关于本数据', children: <>
      <Typography.Paragraph>计算使用真实合约同日收盘价和两合约最后交易日间隔。年化价差是价格关系，不代表实际收益率或交易指令。</Typography.Paragraph>
      <Typography.Paragraph>数据源：{result.source_context.provider} / 交易所：{result.source_context.exchange} / 价格字段：{result.source_context.price_field === 'close' ? '收盘价' : result.source_context.price_field}</Typography.Paragraph>
      {result.source_context.limitations.map((text, i) => <Typography.Paragraph key={i}>{sourceNote(text)}</Typography.Paragraph>)}
    </> }]} />
  </Flex>
}
