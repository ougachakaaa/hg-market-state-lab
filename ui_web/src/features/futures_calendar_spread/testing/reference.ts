import type { Result } from '../api/validateResult'
import daily from './daily.json'
export const referenceStates = [
  ['available', null, null], ['not_applicable', 'non_trading_day', null], ['unavailable', 'cache_incomplete', null],
  ['error', 'final_export_incomplete', 'incomplete_inputs'],
  ['error', 'credential_missing', 'upstream_unavailable'], ['error', 'cache_incompatible', 'upstream_unavailable'], ['error', 'operation_unavailable', 'upstream_unavailable'],
  ['error', 'malformed_export', 'input_contract_error'], ['error', 'malformed_ensure_result', 'input_contract_error'], ['error', 'upstream_request_rejected', 'input_contract_error'],
] as const
export function withReference(base: unknown = daily, state: typeof referenceStates[number] = referenceStates[0]): Result {
  return { ...structuredClone(base as Result), underlying_index: {
    index_code: '000852.SH', trade_date: (base as Result).request.trade_date,
    close: state[0] === 'available' ? 0 : null, availability: state[0], reason_code: state[1], failure_category: state[2],
  } }
}
