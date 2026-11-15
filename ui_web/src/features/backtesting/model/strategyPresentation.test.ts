import { expect, it } from 'vitest'
import fixture from '../api/result.fixture.json'
import { strategyExplanation, strategyLabels, strategyView } from './strategyPresentation'
import type { ViewV2 } from '../../../shared/visualization/contractV2'

it('labels producer events without changing their identities, positions or source data', () => {
  const view = structuredClone(fixture.views.returns) as ViewV2
  const before = structuredClone(view)
  const display = strategyView(view)
  expect(display.events.map(({ id, x }) => ({ id, x }))).toEqual(view.events.map(({ id, x }) => ({ id, x })))
  expect(display.events[0].details.find(item => item.label === 'Profile')?.value).toBe(strategyLabels.expiry_to_M1_v1)
  expect(display.layers[0].layer.data.map(({ x, y }) => ({ x, y }))).toEqual(view.layers[0].layer.data.map(({ x, y }) => ({ x, y })))
  expect(view).toEqual(before)
})

it('explains both shared and selected rules without choosing an input default', () => {
  expect(strategyExplanation()).toContain('当天 M1 或 Q1')
  expect(strategyExplanation('expiry_to_M1_v1')).toContain('换入当天 M1')
  expect(strategyExplanation('expiry_to_Q1_v1')).toContain('换入当天 Q1')
  expect(strategyExplanation('expiry_to_Q1_v1')).toContain('首个 CFFEX 交易日买入 M1')
})
