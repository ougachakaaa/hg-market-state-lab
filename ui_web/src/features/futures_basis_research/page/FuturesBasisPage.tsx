import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import { Alert, Checkbox, Button, DatePicker, Descriptions, Flex, Form, Empty, Select, Badge, Tag, Typography } from 'antd'
import { useEffect, useState } from 'react'
import { products } from '../api/futuresBasis'
import type { RunRequest } from '../api/futuresBasis'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import { shanghaiDate, usePreflight } from '../hooks/usePreflight'
import { useFuturesBasis } from '../hooks/useFuturesBasis'
import { FuturesBasisPresentation } from './FuturesBasisPresentation'

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

// Production composition root: it owns the query form, preflight, explicit Submit, URL Run
// identity, polling and reads, then composes those execution regions into the shared
// Futures Basis presentation. Static composition never mounts this component.
export default function FuturesBasisPage() {
  const research = useFuturesBasis()
  const [form] = Form.useForm()
  useEffect(() => {
    const error = research.feedback
    if (error?.kind === 'invalid_request' && error.param) form.setFields([{ name: error.param, errors: [error.detail] }])
  }, [research.feedback, form])
  const [values, setValues] = useState<{ product_code?: RunRequest['product_code']; start_date?: Dayjs; end_date?: Dayjs }>(() => ({ end_date: dayjs(shanghaiDate()) }))
  const query: RunRequest | undefined = values?.product_code && values?.start_date?.isValid() && values?.end_date?.isValid() && !values.start_date.isAfter(values.end_date, 'day')
    ? { product_code: values.product_code, start_date: values.start_date.format('YYYY-MM-DD'), end_date: values.end_date.format('YYYY-MM-DD') } : undefined
  const preflight = usePreflight(query)
  useEffect(() => {
    if (preflight.error?.param) form.setFields([{ name: preflight.error.param, errors: [preflight.error.detail] }])
  }, [preflight.error, form])
  const phase = phases[research.phase]
  const retryReport = research.phase === 'REPORT_ERROR' || research.errorRead === 'report'

  const parameters = <>
    <Form form={form} initialValues={{ end_date: dayjs(shanghaiDate()) }} layout="vertical" onValuesChange={(_, next) => setValues(next)} onKeyDown={event => {
      // Enter commits a date/selection; only the explicit button submits a non-idempotent Run.
      if (event.key === 'Enter' && event.target instanceof HTMLInputElement) event.preventDefault()
    }} onFinish={() => { if (query && preflight.canSubmit) void research.submit(query) }}>
      <Flex gap="middle" wrap align="end">
        <Form.Item label="品种" name="product_code" rules={[{ required: true, message: '请选择品种' }]}><Select aria-label="品种" options={products.map(value => ({ value, label: value }))} placeholder="选择品种" style={{ width: 140 }} /></Form.Item>
        <Form.Item label="开始日期" name="start_date" rules={[{ required: true, message: '请选择开始日期' }]}><DatePicker aria-label="开始日期" format="YYYY-MM-DD" placeholder="YYYY-MM-DD" /></Form.Item>
        <Form.Item label="结束日期" name="end_date" dependencies={['start_date']} rules={[{ required: true, message: '请选择结束日期' }, ({ getFieldValue }) => ({ validator(_, value) { const start = getFieldValue('start_date'); return !start || !value || !start.isAfter(value, 'day') ? Promise.resolve() : Promise.reject(new Error('结束日期不能早于开始日期')) } })]}><DatePicker aria-label="结束日期" format="YYYY-MM-DD" placeholder="YYYY-MM-DD" /></Form.Item>
        <Form.Item><Button icon={<PlayCircleOutlined aria-hidden="true" />} type="primary" htmlType="button" onClick={() => form.submit()} disabled={!query || !preflight.canSubmit || research.submitting} loading={research.submitting}>生成研究</Button></Form.Item>
      </Flex>
    </Form>
    <Typography.Text type="secondary">仅点击「生成研究」才会创建新 Run；修改参数或按 Enter 不会执行。输入检查不会获取数据，执行仍可能失败。日期包含首尾，范围由服务器验证。年化基差率是研究指标。</Typography.Text>
    <Flex vertical gap="small">
      <Button icon={<ReloadOutlined aria-hidden="true" />} onClick={preflight.refresh} disabled={!query || preflight.checking}>重新检查输入</Button>
      {preflight.checking && <Alert type="info" showIcon title="正在检查本地数据覆盖" />}
      {preflight.error && <Alert type="error" showIcon title="输入检查失败，请重新检查" description={preflight.error.detail || '网络或响应异常；尚未创建 Run。'} />}
      {preflight.result && <>
        <Alert showIcon type={preflight.result.submission === 'blocked' ? 'warning' : 'info'}
          title={preflight.result.today_gate === 'not_ready' || preflight.result.today_gate === 'unknown'
            ? '本地当日数据未就绪，请先完成数据准备，再重新检查。'
            : preflight.result.submission === 'blocked' ? '输入检查发现数据操作或契约异常，请重查或联系维护者。'
            : preflight.result.today_gate === 'ready' ? '本地当日数据已就绪。' : '历史输入检查已完成。'}
          description={`检查时间：${preflight.result.checked_at}；上海日期：${preflight.result.market_date}。可修改结束日期或重新检查；本检查不保证执行成功。`} />
        <Descriptions size="small" column={1} items={preflight.result.dependencies.map(item => ({
          key: `${item.scope}-${item.dependency}`,
          label: `${item.scope === 'today' ? '当日' : '整段'} / ${{ calendar_cffex: '中金所日历', calendar_sse: '上交所日历', futures: '期货日线', index: '指数日线' }[item.dependency]}`,
          children: `${item.message}${item.coverage ? ` 完整目标 ${item.coverage.successful_units}/${item.coverage.requested_units}；缺失 ${item.coverage.missing_units}，待处理 ${item.coverage.pending_units}，失败 ${item.coverage.failed_units}。` : ''}`,
        }))} />
        {preflight.result.submission === 'confirm_required' && <Checkbox checked={preflight.confirmed} onChange={event => preflight.confirm(event.target.checked)}>我理解正式执行将尝试获取缺失数据，仍可能失败。</Checkbox>}
      </>}
    </Flex>
    {research.submitting && <Alert showIcon type="info" title="正在提交 · SUBMITTING" description="等待服务器确认 Run；已有结果仍可阅读。" />}
    {research.feedback && <Alert showIcon type="warning" title={messages[research.feedback.kind] ?? '提交未被确认。'} description={research.feedback.kind === 'invalid_request' ? research.feedback.detail : undefined} />}
  </>

  const run = <>
    {research.phase !== 'IDLE' && <Flex gap="small" align="center" wrap>
      <Badge status={phase.color as 'default' | 'processing' | 'success' | 'error' | 'warning'} />
      <Typography.Text strong>{phase.label}</Typography.Text>
      <Tag color={phase.color}>{research.phase}</Tag>
    </Flex>}
    {(research.run || research.id) && <Descriptions size="small" column={{ xs: 1, md: 2 }} items={[
      { key: 'id', label: 'Run ID', span: 2, children: <Typography.Text copyable style={{ overflowWrap: 'anywhere' }}>{research.run?.run_id ?? research.id}</Typography.Text> },
      ...(research.run ? [{ key: 'created', label: '创建时间', children: research.run.created_at }] : []),
    ]} />}
    {research.run && <Typography.Text type="secondary">当前 Run 使用已接受的固定参数；上方编辑仅用于下一次研究。</Typography.Text>}
    {research.phase === 'IDLE' && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选择品种和起止日期，点击「生成研究」开始。" />}
    {['PENDING', 'RUNNING'].includes(research.phase) && <Typography.Text type="secondary">自动读取服务器状态；执行时间取决于数据与研究服务。</Typography.Text>}
    {research.phase === 'REPORT_LOADING' && <Typography.Text type="secondary">执行已完成，报告读取成功后将在下方显示。</Typography.Text>}
    {research.phase === 'UNKNOWN_RUN' && <Alert showIcon type="warning" title="研究不存在或不可访问" description="请核对 Run 链接，或显式提交新的研究。" />}
    {research.error && research.phase !== 'UNKNOWN_RUN' && <Alert showIcon type="error"
      title={retryReport ? '报告读取失败' : '状态读取失败'}
      description={research.error.kind === 'network' ? '网络读取失败，请手动重试；不会创建新 Run。' : research.error.kind === 'invalid_response' ? '读取响应无法验证，请手动重试。' : messages[research.error.kind] ?? '读取失败，请手动重试。'} />}
    {['STATUS_ERROR', 'REPORT_ERROR', 'UNAVAILABLE'].includes(research.phase) && <Flex><Button icon={<ReloadOutlined aria-hidden="true" />} disabled={research.submitting} onClick={() => research.retry(retryReport)}>{retryReport ? '重新读取报告' : '重新读取状态'}</Button></Flex>}
    {research.run && ['FAILED', 'INTERRUPTED'].includes(research.phase) && <Flex vertical gap="small">
      {'failure' in research.run && research.run.failure && <Alert showIcon type="error" title={`${research.run.failure.stage} / ${research.run.failure.category} / ${research.run.failure.dependency ?? '—'}`} description={research.run.failure.reason} />}
      <Typography.Text type="secondary">此操作先将原请求填入参数并检查；之后点击「生成研究」才会创建新 Run。</Typography.Text>
      <Flex><Button disabled={research.submitting} onClick={() => { const r = research.run!.request; const next = { product_code: r.product_code, start_date: dayjs(r.start_date), end_date: dayjs(r.end_date) }; form.setFieldsValue(next); setValues(next); preflight.refresh() }}>使用原请求创建新 Run</Button></Flex>
    </Flex>}
  </>

  return <FuturesBasisPresentation
    mode="production"
    parameters={parameters}
    run={run}
    request={research.run?.request ?? null}
    report={research.report?.data}
    reportKey={research.report?.run_id}
  />
}
