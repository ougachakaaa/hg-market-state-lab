// Contract conformance only: execute the canonical frontend validator unchanged.
import { readFileSync } from 'node:fs'
import { describe, expect, it } from '../../ui_web/node_modules/vitest/dist/index.js'
import { validateViewV2 } from '../../ui_web/src/shared/visualization/contractV2'

const fixtures = JSON.parse(readFileSync(process.env.W2_V2_FIXTURE!, 'utf8'))
describe('Python W2 producer V2 fixtures', () => {
  for (const [name, view] of Object.entries(fixtures)) {
    it(`accepts ${name} without mutation`, () => {
      const before = JSON.stringify(view)
      validateViewV2(view)
      expect(JSON.stringify(view)).toBe(before)
    })
    it(`rejects extra fields on ${name}`, () => {
      expect(() => validateViewV2({ ...(view as object), business_pnl: 1 })).toThrow()
    })
  }
})
