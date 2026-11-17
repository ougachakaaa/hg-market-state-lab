import { createRoot } from 'react-dom/client'
import loaders from 'virtual:demo-data'
import '../../src/index.css'
import { StaticWorkspace } from './StaticWorkspace'
createRoot(document.getElementById('root')!).render(<StaticWorkspace loaders={loaders} header="Static Demo" notice="正式 FastAPI HTTP 结果的静态展示。构建前已通过结构与完整性校验。静态只读，不进行实时金融计算。数据不保证准确，仅供项目功能展示，不构成投资建议。" />)
