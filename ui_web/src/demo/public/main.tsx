import { createRoot } from 'react-dom/client'
import { Alert, Typography } from 'antd'
import AppUiProvider from '../../app/AppUiProvider'
import { StaticWorkspace } from '../static/StaticWorkspace'
import { admitPublicEnvelope, type PublicIdentity } from './admission'
import envelope from 'virtual:public-examples'
import '../../index.css'
const root = createRoot(document.getElementById('root')!)
root.render(<AppUiProvider><Alert type="info" title="静态 Example 正在校验" /></AppUiProvider>)
admitPublicEnvelope(envelope).then(data => root.render(<StaticWorkspace data={data}
  header="Market State Lab — Personal Research & Engineering Portfolio"
  disclose={identity => (identity as PublicIdentity).disclosure}
  notice={<Alert type="info" showIcon title="Historical Results · Static, Read-Only · 无需登录"
    description={<><Typography.Paragraph>本项目仅用于个人软件工程与金融研究方法展示。历史数据及研究结果不保证准确性、完整性或时效性，不构成投资建议。展示的回测结果不代表真实交易表现。</Typography.Paragraph><Typography.Paragraph>This project is a personal software engineering and financial research portfolio. Historical data and research results are provided for demonstration only, without warranties of accuracy, completeness or timeliness. Nothing constitutes investment advice. Backtested performance does not represent live trading results.</Typography.Paragraph><Typography.Link href="https://github.com/ougachakaaa/hg-market-state-lab">Source Code · AGPL-3.0</Typography.Link></>} />}
/>)).catch(() => root.render(<AppUiProvider><Alert type="error" title="Static Error：公共 Example 准入失败" description="结果、来源或许可校验失败；展示已停止。" /></AppUiProvider>))
