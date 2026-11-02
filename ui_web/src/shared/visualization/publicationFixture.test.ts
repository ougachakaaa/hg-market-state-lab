import { expect, it } from 'vitest'
import fixtures from '../../../../market_research/tests/fixtures/publication_visualization_v1.json'
import { validateChartView } from './contract'
import { chartViewToPlotly } from './figure'

it('accepts the shared Research publication V1 fixtures', () => {
  expect(fixtures).toHaveLength(3)
  for (const fixture of fixtures) {
    expect(() => validateChartView(fixture)).not.toThrow()
    expect(chartViewToPlotly(fixture).data).toHaveLength(1)
  }
})
