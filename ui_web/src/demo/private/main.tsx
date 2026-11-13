import { createRoot } from 'react-dom/client'
import { Alert } from 'antd'
import AppUiProvider from '../../app/AppUiProvider'
import { admitPrivateEnvelope } from './admission'
import { PrivateWorkspace } from './PrivateWorkspace'
import envelope from 'virtual:private-examples'
import '../../index.css'

const root = createRoot(document.getElementById('root')!)
admitPrivateEnvelope(envelope).then(data => root.render(<PrivateWorkspace data={data} />)).catch(() => {
  root.render(<AppUiProvider><Alert type="error" showIcon title="Static Error：私有 Example 校验失败" description="身份、来源、摘要或正式 Result 契约无效，已拒绝展示。无旧结果、Synthetic 或在线服务回退。" /></AppUiProvider>)
})
