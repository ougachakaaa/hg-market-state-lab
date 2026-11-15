import { createRoot } from 'react-dom/client'
import bundles from 'virtual:demo-data'
import '../../src/index.css'
import { StaticWorkspace } from './StaticWorkspace'
import { adaptBundles, disclose } from './dataAdapter'
const root = createRoot(document.getElementById('root')!)
try {
  const data = adaptBundles(bundles)
  root.render(<StaticWorkspace data={data} disclose={disclose} header="Static Demo" notice="正式 FastAPI HTTP 结果的静态展示。构建前已通过结构与完整性校验。静态只读，不进行实时金融计算。数据不保证准确，仅供项目功能展示，不构成投资建议。" />)
} catch {
  root.render(<p role="alert">静态数据无效，无法展示结果。</p>)
}
