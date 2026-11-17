import spot from '../testing/daily_spot.json'
import { expect, it } from 'vitest'
import { validateResult } from '../api/validateResult'
import { serializeJson } from '../../../shared/clipboard/text'
import { contextJson, csvHeader, exportFilename, resultCsv } from './export'
import daily from '../testing/daily.json'
import closed from '../testing/closed.json'
import empty from '../testing/empty.json'
import excluded from '../testing/excluded.json'
import { referenceStates, withReference } from '../testing/reference'

const expectedHeader = 'case,definition_version,product_code,trade_date,day_status,day_reason,comparison_type,comparison_definition_version,slot_a,slot_b,instrument_a_type,instrument_a_code,instrument_a_close,instrument_a_delist_date,instrument_b_type,instrument_b_code,instrument_b_close,instrument_b_delist_date,delta_days,remaining_days,expiry_stage,signed_spread,annualized_point_spread,annualized_spread_ratio,outcome,reason,failure_category,underlying_index_present,underlying_index_code,underlying_index_trade_date,underlying_index_close,underlying_index_availability,underlying_index_reason_code,underlying_index_failure_category,futures_spot_comparisons_present'
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
    expect(cells).toHaveLength(35)
    expect(cells.slice(8, 10)).toEqual([daily.day.observations[i].near_slot, daily.day.observations[i].far_slot])
    expect(cells.slice(27)).toEqual(['false', 'null', 'null', 'null', 'null', 'null', 'null', 'false'])
    expect(cells[23]).toBe(String(daily.day.observations[i].metrics.annualized_spread_ratio.value))
  })
  expect(lines[3].split(',').slice(21, 24)).toEqual(['0', '0', '0'])
  expect(resultCsv(validateResult(closed))).toBe('\uFEFF' + expectedHeader + '\r\n')
  expect(resultCsv(validateResult(empty)).split('\r\n')[1].split(',').slice(21, 24)).toEqual(['null', 'null', 'null'])
  expect(resultCsv(validateResult(excluded)).split('\r\n')[1].split(',')[12]).toBe('0')
})
it.each(referenceStates)('preserves provided reference %s/%s/%s', (...state) => {
  const r = withReference(daily, state)
  expect(resultCsv(r).split('\r\n')[1].split(',').slice(27)).toEqual(['true', '000852.SH', daily.request.trade_date, state[0] === 'available' ? '0' : 'null', state[0], String(state[1]), String(state[2]), 'false'])
})
it('uses shared formula protection, quoting and safe response filenames', () => {
  const r = validateResult(structuredClone(daily)); r.day.observations[0].near!.contract_code = '=SUM(1,2)"\r\n'
  const csv = resultCsv(r)
  expect(csv).toContain('"\'=SUM(1,2)""\r\n"')
  expect(csv.endsWith('\r\n')).toBe(true)
  expect(exportFilename(r)).toBe('futures-calendar-spread_IM_2024-10-18.csv')
  expect(exportFilename(r, true)).toBe('futures-calendar-spread_IM_2024-10-18_context.json')
  r.request.trade_date = '../unsafe:date'
  expect(exportFilename(r)).toBe('futures-calendar-spread_IM_.._unsafe_date.csv')
})

it('exports ten actual comparisons with separate instruments, definitions and denominators', () => {
  const r = validateResult(spot)
  const rows = resultCsv(r).slice(1).trimEnd().split('\r\n').slice(1).map(row => row.split(','))
  expect(rows).toHaveLength(10)
  expect(rows.slice(0, 6).every(row => row[6] === 'calendar_spread')).toBe(true)
  expect(rows.slice(6).map(row => row[8])).toEqual(['M0', 'M1', 'Q1', 'Q2'])
  rows.slice(6).forEach((row, i) => {
    const item = r.futures_spot_comparisons![i]
    expect(row[6]).toBe('futures_spot')
    expect(row[7]).toBe('daily_futures_spot_definition_v1')
    expect(row[14]).toBe('index')
    expect(row[15]).toBe('000852.SH')
    expect(row[17]).toBe('null')
    expect(row[18]).toBe('null')
    expect(row[19]).toBe(String(item.remaining_days))
    expect(row[23]).toBe(String(item.annualized_spread_ratio))
    expect(row[34]).toBe('true')
  })
  expect(rows[6][22]).toBe('null')
  expect(rows[6][19]).toBe('0')
  expect(JSON.parse(contextJson(r)).data).toEqual(r)
  expect(JSON.parse(serializeJson(r))).toEqual(r)
  expect(JSON.parse(contextJson(validateResult(daily))).metadata.reading_notes).toContain('历史数据包未提供期现比较结果')
})
