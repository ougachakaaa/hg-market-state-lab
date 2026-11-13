import { Alert, Button, Card, DatePicker, Descriptions, Flex, Form, Select, Spin, Tag, Typography } from 'antd'
import type { Dayjs } from 'dayjs'
import { products, strategies, type RunRequest } from '../api/backtesting'
import { useBacktesting } from '../hooks/useBacktesting'
import { usePreflight } from '../hooks/usePreflight'
import { dependencyLabels, errorMessage, readinessPresentation } from '../model/presentation'
import { Result } from '../components/Result'
import { Failure } from '../components/Failure'

type Fields = { product?: RunRequest['product_code']; start?: Dayjs; end?: Dayjs; strategy?: RunRequest['strategy_profile'] }
export default function BacktestingPage() {
  const [form] = Form.useForm<Fields>()
  const values = Form.useWatch([], form) as Fields | undefined
  const start = values?.start?.format('YYYY-MM-DD'); const end = values?.end?.format('YYYY-MM-DD')
  const valid = !!values?.product && !!values?.strategy && !!values?.start?.isValid() && !!values?.end?.isValid() && !!start && !!end && start <= end
  const query: RunRequest | undefined = valid ? { product_code: values!.product!, start_date: start!, end_date: end!, strategy_profile: values!.strategy! } : undefined
  const readiness = usePreflight(query)
  const run = useBacktesting()
  return <Flex vertical gap="large">
    <header><Typography.Title level={1} style={{ margin: 0, fontSize: 24 }}>期货展期做多回测</Typography.Title>
      <Typography.Paragraph type="secondary">Futures Roll Long · 单产品、单策略的理想收盘价历史回测，比较策略毛收益与指数价格基准。</Typography.Paragraph></header>
    <Card title="回测参数">
      <Form form={form} layout="vertical" onSubmitCapture={event => event.preventDefault()}>
        <Flex wrap gap="middle">
          <Form.Item name="product" label="产品" style={{ flex: '1 1 180px' }}><Select placeholder="选择产品" options={products.map(value => ({ value, label: value }))} /></Form.Item>
          <Form.Item name="start" label="开始日期" style={{ flex: '1 1 180px' }}><DatePicker placeholder="YYYY-MM-DD" format="YYYY-MM-DD" style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="end" label="结束日期" style={{ flex: '1 1 180px' }}><DatePicker placeholder="YYYY-MM-DD" format="YYYY-MM-DD" style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="strategy" label="策略" style={{ flex: '1 1 240px' }}><Select placeholder="选择策略" options={strategies.map(value => ({ value, label: value }))} /></Form.Item>
        </Flex>
        {start && end && start > end && <Alert type="warning" title="开始日期不能晚于结束日期。" />}
        <Flex gap="middle" wrap><Button type="primary" htmlType="button" disabled={!valid || run.submitting} loading={run.submitting} onClick={() => { if (query) void run.submit(query) }}>开始回测</Button>
          <Button htmlType="button" disabled={!query} onClick={readiness.refresh}>重新检查缓存</Button></Flex>
      </Form>
      <Typography.Paragraph type="secondary">重新检查缓存仅检查本地缓存，不获取或下载数据。</Typography.Paragraph>
      {run.submitting && <Typography.Paragraph role="status">SUBMITTING · 正在提交，请勿重复操作。</Typography.Paragraph>}
      {run.feedback && <Alert type="warning" title={errorMessage(run.feedback.kind, true)} />}
    </Card>
    <Card title="数据准备状态">
      <Typography.Paragraph type="secondary">这里显示本地行情缓存的准备情况。缓存缺失时，点击「开始回测」将尝试自动获取行情；数据获取需要后端已正确配置 Tushare。</Typography.Paragraph>
      {!query && <Typography.Text>请完整选择产品、日期和策略。</Typography.Text>}
      {readiness.checking && <Flex align="center" gap="small"><Spin size="small" /><Typography.Text>正在检查本地缓存…</Typography.Text></Flex>}
      {readiness.error && <Alert type="warning" title={`数据检查失败：${errorMessage(readiness.error.kind)}`} />}
      {readiness.result && <><Tag color={readiness.result.ready ? 'green' : 'orange'}>{readiness.result.ready ? '本地缓存已就绪' : '本地缓存尚未就绪'}</Tag>
        <Descriptions column={1} items={(['calendar_cffex', 'futures', 'index'] as const).map(key => {
          const item = readiness.result![key]
          const display = readinessPresentation(item)
          return { key, label: dependencyLabels[key], children: <>
            <Tag>{display.label}</Tag>{display.description}
            {display.coverage && <Typography.Paragraph>{display.coverage}</Typography.Paragraph>}
          </> }
        })} /></>}
    </Card>
    <Card title="当前 Run 状态">
      <Typography.Paragraph role="status">{run.phase === 'IDLE' ? '尚未提交回测。' : run.phase}</Typography.Paragraph>
      {run.id && <Typography.Paragraph style={{ overflowWrap: 'anywhere' }}>Run ID: {run.id}</Typography.Paragraph>}
      {run.run && <Typography.Paragraph>后端状态：{run.run.status}</Typography.Paragraph>}
      {run.run && <Descriptions column={{ xs: 1, md: 2 }} items={[
        { key: 'request', label: '已接受的请求', children: `${run.run.request.product_code} · ${run.run.request.start_date} → ${run.run.request.end_date} · ${run.run.request.strategy_profile}` },
        { key: 'created', label: 'Created', children: run.run.created_at },
        ...('started_at' in run.run ? [{ key: 'started', label: 'Started', children: run.run.started_at ?? '—' }, { key: 'finished', label: 'Finished', children: run.run.finished_at ?? '—' }] : []),
      ]} />}
      {['FAILED', 'INTERRUPTED'].includes(run.phase) && <Failure status={run.phase} failure={run.run && 'failure' in run.run ? run.run.failure : undefined} runId={run.id} />}
      {run.error && <Alert type="error" title={errorMessage(run.error.kind)} action={<Button onClick={() => run.retry(run.errorRead === 'result')}>重新读取{run.errorRead === 'result' ? '结果' : '状态'}</Button>} />}
    </Card>
    {run.result && !['FAILED', 'INTERRUPTED'].includes(run.phase) && <Result key={run.result.run_id} data={run.result.data} />}
  </Flex>
}
