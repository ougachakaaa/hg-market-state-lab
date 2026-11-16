import { useMemo, useState } from 'react'
import { Card, Collapse, Flex, Statistic, Typography } from 'antd'
import { ChartView, DateAxisControl, DEFAULT_DATE_AXIS_MODE, type DateAxisMode } from '../../../shared/visualization'
import type { BacktestResult } from '../api/validateResult'
import { resultChartOptions, tradingDates } from '../model/dateAxis'
import { backtestQuestion, strategyExplanation, strategyView } from '../model/strategyPresentation'
import { money, percent } from '../model/presentation'

export function Result({ data, mode = 'production', sourceDisclosure }: { sourceDisclosure?: string; data: BacktestResult; mode?: 'production' | 'static' }) {
  const s = data.summary
  const [timeScale, setTimeScale] = useState<DateAxisMode>(DEFAULT_DATE_AXIS_MODE)
  // Stable references: ChartView treats a new ordinal domain as a coordinate-system change.
  const dates = useMemo(() => tradingDates(data.daily), [data.daily])
  const options = useMemo(() => resultChartOptions(dates, timeScale), [dates, timeScale])
  const views = useMemo(() => ({ returns: strategyView(data.views.returns), drawdown: strategyView(data.views.drawdown) }), [data.views])
  return <Card title="回测报告" data-testid="backtest-result" style={{ minWidth: 0 }}>
    <Flex vertical gap="middle" style={{ minWidth: 0 }}>
      <section>
        <Typography.Title level={4}>回测问题</Typography.Title>
        <Typography.Paragraph>{backtestQuestion}</Typography.Paragraph>
      </section>
      <section>
        <Typography.Title level={4}>核心统计结果</Typography.Title>
        <Typography.Paragraph type="secondary">初始指数等效名义本金 {money(data.initial_notional.value)}</Typography.Paragraph>
        <Flex gap="middle" wrap>
          <Statistic style={{ flex: '1 1 180px' }} title="策略累计毛收益率" value={percent(s.gross_return)} />
          <Statistic style={{ flex: '1 1 180px' }} title="基准收益率" value={percent(s.benchmark_return)} />
          <Statistic style={{ flex: '1 1 180px' }} title="超额收益率" value={percent(s.excess_return)} />
          <Statistic style={{ flex: '1 1 180px' }} title="策略最大回撤" value={percent(s.strategy_max_drawdown)} />
          <Statistic style={{ flex: '1 1 180px' }} title="基准最大回撤" value={percent(s.benchmark_max_drawdown)} />
          <Statistic style={{ flex: '1 1 180px' }} title="累计 PnL" value={money(s.total_pnl)} />
          <Statistic style={{ flex: '1 1 180px' }} title="展期次数" value={s.roll_count} />
        </Flex>
      </section>
      <Collapse items={[{ key: 'rules', label: '策略规则与收益口径', children: <>
        <Typography.Paragraph>{strategyExplanation(data.request.strategy_profile)}</Typography.Paragraph>
        <Typography.Paragraph>使用固定初始指数等效名义本金，理想收盘价成交，未考虑手续费、滑点、保证金与融资成本。指数基准为对应标的指数价格收益，不是可直接交易的实盘账户。</Typography.Paragraph>
      </> }]} />
      <section style={{ minWidth: 0 }}>
        <Typography.Title level={4}>回测可视化</Typography.Title>
        <DateAxisControl label="收益与回撤时间轴" value={timeScale} onChange={setTimeScale} />
        <Typography.Title level={5}>累计收益曲线</Typography.Title>
        <div style={{ overflowX: 'auto', maxWidth: '100%' }}><div style={{ minWidth: 620 }}><ChartView view={views.returns} options={options} /></div></div>
        <Typography.Title level={5}>回撤曲线</Typography.Title>
        <div style={{ overflowX: 'auto', maxWidth: '100%' }}><div style={{ minWidth: 620 }}><ChartView view={views.drawdown} options={options} /></div></div>
      </section>
      {mode === 'static' && sourceDisclosure && <Typography.Text type="secondary" style={{ overflowWrap: 'anywhere' }}>{sourceDisclosure}</Typography.Text>}
    </Flex>
  </Card>
}
