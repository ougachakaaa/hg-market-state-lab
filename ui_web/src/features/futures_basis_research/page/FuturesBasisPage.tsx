import { Alert, Button, Card, DatePicker, Descriptions, Flex, Form, Result, Select, Spin, Typography } from 'antd'
import { useEffect } from 'react'
import { products } from '../api/futuresBasis'
import type { RunRequest } from '../api/futuresBasis'
import { useFuturesBasis } from '../hooks/useFuturesBasis'
import { Report } from '../report/Report'

const messages: Record<string, string> = {
  network: '网络响应丢失。提交结果可能已被服务器接受；请勿自动重复提交。',
  invalid_response: '服务器响应无法验证。提交结果可能未知，请勿自动重复提交。',
  run_busy: 'BUSY：已有研究正在执行，请稍后手动提交。',
  invalid_request: 'FORM_ERROR：请求无效，请检查品种和日期。',
  request_too_large: 'FORM_ERROR：请求超过大小限制。',
  origin_forbidden: '访问被拒绝，请检查同源访问入口。',
  unavailable: 'UNAVAILABLE：研究运行存储或平台能力不可用，请稍后重试。',
  corrupt: '研究记录无法通过完整性校验。', unsupported_version: '此研究版本暂不支持。',
  response_too_large: '报告超过读取大小限制，无法显示。', read_busy: '报告读取容量已占用，请手动重试。',
  result_not_ready: '报告尚未准备完成。', result_unavailable: '此 Run 没有可读取的报告。',
  internal_error: '服务暂时无法完成请求。',
}
export default function FuturesBasisPage() {
  const research = useFuturesBasis()
  const [form] = Form.useForm()
  useEffect(() => {
    const error = research.feedback
    if (error?.kind === 'invalid_request' && error.param) form.setFields([{ name: error.param, errors: [error.detail] }])
  }, [research.feedback, form])
  const values = Form.useWatch([], form)
  const ready = values?.product_code && values?.start_date && values?.end_date
  return <Flex vertical gap="large">
    <Typography.Title level={2}>Futures Basis Research</Typography.Title>
    <Card title="Query">
      <Form form={form} layout="vertical" onKeyDown={event => {
        // Enter commits a date/selection; only the explicit button submits a non-idempotent Run.
        if (event.key === 'Enter' && event.target instanceof HTMLInputElement) event.preventDefault()
      }} onFinish={v => void research.submit({ product_code: v.product_code, start_date: v.start_date.format('YYYY-MM-DD'), end_date: v.end_date.format('YYYY-MM-DD') })}>
        <Flex gap="middle" wrap align="end">
          <Form.Item label="Product" name="product_code" rules={[{ required: true }]}><Select aria-label="Product" options={products.map(value => ({ value, label: value }))} style={{ minWidth: 120 }} /></Form.Item>
          <Form.Item label="Start Date" name="start_date" rules={[{ required: true }]}><DatePicker aria-label="Start Date" format="YYYY-MM-DD" /></Form.Item>
          <Form.Item label="End Date" name="end_date" rules={[{ required: true }]}><DatePicker aria-label="End Date" format="YYYY-MM-DD" /></Form.Item>
          <Form.Item><Button type="primary" htmlType="submit" disabled={!ready || research.submitting} loading={research.submitting}>Generate Research</Button></Form.Item>
        </Flex>
      </Form>
      <Typography.Text type="secondary">无默认品种或日期。服务器验证请求范围；在线入口可用不代表 Provider / Cache Ready。年化基差率是研究指标。</Typography.Text>
      {research.submitting && <Alert type="info" title="SUBMITTING" />}
      {research.feedback && <Alert type="warning" title={messages[research.feedback.kind] ?? '提交未被确认。'} description={research.feedback.kind === 'invalid_request' ? research.feedback.detail : undefined} />}
    </Card>
    <Card title="Run Status">
      {research.run && <Descriptions column={1} items={[
        { key: 'id', label: 'Run ID', children: <Typography.Text copyable>{research.run.run_id}</Typography.Text> },
        { key: 'request', label: 'Immutable Request', children: `${research.run.request.product_code} / ${research.run.request.start_date}..${research.run.request.end_date} / ${research.run.request.analysis_profile}` },
        { key: 'created', label: 'Created', children: research.run.created_at },
      ]} />}
      <Typography.Paragraph>{research.phase}</Typography.Paragraph>
      {['PENDING', 'RUNNING', 'REPORT_LOADING'].includes(research.phase) && <Spin description="正在读取研究状态或报告" />}
      {research.phase === 'IDLE' && <Typography.Text>选择品种与日期后生成研究。</Typography.Text>}
      {research.phase === 'UNKNOWN_RUN' && <Result status="404" title="研究不存在或不可访问" />}
      {research.error && research.phase !== 'UNKNOWN_RUN' && <Alert type="error" title={research.error.kind === 'network' ? '读取失败，请手动重试当前状态或报告；不会创建新 Run。' : research.error.kind === 'invalid_response' ? '读取响应无法验证，请手动重试。' : messages[research.error.kind] ?? '读取失败，请手动重试。'} />}
      {['STATUS_ERROR', 'REPORT_ERROR', 'UNAVAILABLE'].includes(research.phase) && <Button disabled={research.submitting} onClick={() => research.retry(research.phase === 'REPORT_ERROR' || research.run?.status === 'COMPLETED')}>{research.phase === 'REPORT_ERROR' || research.run?.status === 'COMPLETED' ? 'Retry report' : 'Retry status'}</Button>}
      {research.run && ['FAILED', 'INTERRUPTED'].includes(research.phase) && <Flex vertical gap="small">
        {'failure' in research.run && research.run.failure && <Alert type="error" title={`${research.run.failure.stage} / ${research.run.failure.category} / ${research.run.failure.dependency ?? '—'}`} description={research.run.failure.reason} />}
        <Button disabled={research.submitting} onClick={() => { const r = research.run!.request; void research.submit({ product_code: r.product_code, start_date: r.start_date, end_date: r.end_date } as RunRequest) }}>Retry as new Run</Button>
      </Flex>}
    </Card>
    {research.report && <Report key={research.report.run_id} data={research.report.data} mode="online" />}
  </Flex>
}
