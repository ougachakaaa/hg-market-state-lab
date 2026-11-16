import { Alert, Collapse, Flex, Space, Table, Typography } from 'antd'
import { formatUnit } from '../../../shared/format/unit'
import { formatPercent } from '../../../shared/format/number'
import type { Analysis } from '../api/validateResearch'
import { Facts } from './Facts'
import { displayValue } from './displayValue'

const ratio = (value: number | null) => value === null ? 'N/A' : formatPercent(value)
function fact(value: { expected_fact_count: number; available_fact_count: number; coverage_ratio: number | null }) {
  return {
    expected_fact_count: value.expected_fact_count,
    available_fact_count: value.available_fact_count,
    coverage_ratio: ratio(value.coverage_ratio),
  }
}

export function AnalysisDetails({ analysis }: { analysis: Analysis }) {
  const result = analysis.result
  const coverage = analysis.coverage
  return <Space orientation="vertical" size="middle" style={{ width: '100%' }}>
    <Typography.Text>实际结果状态：{analysis.outcome}{analysis.reason ? ` — ${analysis.reason}` : ''}</Typography.Text>
    {result && <>
      <Facts title="原始统计结果" data={{ method: result.method, sample_count: result.sample_count, unit: result.unit, ...(result.method === 'quantile' ? { estimator: result.estimator } : {}) }} />
      {result.unit === 'decimal_ratio' && <Typography.Text type="secondary">比例数值以一位小数百分比展示；原始单位与证据保持 decimal_ratio。</Typography.Text>}
      {result.method === 'quantile' ? <Table size="small" pagination={false} rowKey="key" dataSource={result.points_and_values.map(([probability, resultValue], key) => ({ key, probability, resultValue }))} columns={[{ title: '概率 Probability', dataIndex: 'probability', render: (value: number) => formatPercent(value) }, { title: '数值 Value', dataIndex: 'resultValue', render: v => formatUnit(v, result.unit) }]} /> : <Table size="small" pagination={false} rowKey="label" dataSource={[
        { label: 'Underflow', left: '−∞', right: formatUnit(result.edges[0], result.unit), left_inclusive: 'N/A', right_inclusive: 'N/A', count: result.underflow_count, frequency: result.underflow_frequency },
        ...result.bins.map((bin, i) => ({ ...bin, label: `Bin ${i + 1}`, left: formatUnit(bin.left, result.unit), right: formatUnit(bin.right, result.unit), left_inclusive: displayValue(bin.left_inclusive), right_inclusive: displayValue(bin.right_inclusive) })),
        { label: 'Overflow', left: formatUnit(result.edges.at(-1), result.unit), right: '+∞', left_inclusive: 'N/A', right_inclusive: 'N/A', count: result.overflow_count, frequency: result.overflow_frequency },
      ]} columns={[
        { title: '区间', dataIndex: 'label' }, { title: '左边界', dataIndex: 'left' }, { title: '右边界', dataIndex: 'right' },
        { title: '包含左边界', dataIndex: 'left_inclusive' }, { title: '包含右边界', dataIndex: 'right_inclusive' },
        { title: '计数 Count', dataIndex: 'count' }, { title: '频率 Frequency', dataIndex: 'frequency', render: (value: number) => formatPercent(value) },
      ]} scroll={{ x: 820 }} />}
    </>}
    {coverage ? <>
      <Facts title="观察总体与覆盖" data={{ candidate_count: coverage.candidate_count, eligible_count: coverage.eligible_count, unavailable_count: coverage.unavailable_count, excluded_count: coverage.excluded_count, observation_coverage: ratio(coverage.observation_coverage), unavailable_ratio: ratio(coverage.unavailable_ratio), excluded_ratio: ratio(coverage.excluded_ratio) }} />
      <Collapse items={[{ key: 'evidence', label: '展开覆盖与来源证据', children: <Flex vertical gap="middle">{(['overall', 'warm_up', 'sample'] as const).map(name => <Facts key={name} title={`Market fact coverage — ${name}`} data={fact(coverage.market_facts[name])} />)}
      <Facts title="来源与输入证据 Provenance" data={{ observation_unit: coverage.observation_unit, input_profile: coverage.input_profile, input_fingerprint: coverage.input_fingerprint }} /></Flex> }]} />
    </> : <Alert type="info" title="Coverage 不可用" description="未发布观察覆盖；不表示覆盖完整或研究成功。" />}
  </Space>
}
