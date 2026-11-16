import { expect, it } from 'vitest'
import h30 from '../testing/history30.json'
import { validateResult } from '../api/validateResult'
import { historicalView, sessionDates } from './charts'
import { viewV2ToPlotly } from '../../../shared/visualization/figureV2'
import { validateViewV2 } from '../../../shared/visualization/contractV2'
it('keeps backend dates/value/contract identity across both axis projections', () => {
  const r = validateResult(h30); const original = JSON.stringify(r)
  const view = historicalView(r, 0); validateViewV2(view)
  const domain = sessionDates(r)
  const trading = viewV2ToPlotly(view, { ordinalDates: domain })
  const calendar = viewV2ToPlotly(view)
  expect(trading.layout.xaxis!.type).toBe('linear')
  expect(calendar.layout.xaxis!.type).toBe('date')
  expect((trading.data[0] as any).x).toEqual(view.layers[0].layer.data.map(m => domain.indexOf(m.x)))
  expect((calendar.data[0] as any).x).toEqual(view.layers[0].layer.data.map(m => m.x))
  expect((trading.data[0] as any).y).toEqual(r.pairs[0].samples.map(s => s.metric.value))
  expect(trading.data.map((d: any) => d.y)).toEqual(calendar.data.map((d: any) => d.y))
  expect(view.layers[1].layer.data[0].x).toBe(r.request.evaluation_date)
  expect(view.layers[0].layer.data[0].details[0].value).toBe(r.pairs[0].samples[0].near.contract_code)
  expect(JSON.stringify(r)).toBe(original)
})
it('does not bridge missing sessions or real contract switches, and excludes unavailable current marks', () => {
  const r = structuredClone(validateResult(h30))
  r.pairs[0].samples.splice(1, 1)
  r.pairs[0].samples[2].near.contract_code = 'another-real-contract'
  const view = historicalView(r, 0)
  validateViewV2(view)
  expect(view.layers[0].layer.data[1].y).toBeNull()
  expect(view.layers[0].layer.data[0].segment_id).not.toBe(view.layers[0].layer.data[2].segment_id)
  expect(view.layers[0].layer.data[2].segment_id).not.toBe(view.layers[0].layer.data[3].segment_id)
  r.current_day.observations[0].outcome = 'excluded'
  expect(historicalView(r, 0).layers[1].layer.data).toEqual([])
})
