import { fileURLToPath } from 'node:url'
import { isAbsolute, relative } from 'node:path'
import ts from 'typescript'
import { mergeConfig, type Plugin } from 'vite'
import { workspaceRoutes, workspaceAreas } from './src/app/routeInventory.ts'
import demoConfig from './vite.demo.config.ts'

const web = fileURLToPath(new URL('.', import.meta.url))
const allowed = new Set([
  'src/demo/shell/index.html', 'src/demo/shell/main.tsx',
  'src/demo/shell/StaticShellHarness.tsx', 'src/demo/shell/hashRoutes.ts',
  'src/app/ApplicationShell.tsx', 'src/app/AppUiProvider.tsx',
  'src/app/DailyDataLanding.tsx', 'src/app/routeInventory.ts',
  'src/shared/ui/theme.ts', 'src/index.css',
])
const projectPath = (id: string) => relative(web, id.split('?')[0]).replaceAll('\\', '/')
const isProject = (id: string) => isAbsolute(id) && !id.includes('/node_modules/')

// Inspect loaded modules, including imports later removed by tree shaking, and
// resolved dynamic edges. Fail closed for dynamic imports the bundler cannot resolve.
function shellIsolation(): Plugin {
  return {
    name: 'd1-shell-isolation',
    enforce: 'pre',
    transform(code, id) {
      if (!isProject(id) || !/\.[cm]?[jt]sx?$/.test(id)) return
      const source = ts.createSourceFile(id, code, ts.ScriptTarget.Latest, true)
      const visit = (node: ts.Node) => {
        if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword &&
          (node.arguments.length !== 1 || !ts.isStringLiteralLike(node.arguments[0]))) {
          this.error(`Unresolved dynamic import in static shell: ${projectPath(id)}`)
        }
        ts.forEachChild(node, visit)
      }
      visit(source)
    },
    generateBundle() {
      const modules = [...this.getModuleIds()].map(id => {
        const info = this.getModuleInfo(id)!
        return { id, imports: info.importedIds, dynamicImports: info.dynamicallyImportedIds }
      })
      for (const { id, imports, dynamicImports } of modules) {
        for (const dependency of [id, ...imports, ...dynamicImports]) {
          if (isProject(dependency) && !allowed.has(projectPath(dependency))) {
            this.error(`Forbidden static shell runtime dependency: ${projectPath(dependency)}`)
          }
        }
      }
      this.emitFile({ type: 'asset', fileName: 'shell-routes.json', source: JSON.stringify({ routes: workspaceRoutes, areas: workspaceAreas }) })
      this.emitFile({ type: 'asset', fileName: 'shell-dependencies.json', source: JSON.stringify({
        projectModules: modules.filter(m => isProject(m.id)).map(m => ({
          id: projectPath(m.id),
          imports: m.imports.map(projectPath), dynamicImports: m.dynamicImports.map(projectPath),
        })),
        moduleCount: modules.length,
      }, null, 2) })
    },
  }
}

// Verification only; V1 release entry and dist-demo are untouched.
export default mergeConfig(demoConfig, {
  root: fileURLToPath(new URL('./src/demo/shell', import.meta.url)),
  plugins: [shellIsolation()],
  build: { outDir: fileURLToPath(new URL('./dist-demo-shell', import.meta.url)) },
})
