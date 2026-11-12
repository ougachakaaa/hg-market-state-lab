import { Card, Collapse, Descriptions, Flex, Statistic, Table, Typography } from 'antd'
import { ChartView } from '../../../shared/visualization'
import type { BacktestResult } from '../api/validateResult'
import { money, percent } from '../model/presentation'

export function Result({ data, mode = 'production' }: { data: BacktestResult; mode?: 'production' | 'static' }) {
  const s = data.summary
  return <Flex vertical gap="large" data-testid="backtest-result">
    <Card title="回测结果 · Result Summary">
      <Descriptions column={{ xs: 1, md: 2 }} items={[
        { key: 'product', label: '产品', children: data.request.product_code },
        { key: 'strategy', label: '策略', children: data.request.strategy_profile },
        { key: 'requested', label: '请求日期区间', children: `${data.request.start_date} → ${data.request.end_date}` },
        { key: 'observed', label: '实际交易区间', children: `${data.window.first_session} → ${data.window.last_session}（${data.window.cffex_session_count} 个交易日）` },
        { key: 'index', label: 'Benchmark Index', children: `${data.benchmark.index_name} · ${data.benchmark.index_code}` },
        { key: 'capital', label: '初始名义本金', children: money(data.initial_notional.value) },
      ]} />
      <Flex gap="large" wrap>
        <Statistic title="Total PnL" value={money(s.total_pnl)} />
        <Statistic title="Gross Return · 未扣费" value={percent(s.gross_return)} />
        <Statistic title="Benchmark Return" value={percent(s.benchmark_return)} />
        <Statistic title="Excess Return" value={percent(s.excess_return)} />
        <Statistic title="策略最大回撤" value={percent(s.strategy_max_drawdown)} />
        <Statistic title="基准最大回撤" value={percent(s.benchmark_max_drawdown)} />
        <Statistic title="Execution Count" value={s.execution_count} />
        <Statistic title="Roll Count" value={s.roll_count} />
      </Flex>
    </Card>
    <Card title="累计收益 · Cumulative Return"><div style={{ overflowX: 'auto' }}><div style={{ minWidth: 620 }}><ChartView view={data.views.returns} /></div></div></Card>
    <Card title="回撤 · Drawdown"><div style={{ overflowX: 'auto' }}><div style={{ minWidth: 620 }}><ChartView view={data.views.drawdown} /></div></div></Card>
    <Card title="交易记录 · Trades"><Table size="small" dataSource={data.trades} rowKey={row => `${row.trade_date}:${row.side}:${row.contract_code}:${row.reason}`}  scroll={{ x: 850 }} columns={[
      { title: 'Trade Date', dataIndex: 'trade_date' }, { title: 'BUY / SELL', dataIndex: 'side' },
      { title: 'Contract Code', dataIndex: 'contract_code' }, { title: 'Execution Close', dataIndex: 'price' },
      { title: 'Multiplier', dataIndex: 'multiplier' }, { title: 'Reason', dataIndex: 'reason' },
      { title: 'Selection Slot', dataIndex: 'selection_slot', render: v => v ?? '—' },
    ]} /></Card>
    <Card title="展期记录 · Rolls"><Table size="small" dataSource={data.rolls} rowKey={row => `${row.trade_date}:${row.old_contract_code}:${row.new_contract_code}`}  scroll={{ x: 750 }} columns={[
      { title: 'Roll Date', dataIndex: 'trade_date' }, { title: 'Old Contract', dataIndex: 'old_contract_code' },
      { title: 'Old Close', dataIndex: 'old_close' }, { title: 'New Contract', dataIndex: 'new_contract_code' },
      { title: 'New Close', dataIndex: 'new_close' }, { title: 'Target Slot', dataIndex: 'new_slot' },
    ]} /></Card>
    <Collapse items={[{ key: 'evidence', label: '研究证据与限制 · Evidence / Limitations', children: <>
      <Typography.Paragraph>{mode === 'production'
        ? '采用理想收盘价成交；不包含手续费、滑点和保证金机制。Benchmark 为指数价格基准。Historical Metadata 使用已记录的历史可得性假设；缓存完整不保证数据源实时性。这里是在线证据摘要。'
        : '本页来自 Embedded Synthetic Example，未执行服务器回测，也不构成完整离线证据包；未检查当前市场、缓存或 Provider 就绪。采用理想收盘价成交；不包含手续费、滑点和保证金机制。Benchmark 为指数价格基准。Historical Metadata 使用已记录的历史可得性假设；缓存完整不保证数据源实时性。以下保留 Producer Result 中的原始 Evidence 数据。'}</Typography.Paragraph>
      <Descriptions column={1} items={[
        { key: 'profile', label: 'Result Profile', children: data.profile },
        { key: 'definition', label: 'Definition Version', children: data.definition_version },
        { key: 'input', label: 'Input Profile', children: data.evidence.input_profile },
        { key: 'fingerprint', label: 'Input Fingerprint', children: <Typography.Text style={{ overflowWrap: 'anywhere' }}>{data.evidence.input_fingerprint}</Typography.Text> },
        { key: 'slot', label: 'Slot Authority', children: data.evidence.slot_resolution_authority },
      ]} />
      {(['sources', 'coverage', 'public_requests', 'limitations'] as const).map(key => <section key={key}>
        <Typography.Title level={5}>{key}</Typography.Title>
        <pre style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere' }}>{JSON.stringify(data.evidence[key], null, 2)}</pre>
      </section>)}
    </> }]} />
  </Flex>
}
