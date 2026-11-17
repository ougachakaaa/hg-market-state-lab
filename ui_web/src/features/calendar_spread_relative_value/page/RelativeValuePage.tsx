import { parseEdges } from '../model/queryInput'
import { Alert, Button, Card, Collapse, DatePicker, Flex, Form, Input, Select, Spin, Typography } from 'antd'
import { useState } from 'react'
import { products, units, type Query } from '../api/validateResult'
import { RelativeValuePresentation } from '../components/RelativeValuePresentation'
import { useQuery } from '../hooks/useQuery'
import { errorMessage, metricLabels } from '../model/format'

export default function RelativeValuePage() {
  const { state, submit, retry } = useQuery()
  const [product, setProduct] = useState<Query['product_code'] | undefined>()
  const [start, setStart] = useState(''); const [end, setEnd] = useState('')
  const [metric, setMetric] = useState<Query['metric']>('annualized_spread_ratio')
  const [edges, setEdges] = useState(''); const [inputError, setInputError] = useState('')
  let parsed: number[] | undefined; let invalidEdges = false
  try { parsed = parseEdges(edges) } catch { invalidEdges = true }
  const draft = { product_code: product, history_start: start, evaluation_date: end, metric, ...(parsed ? { histogram_edges: parsed } : {}) }
  const dirty = state.status !== 'idle' && (invalidEdges || JSON.stringify(draft) !== JSON.stringify(state.query))
  return <Flex vertical gap="large">
    <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>Calendar Spread Historical Relative Value</Typography.Title>
    <Typography.Paragraph>比较近月多头移至远月时的收盘价差关系，观察它在同到期阶段及全部阶段的历史样本中处于什么位置；不预测未来收益。</Typography.Paragraph>
    <Card><Form onKeyDown={e => { if (e.key === 'Enter' && e.target instanceof HTMLInputElement) e.preventDefault() }} layout="vertical" onFinish={() => {
      if (!product || !start || !end || start >= end) { setInputError('请填写品种与日期，历史起点必须早于评价日期。'); return }
      try { const histogram_edges = parseEdges(edges); setInputError(''); submit({ product_code: product, history_start: start, evaluation_date: end, metric, ...(histogram_edges ? { histogram_edges } : {}) }) }
      catch { setInputError('直方图边界必须是 2–128 个严格递增有限数值的 JSON 数组。') }
    }}>
      <Flex gap="middle" wrap>
        <Form.Item label="品种"><Select aria-label="品种" placeholder="选择品种" value={product} onChange={setProduct} options={products.map(value => ({ value, label: value }))} style={{ width: 120 }} /></Form.Item>
        <Form.Item label="历史起点"><DatePicker aria-label="历史起点" onChange={d => setStart(d?.format('YYYY-MM-DD') ?? '')} /></Form.Item>
        <Form.Item label="评价日期"><DatePicker aria-label="评价日期" onChange={d => setEnd(d?.format('YYYY-MM-DD') ?? '')} /></Form.Item>
        <Form.Item label="价差口径"><Select aria-label="价差口径" value={metric} onChange={setMetric} options={Object.keys(units).map(value => ({ value, label: metricLabels[value] }))} style={{ width: 330, maxWidth: '100%' }} /></Form.Item>
      </Flex>
      <Typography.Paragraph type="secondary">历史样本不含评价日。日期、价差口径与高级参数改变后，需显式重新开始研究。</Typography.Paragraph>
      <Collapse items={[{ key: 'advanced', label: '高级参数（可选）', children: <Form.Item label="直方图边界（JSON，当前口径的原始单位；比例使用小数）"><Input aria-label="直方图边界" placeholder="留空不请求；或输入 JSON 数组，例如 [-0.1, 0, 0.1]" value={edges} onChange={e => setEdges(e.target.value)} /></Form.Item> }]} style={{ marginBottom: 16 }} />
      <Button type="primary" htmlType="submit" disabled={!product || !start || !end}>开始研究</Button>
    </Form></Card>
    {inputError && <Alert type="error" title={inputError} />}
    {dirty && <Alert type="info" title="参数已修改，需重新开始研究。下方状态仍对应已提交参数。" />}
    {state.status === 'loading' && <Spin tip="正在准备所需数据并计算结果，请稍候。"><div style={{ minHeight: 80 }} /></Spin>}
    {state.status === 'error' && <Alert type="error" title={errorMessage(state.error)} description={`${state.query.product_code} · ${state.query.history_start} – ${state.query.evaluation_date} · ${state.query.metric}${state.error.param ? ` · ${state.error.param}` : ''}`} action={<Button onClick={retry}>重试原查询</Button>} />}
    {state.status === 'success' && <RelativeValuePresentation key={state.revision} result={state.result} />}
  </Flex>
}
