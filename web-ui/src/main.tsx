import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './application.css'
import './features/mo_option_chain/index.css'
import './features/mo_option_premium/index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
