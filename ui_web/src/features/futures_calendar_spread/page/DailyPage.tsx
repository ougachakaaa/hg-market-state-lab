import { Alert, Button, Card, DatePicker, Flex, Form, Select, Spin, Typography } from 'antd'
import { useState } from 'react'
import dateLocale from 'antd/es/date-picker/locale/zh_CN'
import { products, type Query } from '../api/validateResult'
import { DailyPresentation } from '../components/DailyPresentation'
import { useQuery } from '../hooks/useQuery'
import { errorMessage } from '../model/format'
export default function DailyPage() {
  const { state, submit, retry } = useQuery()
  const [product, setProduct] = useState<Query['product_code'] | undefined>()
  const [date, setDate] = useState('')
  const dirty = state.status !== 'idle' && (state.query.product_code !== product || state.query.trade_date !== date)
  return <Flex vertical gap="large">
    <Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>股指期货跨期价差</Typography.Title>
    <Card><Form onKeyDown={e => { if (e.key === 'Enter' && e.target instanceof HTMLInputElement) e.preventDefault() }} layout="inline" onFinish={() => { if (product && date) submit({ product_code: product, trade_date: date }) }}>
      <Form.Item label="品种"><Select aria-label="品种" placeholder="选择品种" value={product} onChange={setProduct} options={products.map(value => ({ value, label: `${value} · ${{ IF: '沪深300', IH: '上证50', IC: '中证500', IM: '中证1000' }[value]}` }))} style={{ width: 180 }} /></Form.Item>
      <Form.Item label="查询日期"><DatePicker aria-label="查询日期" placeholder="选择查询日期" locale={dateLocale} onChange={d => setDate(d?.format('YYYY-MM-DD') ?? '')} /></Form.Item>
      <Form.Item><Button aria-label="查询" htmlType="submit" type="primary" disabled={!product || !date}>查询</Button></Form.Item>
    </Form></Card>
    {dirty && <Alert type="info" title="参数已修改，需重新查询。下方状态仍对应已提交参数。" />}
    {state.status === 'loading' && <Spin description="正在准备所需数据并计算结果，请稍候。"><div style={{ minHeight: 80 }} /></Spin>}
    {state.status === 'error' && <Alert type="error" title={errorMessage(state.error)} description={`${state.query.product_code} · ${state.query.trade_date}${state.error.param ? ` · ${{ product_code: '品种', trade_date: '查询日期' }[state.error.param] ?? state.error.param}` : ''}`} action={<Button onClick={retry}>重试原查询</Button>} />}
    {state.status === 'success' && <DailyPresentation key={state.revision} result={state.result} />}
  </Flex>
}
