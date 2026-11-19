import { readFileSync } from 'node:fs'
import { normalizePath, type Plugin } from 'vite'
import { mapLocation, mapPath, schemaPath, validateResearchMap } from './validate.ts'

const moduleId = 'virtual:strategy-research-map'
const resolvedId = '\0' + moduleId
const files = [mapPath, schemaPath]

export function researchMapValidation(): Plugin {
  return {
    name: 'strategy-research-map',
    resolveId(id) {
      if (id === moduleId) return resolvedId
    },
    load(id) {
      if (id !== resolvedId) return
      for (const file of files) this.addWatchFile(file)
      try {
        const map = validateResearchMap(JSON.parse(readFileSync(mapPath, 'utf8')))
        return `export default ${JSON.stringify(map)}`
      } catch (error) {
        this.error(`Invalid Strategy Research Map (${mapLocation}): ${error instanceof Error ? error.message : String(error)}`)
      }
    },
    configureServer(server) {
      server.watcher.add(files)
    },
    hotUpdate({ file, timestamp }) {
      if (!files.some(path => normalizePath(path) === normalizePath(file))) return
      const module = this.environment.moduleGraph.getModuleById(resolvedId)
      if (module) this.environment.moduleGraph.invalidateModule(module, new Set(), timestamp, true)
      if (this.environment.name === 'client') this.environment.hot.send({ type: 'full-reload' })
      return []
    },
  }
}
