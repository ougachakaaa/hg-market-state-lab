import { relative, isAbsolute } from 'node:path'
import { fileURLToPath } from 'node:url'
const web = fileURLToPath(new URL('../', import.meta.url))
export function staticRuntimeIsolation(runtime = 'static') {
  return {
    name: 'static-runtime-isolation',
    generateBundle() {
      const ids = [...this.getModuleIds()].filter(id => isAbsolute(id) && !id.includes('/node_modules/'))
      const paths = ids.map(id => relative(web, id.split('?')[0]).replaceAll('\\', '/'))
      for (const path of paths) {
        const allowed = (path.startsWith(`src/demo/${runtime}/`) || /^src\/demo\/(static|shell\/hashRoutes)/.test(path)) ||
          /^src\/app\/(ApplicationShell|AppUiProvider|DailyDataLanding|routeInventory)\./.test(path) ||
          path === 'src/index.css' || /^src\/shared\/(ui|charts|format|clipboard|csv|download|visualization)\//.test(path) ||
          /^src\/features\/(mo_option_chain|mo_option_premium|research_catalog|research_explorer|futures_basis_research|backtesting)\//.test(path)
        const forbidden = /\/testing\/|\/hooks\/use(?!OptionChainPresentation|PremiumPresentation)|\/api\/(moOptionChain|moOptionPremium|catalog|research|backtesting|futuresBasis)\.(ts|tsx)$|\/page\/\w+Page\.tsx$|shared\/http|app\/auth/.test(path)
        if (!allowed || forbidden) this.error(`Forbidden static dependency: ${path}`)
      }
      this.emitFile({ type: 'asset', fileName: 'presentation-dependencies.json', source: JSON.stringify(paths.sort(), null, 2) })
    },
  }
}
