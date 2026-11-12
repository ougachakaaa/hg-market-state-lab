// Build-time verification only; no feature runtime or business semantics.
import { fileURLToPath } from 'node:url'
import { isAbsolute, relative } from 'node:path'
import ts from 'typescript'
import type { Plugin } from 'vite'

const web = fileURLToPath(new URL('../', import.meta.url))
const local = (id: string) => relative(web, id.split('?')[0]).replaceAll('\\', '/')
const project = (id: string) => isAbsolute(id) && !id.includes('/node_modules/')
export function staticPresentationIsolation(feature: string, forbidden: RegExp, compositionModules: readonly string[] = []): Plugin {
  const composition = new Set(compositionModules)
  return {
    name: `static-${feature}-isolation`, enforce: 'pre',
    transform(code, id) {
      if (!project(id) || !/\.[cm]?[jt]sx?$/.test(id)) return
      const source = ts.createSourceFile(id, code, ts.ScriptTarget.Latest, true)
      const visit = (node: ts.Node) => {
        if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword &&
          (node.arguments.length !== 1 || !ts.isStringLiteralLike(node.arguments[0]))) {
          this.error(`Unresolved static presentation import: ${local(id)}`)
        }
        ts.forEachChild(node, visit)
      }
      visit(source)
    },
    generateBundle() {
      const modules = [...this.getModuleIds()].filter(project)
      const allowed = (path: string) =>
        path === 'src/app/AppUiProvider.tsx' || path === 'src/index.css' ||
        composition.has(path) ||
        /^src\/shared\/(ui|charts|format|clipboard|csv|download)\//.test(path) ||
        (path.startsWith(`src/features/${feature}/`) &&
          !forbidden.test(path))
      for (const id of modules) {
        const info = this.getModuleInfo(id)!
        for (const dependency of [id, ...info.importedIds, ...info.dynamicallyImportedIds]) {
          if (project(dependency) && !allowed(local(dependency))) {
            this.error(`Forbidden static presentation dependency: ${local(dependency)}`)
          }
        }
      }
      this.emitFile({ type: 'asset', fileName: 'presentation-dependencies.json', source: JSON.stringify(modules.map(local), null, 2) })
    },
  }
}
