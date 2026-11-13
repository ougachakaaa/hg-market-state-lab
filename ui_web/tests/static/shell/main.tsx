import { createRoot } from 'react-dom/client'
import '../../../src/index.css'
import StaticShellHarness from './StaticShellHarness'

createRoot(document.getElementById('root')!).render(<StaticShellHarness />)
