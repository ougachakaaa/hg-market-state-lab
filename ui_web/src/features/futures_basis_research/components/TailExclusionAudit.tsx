import { Collapse, Flex, Table, Typography } from 'antd'
import { formatPercent } from '../../../shared/format/number'
import { formatUnit } from '../../../shared/format/unit'
import type { SlotSelection } from '../model/histogramAggregation'

export function TailExclusionAudit({ selections, tail }: { selections: SlotSelection[]; tail: number }) {
  const excluded = selections.flatMap(selection => selection.excluded)
  const value = (raw: number | null, row: SlotSelection) => raw === null ? '—' : formatUnit(raw, row.original[0]?.unit)
  return <Collapse items={[{
    key: 'audit', label: '尾部排除明细', children: <Flex vertical gap="small">
      <Typography.Text>计划排除比例为每尾 {tail}%，边界并列值全部保留。</Typography.Text>
      <Table<SlotSelection> size="small" rowKey="slot" pagination={false} scroll={{ x: 'max-content' }} dataSource={selections} columns={[
        { title: 'Slot', dataIndex: 'slot' },
        { title: '原始 Eligible N', render: (_, row) => row.original.length },
        { title: '下尾排除 N', dataIndex: 'lowerExcludedN' },
        { title: '上尾排除 N', dataIndex: 'upperExcludedN' },
        { title: '实际排除 N', render: (_, row) => row.excluded.length },
        { title: '参与分箱 N', render: (_, row) => row.retained.length },
        { title: '实际排除比例', render: (_, row) => row.actualExcludedFraction === null ? '—' : formatPercent(row.actualExcludedFraction) },
        { title: '下侧保留 cutoff', render: (_, row) => value(row.lowerCutoff, row) },
        { title: '上侧保留 cutoff', render: (_, row) => value(row.upperCutoff, row) },
        { title: '保留 Min', render: (_, row) => value(row.retainedMin, row) },
        { title: '保留 Max', render: (_, row) => value(row.retainedMax, row) },
      ]} />
      {excluded.length ? <Table size="small" rowKey={row => `${row.product}/${row.date}/${row.slot}/${row.metric}`}
        scroll={{ x: 'max-content' }} dataSource={excluded} pagination={{ pageSize: 10, showSizeChanger: false }} columns={[
          { title: 'Product', dataIndex: 'product' }, { title: 'Trade Date', dataIndex: 'date' },
          { title: 'Slot', dataIndex: 'slot' }, { title: 'Metric', dataIndex: 'metric' },
          { title: '指标值', render: (_, row) => formatUnit(row.value, row.unit) },
          { title: 'Raw value', render: (_, row) => <Typography.Text copyable={{ text: Object.is(row.value, -0) ? '-0' : String(row.value) }}>{Object.is(row.value, -0) ? '-0' : String(row.value)}</Typography.Text> },
          { title: '单位', dataIndex: 'unit' }, { title: '排除方向', dataIndex: 'direction' },
        ]} /> : <Typography.Text>无尾部排除记录</Typography.Text>}
    </Flex>,
  }]} />
}
