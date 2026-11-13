import { relative, isAbsolute } from 'node:path'
import { web } from './private_demo_boundary.mjs'
export function privateDemoIsolation() {
  return {
    name: 'private-demo-isolation',
    generateBundle() {
      const ids = [...this.getModuleIds()].filter(id => isAbsolute(id) && !id.includes('/node_modules/'))
      const paths = ids.map(id => relative(web, id.split('?')[0]).replaceAll('\\', '/'))
      for (const path of paths) {
        const allowed = /^src\/demo\/(private|shell\/hashRoutes)/.test(path) ||
          /^src\/app\/(ApplicationShell|AppUiProvider|DailyDataLanding|routeInventory)\./.test(path) ||
          path === 'src/index.css' || /^src\/shared\/(ui|charts|format|clipboard|csv|download|visualization)\//.test(path) ||
          /^src\/features\/(mo_option_chain|mo_option_premium|research_catalog|research_explorer|futures_basis_research|backtesting)\//.test(path)
        const forbidden = /\/testing\/|\/hooks\/use(?!OptionChainPresentation|PremiumPresentation)|\/api\/(moOptionChain|moOptionPremium|catalog|research|backtesting|futuresBasis)\.(ts|tsx)$|\/page\/\w+Page\.tsx$|shared\/http|app\/auth/.test(path)
        if (!allowed || forbidden) this.error(`Forbidden private static dependency: ${path}`)
      }
      this.emitFile({ type: 'asset', fileName: 'presentation-dependencies.json', source: JSON.stringify(paths.sort(), null, 2) })
    },
  }
}
