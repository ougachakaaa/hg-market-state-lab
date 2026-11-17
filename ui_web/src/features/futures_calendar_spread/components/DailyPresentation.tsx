import { Alert, Card, Collapse, Descriptions, Flex, Table, Typography } from 'antd'
import type { Result } from '../api/validateResult'
import { metricLabels, number, count, expiryLabels, indexStatusLabels, sourceNote } from '../model/format'
import { historicalReferenceNote, historicalSpotNote } from '../model/export'
import { ExportActions } from './ExportActions'

type Observation = Result['day']['observations'][number]
type Spot = NonNullable<Result['futures_spot_comparisons']>[number]
const metricValue = (value: number | null | undefined, ratio = false) => value == null ? '—' : number(value, ratio)
export function DailyPresentation({ result }: { result: Result }) {
  const reasons = { no_active_contract: '没有活跃合约', nonpositive_close: '收盘价非正', index_reference_unavailable: '同日指数参考不可用', expiry_day: '合约到期日，年化指标不适用', calculation_failure: '数值计算失败，指标未提供' }
  const spots = result.futures_spot_comparisons
  const notes = [...result.day.observations.filter(o => o.reason).map(o => `${o.near_slot}/${o.far_slot}：${reasons[o.reason!]}`), ...(spots ?? []).filter(o => o.reason).map(o => `${o.slot}/现货：${reasons[o.reason!]}`)]
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
        {result.day.status === 'closed' ? <Alert type="info" title="休市日" description="该日无跨期观察，不回退到其他交易日。" /> : <Table<Observation> size="small" rowKey={o => `${o.near_slot}/${o.far_slot}`} pagination={false} title={() => '跨期比较'} scroll={{ x: 1320 }} dataSource={result.day.observations} columns={[
          { title: '比较组合', width: 90, render: (_, o) => `${o.near_slot}/${o.far_slot}`, fixed: 'left' },
          ...(['near', 'far'] as const).map(side => ({ title: `${side === 'near' ? '近端' : '远端'}合约`, width: 125, render: (_: unknown, o: Observation) => o[side]?.contract_code ?? '—' })),
          ...(['near', 'far'] as const).map(side => ({ title: `${side === 'near' ? '近端' : '远端'}收盘价`, width: 100, render: (_: unknown, o: Observation) => metricValue(o[side]?.close) })),
          ...(['signed_spread', 'annualized_point_spread', 'annualized_spread_ratio'] as const).map(metric => ({ title: metricLabels[metric], width: metric === 'annualized_point_spread' ? 140 : 105, render: (_: unknown, o: Observation) => metricValue(o.metrics?.[metric].value, metric === 'annualized_spread_ratio') })),
          { title: '期限差（自然日）', width: 95, render: (_, o) => count(o.delta_days) },
          { title: '近端剩余到期天数', width: 100, render: (_, o) => count(o.near_dte_days) },
          { title: '到期阶段', width: 110, render: (_, o) => o.expiry_stage ? expiryLabels[o.expiry_stage] : '未提供' },
        ]} />}
        {!Object.hasOwn(result, 'futures_spot_comparisons') ? <Typography.Text>{historicalSpotNote}</Typography.Text> : result.day.status === 'open' && <Table<Spot> size="small" title={() => '期现比较'} rowKey="slot" pagination={false} scroll={{ x: 1200 }} dataSource={spots} columns={[
          { title: '比较组合', width: 90, fixed: 'left', render: (_, o) => `${o.slot}/现货` },
          { title: '期货合约', width: 125, render: (_, o) => o.futures?.contract_code ?? '—' },
          { title: '现货指数', width: 125, render: (_, o) => o.underlying_index.index_code },
          { title: '期货收盘价', width: 100, render: (_, o) => metricValue(o.futures?.close) },
          { title: '现货收盘价', width: 100, render: (_, o) => metricValue(o.underlying_index.close) },
          ...(['signed_spread', 'annualized_point_spread', 'annualized_spread_ratio'] as const).map(key => ({ title: metricLabels[key], width: 140, render: (_: unknown, o: Spot) => metricValue(o[key], key === 'annualized_spread_ratio') })),
          { title: '期货剩余期限（自然日）', width: 130, render: (_, o) => count(o.remaining_days) },
          { title: '到期阶段', width: 110, render: (_, o) => o.expiry_stage ? expiryLabels[o.expiry_stage] : '—' },
        ]} />}
        {notes.length > 0 && <>
          <Alert type="info" title="部分比较指标不适用或不可用，详见数据说明。" />
          <Collapse items={[{ key: 'data', label: '数据说明', children: notes.map(note => <Typography.Paragraph key={note}>{note}</Typography.Paragraph>) }]} />
        </>}
        <Typography.Paragraph type="secondary">合法零价差显示为 0.00；未提供的数值不会补零。</Typography.Paragraph>
      </Flex>
    </Card>
    <Collapse items={[{ key: 'about', label: '关于本数据', children: <>
      <Typography.Paragraph>跨期比较使用近端减远端收盘价，以两合约最后交易日间隔年化；期现比较使用期货减同日指数收盘价，以期货剩余自然日数年化。年化价差是价格关系，不代表实际收益率或交易指令。</Typography.Paragraph>
      <Typography.Paragraph>数据源：{result.source_context.provider} / 交易所：{result.source_context.exchange} / 价格字段：{result.source_context.price_field === 'close' ? '收盘价' : result.source_context.price_field}</Typography.Paragraph>
      {result.source_context.limitations.map((text, i) => <Typography.Paragraph key={i}>{sourceNote(text)}</Typography.Paragraph>)}
    </> }]} />
  </Flex>
}
