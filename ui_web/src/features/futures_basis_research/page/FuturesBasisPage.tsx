import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons'
import { Alert, Collapse, Button, DatePicker, Descriptions, Flex, Form, Empty, Select, Tag, Typography } from 'antd'
import { useEffect, useState } from 'react'
import { products } from '../api/futuresBasis'
import type { RunRequest } from '../api/futuresBasis'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import { shanghaiDate, usePreflight } from '../hooks/usePreflight'
import { useFuturesBasis } from '../hooks/useFuturesBasis'
import { formatBeijingTime } from '../../../shared/format/time'
import { FuturesBasisPresentation } from './FuturesBasisPresentation'

const messages: Record<string, string> = {
  network: '网络响应丢失。提交结果可能已被服务器接受；请勿自动重复提交。',
  invalid_response: '服务器响应无法验证。提交结果可能未知，请勿自动重复提交。',
  run_busy: 'BUSY：已有研究正在执行，请稍后手动提交。',
  invalid_request: 'FORM_ERROR：请求无效，请检查品种和日期。',
  request_too_large: 'FORM_ERROR：请求超过大小限制。',
  origin_forbidden: '访问被拒绝，请检查同源访问入口。',
  unavailable: '研究运行存储暂不可用。若持续失败，请联系维护者查看后端日志，修正原因后按需重启后端。',
  corrupt: '研究记录无法通过完整性校验。', unsupported_version: '此研究记录的版本暂不受支持。',
  response_too_large: '报告超过读取大小限制，无法显示。', read_busy: '报告读取容量已占用，请手动重试。',
  result_not_ready: '报告尚未准备完成。', result_unavailable: '此 Run 没有可读取的报告。',
  internal_error: '服务暂时无法完成请求。',
}
const statuses: Record<string, { label: string; color: string }> = {
  PENDING: { label: '等待执行', color: 'gold' }, RUNNING: { label: '运行中', color: 'gold' },
  COMPLETED: { label: '已完成', color: 'green' }, FAILED: { label: '失败', color: 'red' },
  INTERRUPTED: { label: '已中断', color: 'red' },
}
const phases: Record<string, string> = {
  IDLE: '尚未提交', STATUS_LOADING: '正在读取状态', REPORT_LOADING: '正在读取报告',
  STATUS_ERROR: '状态读取遇到问题', REPORT_ERROR: '报告读取遇到问题',
  UNKNOWN_RUN: '研究不存在或不可访问', UNAVAILABLE: '服务暂不可用',
}
const dependencyLabels = { calendar_cffex: '中金所日历', calendar_sse: '上交所日历', futures: '期货日线', index: '指数日线' }
const dependencyStates = { complete: '已就绪', needs_fetch: '不完整', unknown: '未知', operation_error: '检查失败', contract_error: '检查异常' }

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
  const status = statuses[research.run?.status ?? '']
  const retryReport = research.phase === 'REPORT_ERROR' || research.errorRead === 'report'

  const parameters = <>
    <Form form={form} initialValues={{ end_date: dayjs(shanghaiDate()) }} layout="vertical" onValuesChange={(_, next) => setValues(next)} onKeyDown={event => {
      // Enter commits a date/selection; only the explicit button submits a non-idempotent Run.
      if (event.key === 'Enter' && event.target instanceof HTMLInputElement) event.preventDefault()
    }} onFinish={() => { if (query && !research.submitting) void research.submit(query) }}>
      <Flex gap="middle" wrap align="end">
        <Form.Item label="品种" name="product_code" rules={[{ required: true, message: '请选择品种' }]}><Select aria-label="品种" options={products.map(value => ({ value, label: value }))} placeholder="选择品种" style={{ width: 140 }} /></Form.Item>
        <Form.Item label="开始日期" name="start_date" rules={[{ required: true, message: '请选择开始日期' }]}><DatePicker aria-label="开始日期" format="YYYY-MM-DD" placeholder="YYYY-MM-DD" /></Form.Item>
        <Form.Item label="结束日期" name="end_date" dependencies={['start_date']} rules={[{ required: true, message: '请选择结束日期' }, ({ getFieldValue }) => ({ validator(_, value) { const start = getFieldValue('start_date'); return !start || !value || !start.isAfter(value, 'day') ? Promise.resolve() : Promise.reject(new Error('结束日期不能早于开始日期')) } })]}><DatePicker aria-label="结束日期" format="YYYY-MM-DD" placeholder="YYYY-MM-DD" /></Form.Item>
        <Form.Item><Button icon={<PlayCircleOutlined aria-hidden="true" />} type="primary" htmlType="button" onClick={() => form.submit()} disabled={!query || research.submitting} loading={research.submitting}>生成研究</Button></Form.Item>
      </Flex>
    </Form>
    <Flex vertical gap="small">
      <Typography.Title level={5}>数据准备状态</Typography.Title>
      <Flex wrap gap="small" align="center">
        <Tag color={preflight.result?.submission === 'allowed' ? 'green' : 'default'}>{preflight.checking ? '检查中' : preflight.error ? '检查失败' : !preflight.result ? '未知' : preflight.result.submission === 'allowed' ? '已就绪' : preflight.result.dependencies.some(item => ['operation_error', 'contract_error'].includes(item.state)) ? '检查失败' : preflight.result.dependencies.some(item => item.state === 'unknown') ? '未知' : '不完整'}</Tag>
        <Button icon={<ReloadOutlined aria-hidden="true" />} onClick={preflight.refresh} disabled={!query || preflight.checking}>重新检查</Button>
      </Flex>
      {preflight.error && <Alert type="warning" title="数据检查失败，可重试" />}
      {preflight.result && <>
        {preflight.result.submission !== 'allowed' && <Typography.Text type="secondary">{preflight.result.dependencies.some(item => ['operation_error', 'contract_error'].includes(item.state)) ? '数据操作或契约检查异常，可重新检查或联系维护者。' : preflight.result.today_gate === 'not_ready' ? '当日缓存不完整' : preflight.result.today_gate === 'unknown' ? '当日数据准备情况未知，可重新检查。' : '正式执行可能需要获取缺失数据'}</Typography.Text>}
        <Descriptions size="small" column={1} items={preflight.result.dependencies.map(item => ({
          key: `${item.scope}-${item.dependency}`,
          label: `${item.scope === 'today' ? '当日' : '整段'} / ${dependencyLabels[item.dependency]}`,
          children: <Flex wrap gap="small" align="center"><Tag>{dependencyStates[item.state]}</Tag>
            {item.coverage && <Typography.Text>· 已缓存 {item.coverage.successful_units} / {item.coverage.requested_units} {item.dependency.startsWith('calendar_') ? '个自然日目标' : item.dependency === 'futures' ? '个品种×日期目标' : '个指数×日期目标'}</Typography.Text>}
          </Flex>,
        }))} />
        <Collapse items={[{ key: 'assessment', label: '预检详情', children: <Typography.Text>submission: {preflight.result.submission} · today_gate: {preflight.result.today_gate}</Typography.Text> }]} />
      </>}
    </Flex>
    {research.submitting && <Alert showIcon type="info" title="正在提交 · SUBMITTING" description="等待服务器确认 Run；已有结果仍可阅读。" />}
    {research.feedback && <Alert showIcon type="warning"
      title={research.feedback.kind === 'unavailable' ? '研究提交未确认 · UNAVAILABLE' : messages[research.feedback.kind] ?? '提交未被确认。'}
      description={research.feedback.kind === 'unavailable' ? messages.unavailable : research.feedback.kind === 'invalid_request' ? research.feedback.detail : undefined} />}
  </>

  const run = <>
    <Flex gap="middle" align="center" wrap>
      <Tag color={status?.color ?? 'default'}>{status?.label ?? '未知'}</Tag>
      {phases[research.phase] && <Typography.Text>{phases[research.phase]}</Typography.Text>}
      <Typography.Text>Started: {formatBeijingTime(research.run && 'started_at' in research.run ? research.run.started_at : undefined)}</Typography.Text>
      <Typography.Text>Finished: {formatBeijingTime(research.run && 'finished_at' in research.run ? research.run.finished_at : undefined)}</Typography.Text>
    </Flex>
    {(research.run || research.id) && <Typography.Text type="secondary" style={{ overflowWrap: 'anywhere' }}>Run ID: <Typography.Text copyable>{research.run?.run_id ?? research.id}</Typography.Text></Typography.Text>}
    <Collapse items={[{ key: 'run-details', label: '运行详情', children: <Descriptions size="small" column={1} items={[
      { key: 'created', label: 'Created', children: formatBeijingTime(research.run?.created_at) },
      { key: 'status', label: 'Backend Status', children: research.run?.status ?? '—' },
      { key: 'phase', label: 'Phase', children: research.phase },
      ...(research.run && 'failure' in research.run && research.run.failure ? Object.entries(research.run.failure).map(([key, value]) => ({ key, label: key, children: value ?? '—' })) : []),
    ]} /> }]} />
    {research.phase === 'IDLE' && <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选择品种和起止日期，点击「生成研究」开始。" />}
    {research.phase === 'UNKNOWN_RUN' && <Alert showIcon type="warning" title="研究不存在或不可访问" description="请核对 Run 链接，或显式提交新的研究。" />}
    {research.error && research.phase !== 'UNKNOWN_RUN' && <Alert showIcon type="error"
      title={retryReport ? '报告读取失败' : '状态读取失败'}
      description={research.error.kind === 'network' ? '网络读取失败，请手动重试；不会创建新 Run。' : research.error.kind === 'invalid_response' ? '读取响应无法验证，请手动重试。' : messages[research.error.kind] ?? '读取失败，请手动重试。'} />}
    {['STATUS_ERROR', 'REPORT_ERROR', 'UNAVAILABLE'].includes(research.phase) && <Flex><Button icon={<ReloadOutlined aria-hidden="true" />} disabled={research.submitting} onClick={() => research.retry(retryReport)}>{retryReport ? '重新读取报告' : '重新读取状态'}</Button></Flex>}
    {research.run && ['FAILED', 'INTERRUPTED'].includes(research.phase) && <Flex vertical gap="small">
      <Alert showIcon type="error" title={research.phase === 'INTERRUPTED' ? '研究执行已中断' : '研究执行失败'} description={'failure' in research.run && research.run.failure ? research.run.failure.reason : '未生成研究报告，请检查服务后显式重试。'} />
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
