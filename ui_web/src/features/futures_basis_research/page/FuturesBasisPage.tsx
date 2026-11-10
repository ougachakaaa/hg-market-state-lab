import { Alert, Button, Card, DatePicker, Descriptions, Flex, Form, Empty, Select, Badge, Tag, Typography } from 'antd'
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
const phases: Record<string, { label: string; color: string }> = {
  IDLE: { label: '尚未提交', color: 'default' },
  PENDING: { label: '已接受，等待执行', color: 'processing' },
  RUNNING: { label: '正在执行', color: 'processing' },
  REPORT_LOADING: { label: '执行已完成 · 正在读取报告', color: 'processing' },
  COMPLETED: { label: '执行已完成 · 报告已就绪', color: 'success' },
  FAILED: { label: '执行失败', color: 'error' },
  INTERRUPTED: { label: '执行已中断', color: 'warning' },
  STATUS_ERROR: { label: '状态读取失败', color: 'error' },
  REPORT_ERROR: { label: '执行已完成 · 报告读取失败', color: 'error' },
  UNKNOWN_RUN: { label: '研究不存在或不可访问', color: 'warning' },
  UNAVAILABLE: { label: '服务暂不可用', color: 'warning' },
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
  const phase = phases[research.phase]
  const retryReport = research.phase === 'REPORT_ERROR' || research.errorRead === 'report'
  return <Flex vertical gap="large" style={{ minWidth: 0 }}>
    <Flex vertical gap="small">
      <Typography.Title level={2} style={{ margin: 0 }}>Futures Basis Research</Typography.Title>
      <Typography.Text type="secondary">期货基差研究 · 选择参数、提交 Run，再阅读报告与证据。</Typography.Text>
    </Flex>
    <Card title="研究参数" size="small">
      <Form form={form} layout="vertical" onKeyDown={event => {
        // Enter commits a date/selection; only the explicit button submits a non-idempotent Run.
        if (event.key === 'Enter' && event.target instanceof HTMLInputElement) event.preventDefault()
      }} onFinish={v => void research.submit({ product_code: v.product_code, start_date: v.start_date.format('YYYY-MM-DD'), end_date: v.end_date.format('YYYY-MM-DD') })}>
        <Flex gap="middle" wrap align="end">
          <Form.Item label="品种" name="product_code" rules={[{ required: true, message: '请选择品种' }]}><Select aria-label="品种" options={products.map(value => ({ value, label: value }))} placeholder="选择品种" style={{ width: 140 }} /></Form.Item>
          <Form.Item label="开始日期" name="start_date" rules={[{ required: true, message: '请选择开始日期' }]}><DatePicker aria-label="开始日期" format="YYYY-MM-DD" placeholder="YYYY-MM-DD" /></Form.Item>
          <Form.Item label="结束日期" name="end_date" rules={[{ required: true, message: '请选择结束日期' }]}><DatePicker aria-label="结束日期" format="YYYY-MM-DD" placeholder="YYYY-MM-DD" /></Form.Item>
          <Form.Item><Button type="primary" htmlType="button" onClick={() => form.submit()} disabled={!ready || research.submitting} loading={research.submitting}>生成研究</Button></Form.Item>
        </Flex>
      </Form>
      <Typography.Text type="secondary">仅点击「生成研究」才会创建新 Run；修改参数或按 Enter 不会执行。日期包含首尾，范围由服务器验证。在线入口可用不代表 Provider / Cache Ready；年化基差率是研究指标。</Typography.Text>
      {research.submitting && <Alert showIcon type="info" title="正在提交 · SUBMITTING" description="等待服务器确认 Run；已有结果仍可阅读。" />}
      {research.feedback && <Alert showIcon type="warning" title={messages[research.feedback.kind] ?? '提交未被确认。'} description={research.feedback.kind === 'invalid_request' ? research.feedback.detail : undefined} />}
    </Card>
    <Card title="当前 Run" size="small" extra={<Tag color={phase.color}>{research.phase}</Tag>} styles={{ body: { display: 'flex', flexDirection: 'column', gap: 16 } }}>
      {research.phase !== 'IDLE' && <Flex gap="small" align="center">
        <Badge status={phase.color as 'default' | 'processing' | 'success' | 'error' | 'warning'} />
        <Typography.Text strong>{phase.label}</Typography.Text>
      </Flex>}
      {(research.run || research.id) && <Descriptions size="small" column={{ xs: 1, md: 2 }} items={[
        { key: 'id', label: 'Run ID', span: 2, children: <Typography.Text copyable style={{ overflowWrap: 'anywhere' }}>{research.run?.run_id ?? research.id}</Typography.Text> },
        ...(research.run ? [
          { key: 'request', label: '已接受的请求', children: `${research.run.request.product_code} / ${research.run.request.start_date} 至 ${research.run.request.end_date}` },
          { key: 'created', label: '创建时间', children: research.run.created_at },
          { key: 'profile', label: '分析 Profile', children: research.run.request.analysis_profile },
        ] : []),
      ]} />}
      {research.run && <Typography.Text type="secondary">当前 Run 使用已接受的固定参数；上方编辑仅用于下一次研究。</Typography.Text>}
      {research.phase === 'IDLE' && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选择品种和起止日期，点击「生成研究」开始。" />}
      {['PENDING', 'RUNNING'].includes(research.phase) && <Typography.Text type="secondary">自动读取服务器状态；执行时间取决于数据与研究服务。</Typography.Text>}
      {research.phase === 'REPORT_LOADING' && <Typography.Text type="secondary">执行已完成，报告读取成功后将在下方显示。</Typography.Text>}
      {research.phase === 'UNKNOWN_RUN' && <Alert showIcon type="warning" title="研究不存在或不可访问" description="请核对 Run 链接，或显式提交新的研究。" />}
      {research.error && research.phase !== 'UNKNOWN_RUN' && <Alert showIcon type="error"
        title={retryReport ? '报告读取失败' : '状态读取失败'}
        description={research.error.kind === 'network' ? '网络读取失败，请手动重试；不会创建新 Run。' : research.error.kind === 'invalid_response' ? '读取响应无法验证，请手动重试。' : messages[research.error.kind] ?? '读取失败，请手动重试。'} />}
      {['STATUS_ERROR', 'REPORT_ERROR', 'UNAVAILABLE'].includes(research.phase) && <Flex><Button disabled={research.submitting} onClick={() => research.retry(retryReport)}>{retryReport ? '重新读取报告' : '重新读取状态'}</Button></Flex>}
      {research.run && ['FAILED', 'INTERRUPTED'].includes(research.phase) && <Flex vertical gap="small">
        {'failure' in research.run && research.run.failure && <Alert showIcon type="error" title={`${research.run.failure.stage} / ${research.run.failure.category} / ${research.run.failure.dependency ?? '—'}`} description={research.run.failure.reason} />}
        <Typography.Text type="secondary">再次执行会使用此 Run 的固定请求创建新 Run。</Typography.Text>
        <Flex><Button disabled={research.submitting} onClick={() => { const r = research.run!.request; void research.submit({ product_code: r.product_code, start_date: r.start_date, end_date: r.end_date } as RunRequest) }}>使用原请求创建新 Run</Button></Flex>
      </Flex>}
    </Card>
    {research.report && <Report key={research.report.run_id} data={research.report.data} mode="online" />}
  </Flex>
}
