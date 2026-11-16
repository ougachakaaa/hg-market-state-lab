import { Alert, Button, Card, DatePicker, Flex, Form, Select, Spin, Typography } from 'antd'
import { useState } from 'react'
import { products, type Query } from '../api/validateResult'
import { DailyPresentation } from '../components/DailyPresentation'
import { useQuery } from '../hooks/useQuery'
import { errorMessages } from '../model/format'
export default function DailyPage() {
  const { state, submit, retry } = useQuery()
  const [product, setProduct] = useState<Query['product_code'] | undefined>()
  const [date, setDate] = useState('')
  const dirty = state.status !== 'idle' && (state.query.product_code !== product || state.query.trade_date !== date)
  return <Flex vertical gap="large">
    <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>Futures Calendar Spread</Typography.Title>
    <Card><Form onKeyDown={e => { if (e.key === 'Enter' && e.target instanceof HTMLInputElement) e.preventDefault() }} layout="inline" onFinish={() => { if (product && date) submit({ product_code: product, trade_date: date }) }}>
      <Form.Item label="Product"><Select aria-label="Product" placeholder="选择产品" value={product} onChange={setProduct} options={products.map(value => ({ value, label: value }))} style={{ width: 120 }} /></Form.Item>
      <Form.Item label="Trade Date"><DatePicker aria-label="Trade Date" onChange={d => setDate(d?.format('YYYY-MM-DD') ?? '')} /></Form.Item>
      <Form.Item><Button aria-label="查询" htmlType="submit" type="primary" disabled={!product || !date}>查询</Button></Form.Item>
    </Form></Card>
    {dirty && <Alert type="info" title="参数已修改，需重新查询。下方状态仍对应已提交参数。" />}
    {state.status === 'loading' && <Spin tip="正在查询…"><div style={{ minHeight: 80 }} /></Spin>}
    {state.status === 'error' && <Alert type="error" title={errorMessages[state.error.kind]} description={`${state.query.product_code} · ${state.query.trade_date}${state.error.param ? ` · ${state.error.param}` : ''}`} action={<Button onClick={retry}>重试原查询</Button>} />}
    {state.status === 'success' && <DailyPresentation result={state.result} />}
  </Flex>
}
