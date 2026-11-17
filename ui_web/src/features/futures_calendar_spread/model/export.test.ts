import { expect, it } from 'vitest'
import { validateResult } from '../api/validateResult'
import { serializeJson } from '../../../shared/clipboard/text'
import { contextJson, csvHeader, exportFilename, resultCsv } from './export'
import daily from '../testing/daily.json'
import closed from '../testing/closed.json'
import empty from '../testing/empty.json'
import excluded from '../testing/excluded.json'
import { referenceStates, withReference } from '../testing/reference'

const expectedHeader = 'case,definition_version,product_code,trade_date,day_status,day_reason,near_slot,far_slot,near_contract_code,near_close,near_delist_date,far_contract_code,far_close,far_delist_date,delta_days,near_dte_days,expiry_stage,signed_spread,annualized_point_spread,annualized_spread_ratio,outcome,reason,underlying_index_present,underlying_index_code,underlying_index_trade_date,underlying_index_close,underlying_index_availability,underlying_index_reason_code,underlying_index_failure_category'
it.each([daily, closed, empty, excluded, withReference()])('preserves full Raw and Context facts and omission', input => {
  const r = validateResult(input)
  const before = JSON.stringify(r)
  expect(JSON.parse(serializeJson(r))).toEqual(r)
  const context = JSON.parse(contextJson(r))
  expect(context.format_version).toBe('daily-data-context-v1')
  expect(context.metadata.product).toBe('Futures Calendar Spread')
  expect(context.metadata.response_identity).toEqual({ case: r.case, definition_version: r.definition_version, operation: r.request.operation, product_code: r.request.product_code, trade_date: r.request.trade_date })
  expect(context.data).toEqual(r)
  expect(Object.hasOwn(context.data, 'underlying_index')).toBe(Object.hasOwn(r, 'underlying_index'))
  expect(JSON.stringify(r)).toBe(before)
})
it('exports the complete ordered header, six rows, original precision, null and zero', () => {
  expect(csvHeader.join(',')).toBe(expectedHeader)
  const csv = resultCsv(validateResult(daily))
  expect(csv.startsWith('\uFEFF' + expectedHeader + '\r\n')).toBe(true)
  const lines = csv.slice(1).trimEnd().split('\r\n')
  expect(lines).toHaveLength(7)
  lines.slice(1).forEach((line, i) => {
    const cells = line.split(',')
    expect(cells).toHaveLength(29)
    expect(cells.slice(6, 8)).toEqual([daily.day.observations[i].near_slot, daily.day.observations[i].far_slot])
    expect(cells.slice(22)).toEqual(['false', 'null', 'null', 'null', 'null', 'null', 'null'])
    expect(cells[19]).toBe(String(daily.day.observations[i].metrics.annualized_spread_ratio.value))
  })
  expect(lines[3].split(',').slice(17, 20)).toEqual(['0', '0', '0'])
  expect(resultCsv(validateResult(closed))).toBe('\uFEFF' + expectedHeader + '\r\n')
  expect(resultCsv(validateResult(empty)).split('\r\n')[1].split(',').slice(8, 20)).toEqual(Array(12).fill('null'))
  expect(resultCsv(validateResult(excluded)).split('\r\n')[1].split(',')[9]).toBe('0')
})
it.each(referenceStates)('preserves provided reference %s/%s/%s', (...state) => {
  const r = withReference(daily, state)
  expect(resultCsv(r).split('\r\n')[1].split(',').slice(22)).toEqual(['true', '000852.SH', daily.request.trade_date, state[0] === 'available' ? '0' : 'null', state[0], String(state[1]), String(state[2])])
})
it('uses shared formula protection, quoting and safe response filenames', () => {
  const r = validateResult(daily); r.day.observations[0].near!.contract_code = '=SUM(1,2)"\r\n'
  const csv = resultCsv(r)
  expect(csv).toContain('"\'=SUM(1,2)""\r\n"')
  expect(csv.endsWith('\r\n')).toBe(true)
  expect(exportFilename(r)).toBe('futures-calendar-spread_IM_2024-10-18.csv')
  expect(exportFilename(r, true)).toBe('futures-calendar-spread_IM_2024-10-18_context.json')
  r.request.trade_date = '../unsafe:date'
  expect(exportFilename(r)).toBe('futures-calendar-spread_IM_.._unsafe_date.csv')
})
