import { Component, type ReactNode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Alert, Button, ConfigProvider, Divider, Flex, Layout, Spin, Tag, Typography, theme } from 'antd'
import { GithubOutlined } from '@ant-design/icons'
import { applicationTheme } from '../../shared/ui/theme'
import { Report } from '../../features/futures_basis_research/report/Report'
import type { FuturesBasisDemoFixture } from './fixture'
import '../../shared/visualization/plotly.css'
import './demo.css'

const repository = 'https://github.com/ougachakaaa/hg-market-state-lab'
const source = `${repository}/tree/feat/github-pages-demo/ui_web/src/demo/futures_basis`

class ReportBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    return this.state.failed
      ? <Alert showIcon type="error" title="演示报告无法展示" description="报告未能通过展示检查。请刷新页面或查看 GitHub 中的演示源文件。" />
      : this.props.children
  }
}

export function Demo() {
  const { token } = theme.useToken()
  const [fixture, setFixture] = useState<FuturesBasisDemoFixture | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    let active = true
    // The WP2 export validates at import time; rejection remains visible in the shell.
    void import('./fixture').then(({ futuresBasisDemoFixture }) => {
      if (active) setFixture(futuresBasisDemoFixture)
    }, () => { if (active) setFailed(true) })
    return () => { active = false }
  }, [])

  return <Layout style={{ minHeight: '100vh' }}>
    <Flex component="header" vertical gap="small" style={{ padding: token.paddingLG, borderBottom: `1px solid ${token.colorBorderSecondary}` }}>
      <Flex justify="space-between" align="center" gap="middle" wrap>
        <Typography.Text strong>Market State Lab</Typography.Text>
        <Button icon={<GithubOutlined aria-hidden />} href={repository}>GitHub Repository</Button>
      </Flex>
      <Typography.Text type="secondary">Interactive Research Demo · 静态演示，无需后端或登录</Typography.Text>
    </Flex>
    <Flex vertical gap="large" style={{ position: 'sticky', top: 0, zIndex: 20, padding: `${token.paddingSM}px ${token.paddingLG}px`, background: token.colorBgElevated, borderBottom: `1px solid ${token.colorBorderSecondary}` }}>
      <Typography.Link href="#synthetic-disclosure" aria-label="查看合成演示数据声明">{fixture?.disclosure.label ?? 'Synthetic Demo'} / 合成演示数据 · 查看声明</Typography.Link>
    </Flex>
    <Layout.Content style={{ width: '100%', maxWidth: 1448, margin: '0 auto', padding: token.paddingLG, minWidth: 0 }}>
      <Flex vertical gap="large" style={{ minWidth: 0 }}>
        <section aria-labelledby="demo-title">
          <Tag>RESEARCH / 研究阅读体验</Tag>
          <Typography.Title id="demo-title" level={1}>股指期货历史基差研究</Typography.Title>
          <Typography.Paragraph>探索不同期限合约的历史基差、基差分布、期限结构与贴水持续区间，阅读 Evidence 与研究限制。</Typography.Paragraph>
          <Typography.Paragraph type="secondary">本案例使用 WP2 Synthetic Fixture。下方复用正式应用的报告阅读器；选择 Metric、Slot 或时间轴仅切换已有结果，图表支持缩放、平移、重置与悬停查看；窄屏可在图表区域横向滚动。</Typography.Paragraph>
        </section>
        <section id="synthetic-disclosure" aria-label="Synthetic Disclosure" style={{ scrollMarginTop: 80 }}>
          {fixture && <Alert showIcon type="warning" title={`${fixture.disclosure.label} / 合成演示数据`} description={<Flex vertical gap="small">
            <Typography.Text>{fixture.disclosure.notice}</Typography.Text>
            <Typography.Text>{fixture.disclosure.data_source}</Typography.Text>
            <Typography.Text>不是实时行情，不是未经说明的真实市场数据，不是实际交易绩效，不构成投资建议。</Typography.Text>
          </Flex>} />}
        </section>
        {failed ? <Alert showIcon type="error" title="演示数据无法加载或校验失败" description="未展示研究结果。请刷新页面；如仍失败，请查看 GitHub 中已提交的 Synthetic Fixture。" />
          : fixture ? <ReportBoundary><Report data={fixture.report} mode="demo" /></ReportBoundary>
            : <Flex align="center" gap="middle" role="status"><Spin /><Typography.Text>正在加载并校验静态演示数据…</Typography.Text></Flex>}
      </Flex>
    </Layout.Content>
    <Layout.Footer>
      <Divider />
      <Flex vertical gap="middle" style={{ maxWidth: 1400, margin: '0 auto' }}>
        <Flex gap="large" wrap>
          <Typography.Link href={source}>View Source on GitHub</Typography.Link>
          <Typography.Link href={`${repository}/blob/feat/github-pages-demo/README.md`}>README</Typography.Link>
          <Typography.Link href="#synthetic-disclosure">Synthetic 数据声明</Typography.Link>
        </Flex>
        <Typography.Text type="secondary">体验完整应用与研究执行需本地部署。安装与运行方式见 README；本页仅展示合成演示数据。</Typography.Text>
      </Flex>
    </Layout.Footer>
  </Layout>
}

createRoot(document.getElementById('root')!).render(
  <ConfigProvider componentSize="small" button={{ autoInsertSpace: false }} theme={applicationTheme}>
    <Demo />
  </ConfigProvider>,
)
