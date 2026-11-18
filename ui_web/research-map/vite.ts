import { normalizePath, type Plugin } from 'vite'
import { mapPath, schemaPath, validateResearchMap } from './validate.ts'

export function researchMapValidation(): Plugin {
  return {
    name: 'strategy-research-map',
    enforce: 'pre',
    transform(source, id) {
      if (normalizePath(id.split('?')[0]) !== normalizePath(mapPath)) return
      this.addWatchFile(schemaPath)
      try {
        validateResearchMap(JSON.parse(source))
      } catch (error) {
        this.error(`Invalid Research Map (research-map/map.json): ${error instanceof Error ? error.message : String(error)}`)
      }
    },
  }
}
