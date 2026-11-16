import { parseEdges } from '../model/queryInput'
import { Alert, Button, Card, DatePicker, Flex, Form, Input, Select, Spin, Typography } from 'antd'
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
    <Card><Form onKeyDown={e => { if (e.key === 'Enter' && e.target instanceof HTMLInputElement) e.preventDefault() }} layout="vertical" onFinish={() => {
      if (!product || !start || !end || start >= end) { setInputError('请填写产品与日期，History Start 必须早于 Evaluation Date。'); return }
      try { const histogram_edges = parseEdges(edges); setInputError(''); submit({ product_code: product, history_start: start, evaluation_date: end, metric, ...(histogram_edges ? { histogram_edges } : {}) }) }
      catch { setInputError('Histogram Edges 必须是 2–128 个严格递增有限数值的 JSON 数组。') }
    }}>
      <Flex gap="middle" wrap>
        <Form.Item label="Product"><Select aria-label="Product" placeholder="选择产品" value={product} onChange={setProduct} options={products.map(value => ({ value, label: value }))} style={{ width: 120 }} /></Form.Item>
        <Form.Item label="History Start"><DatePicker aria-label="History Start" onChange={d => setStart(d?.format('YYYY-MM-DD') ?? '')} /></Form.Item>
        <Form.Item label="Evaluation Date"><DatePicker aria-label="Evaluation Date" onChange={d => setEnd(d?.format('YYYY-MM-DD') ?? '')} /></Form.Item>
        <Form.Item label="Metric"><Select aria-label="Metric" value={metric} onChange={setMetric} options={Object.keys(units).map(value => ({ value, label: metricLabels[value] }))} style={{ width: 330, maxWidth: '100%' }} /></Form.Item>
      </Flex>
      <Form.Item label="Histogram Edges（可选，当前 Metric 的原始单位；Ratio 使用小数）"><Input aria-label="Histogram Edges" placeholder="留空不请求；或输入 JSON 数组，例如 [-0.1, 0, 0.1]" value={edges} onChange={e => setEdges(e.target.value)} /></Form.Item>
      <Button type="primary" htmlType="submit" disabled={!product || !start || !end}>开始研究</Button>
    </Form></Card>
    {inputError && <Alert type="error" title={inputError} />}
    {dirty && <Alert type="info" title="参数已修改，需重新开始研究。下方状态仍对应已提交参数。" />}
    {state.status === 'loading' && <Spin tip="正在准备所需数据并计算结果，请稍候。"><div style={{ minHeight: 80 }} /></Spin>}
    {state.status === 'error' && <Alert type="error" title={errorMessage(state.error)} description={`${state.query.product_code} · ${state.query.history_start} – ${state.query.evaluation_date} · ${state.query.metric}${state.error.param ? ` · ${state.error.param}` : ''}`} action={<Button onClick={retry}>重试原查询</Button>} />}
    {state.status === 'success' && <RelativeValuePresentation key={state.revision} result={state.result} />}
  </Flex>
}
