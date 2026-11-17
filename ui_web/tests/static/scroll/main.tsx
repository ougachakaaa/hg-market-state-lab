import { createRoot } from 'react-dom/client'
import ApplicationShell from '../../../src/app/ApplicationShell'
import AppUiProvider from '../../../src/app/AppUiProvider'
import { useWorkspaceRoute } from '../../../src/app/routes'
import { useHashRoute, staticHref } from '../../../demo/runtime/hashRoutes'
import '../../../src/index.css'

const mode = new URL(location.href).searchParams.get('mode') === 'static' ? 'static' : 'production'
function Harness() {
  const { path, navigate } = (mode === 'static' ? useHashRoute : useWorkspaceRoute)()
  return <AppUiProvider><ApplicationShell mode={mode} path={path} navigate={navigate}
    href={mode === 'static' ? staticHref : path => path} header={<span>Scroll acceptance · {mode}</span>}>
    <h1>{path}</h1>
    <button onClick={() => document.getElementById('chapter')?.scrollIntoView({ block: 'start' })}>章节跳转</button>
    <div data-testid="horizontal" style={{ overflowX: 'auto', maxWidth: '100%' }}><div style={{ width: 2000 }}>Wide feature content</div></div>
    <div style={{ height: 2200 }}>Long Workspace content</div>
    <h2 id="chapter">目标章节</h2>
    <div style={{ height: 1000 }}>End</div>
  </ApplicationShell></AppUiProvider>
}
createRoot(document.getElementById('root')!).render(<Harness />)
