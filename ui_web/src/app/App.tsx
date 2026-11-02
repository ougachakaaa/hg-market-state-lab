import { Alert, Button, Flex, Layout, Spin, Typography, theme } from 'antd'
import { useState } from 'react'
import OptionChainPage from '../features/mo_option_chain'
import PremiumPlanePage from '../features/mo_option_premium'
import ResearchExplorerPage from '../features/research_explorer/page/ResearchExplorerPage'
import AppUiProvider from './AppUiProvider'
import AuthForm from './auth/AuthForm'
import { useAuthentication } from './auth/useAuthentication'
import type { CurrentUser } from './auth/api/auth'

type Feature = 'option-chain' | 'premium-plane' | 'research'

function ApplicationShell({ user, signOut }: { user: CurrentUser; signOut: () => Promise<void> }) {
  const [feature, setFeature] = useState<Feature>('option-chain')
  const { token } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Header style={{ height: 'auto', padding: `${token.paddingSM}px ${token.paddingLG}px 0`, background: token.colorBgLayout }}>
        <Flex component="nav" gap="small" wrap aria-label="产品功能导航"
          style={{ width: '100%', maxWidth: 1400, margin: '0 auto' }}>
          <Button type={feature === 'option-chain' ? 'primary' : 'default'}
            aria-pressed={feature === 'option-chain'} onClick={() => setFeature('option-chain')}>
            MO Option Chain
          </Button>
          <Button type={feature === 'premium-plane' ? 'primary' : 'default'}
            aria-pressed={feature === 'premium-plane'} onClick={() => setFeature('premium-plane')}>
            MO Premium Plane
          </Button>
          <Button type={feature === 'research' ? 'primary' : 'default'}
            aria-pressed={feature === 'research'} onClick={() => setFeature('research')}>
            Research Explorer
          </Button>
          <Typography.Text>{user.username}</Typography.Text>
          <Button onClick={() => void signOut()}>Logout</Button>
        </Flex>
      </Layout.Header>
      <Layout.Content style={{ width: '100%', maxWidth: 1400, margin: '0 auto', padding: token.paddingLG, boxSizing: 'border-box' }}>
        {feature === 'option-chain' ? <OptionChainPage /> : feature === 'premium-plane' ? <PremiumPlanePage /> : <ResearchExplorerPage />}
      </Layout.Content>
    </Layout>
  )
}

function AuthenticationGate() {
  const { state, check, signIn, signOut } = useAuthentication()
  if (state.status === 'authenticated') return <ApplicationShell user={state.user} signOut={signOut} />
  if (state.status === 'anonymous') return <AuthForm signIn={signIn} />
  return <Flex vertical align="center" justify="center" gap="middle" style={{ minHeight: '100vh', padding: 24 }}>
    {state.status === 'checking' && <><Spin /><Typography.Text>正在检查登录状态…</Typography.Text></>}
    {state.status === 'error' && <><Alert type="error" title={state.message} /><Button onClick={() => void check()}>重试登录状态检查</Button></>}
    {state.status === 'logging_out' && (state.pending ? <><Spin /><Typography.Text>正在退出…</Typography.Text></>
      : <><Alert type="error" title={state.message} /><Button onClick={() => void signOut()}>重试退出</Button></>)}
  </Flex>
}

function App() {
  return <AppUiProvider><AuthenticationGate /></AppUiProvider>
}

export default App
