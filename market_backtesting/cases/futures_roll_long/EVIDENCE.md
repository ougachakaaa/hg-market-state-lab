# Futures Roll Long portable evidence

This specializes [Result](RESULT.md) and owns the case-specific
`futures_roll_long_evidence_v1` portable package, not an online store or HTTP DTO.

## Contents and encoding

The package retains the semantic request, canonical three-export input payload,
independent SSE Calendar request/export, exact public requests, definition/result
versions, policy identity and fixed transformation/execution assumptions. It also
retains the complete W2 replay (including every Core daily record, Previous/Target/Next
Portfolio, snapshot, pricing, assumptions, ordered mark/close/open StateEvents and
Accounting), Performance and accepted BacktestResult.

The encoded top-level fields are exactly:

```text
profile = futures_roll_long_evidence_v1
request
canonical_inputs         # existing futures_roll_long_inputs_v1 JSON object
auxiliary_sse_calendar   # separately encoded complete Calendar export
input_fingerprint
replay                   # complete existing FuturesRollReplay semantic fields
performance              # complete existing FuturesRollPerformance fields
result                   # accepted BacktestResult semantic fields
associations = {public_requests, auxiliary_sse_request, definition_version,
                result_profile, policy, strategy_profile, assumptions}
```

`replay`, `performance` and `result` preserve their immutable Python carrier field
names and sequence order. Canonical export envelopes retain all published row fields;
no field is silently omitted. The Python package holds these sections as immutable
JSON bytes; the portable outer encoding embeds them as objects, not escaped strings.

The Python package is immutable. Its portable encoding is UTF-8 JSON with sorted keys,
compact separators and no nonfinite numbers. Dates use canonical ISO dates; canonical
input float fields retain the existing float64 hex representation. Replay/result
numbers use round-trip JSON binary64 numbers. Duplicate keys, missing/extra fields,
wrong types and unsupported profiles fail explicitly. No pickle, dynamic class loading,
filesystem paths, credentials, persistence identifiers or raw ensure diagnostics enter
this package. File ownership and storage belong to the caller.

The input profile remains `futures_roll_long_inputs_v1`: exactly CFFEX Calendar,
Futures and Index. Neither the request/profile nor auxiliary SSE Calendar is a fourth
fingerprint member. The auxiliary request and export are independently validated.

## Public pure Python boundary

`build_backtest_result(execution)` projects and validates existing records without
replaying or reanalyzing. `validate_backtest_result(result, execution)` checks the
producer contract. `build_evidence_package(execution, result)` validates before
retaining evidence. `encode_evidence_package(package)` and
`decode_evidence_package(payload)` use bytes without file I/O.

`reproduce_futures_roll_evidence(payload, expected_result=None)` validates retained
public inputs, recomputes and checks the fingerprint, rebuilds the existing pure W2
input, invokes the existing Replay and Analyzer and rebuilds the Result. It compares
the complete reconstructed replay, performance, result and package metadata, including
all StateEvents and their state-chain reconstruction. Decode also performs this
verification before accepting portable evidence. The deterministic outcome carries
`status=verified`, fingerprint, rebuilt result and checked daily/event counts.
Failures raise safe typed case errors without repair or upstream I/O.

This verifies internal reproducibility and inconsistency/tamper detection relative to
retained facts and fingerprint; it is not a cryptographic signature or proof of Source
freshness. Changing all facts and recomputing all evidence creates a different package.

## Usage

```python
execution = service.run(request)
result = build_backtest_result(execution)
package = build_evidence_package(execution, result)
payload = encode_evidence_package(package)
# The caller may retain/transfer payload by its own storage mechanism.
verified = reproduce_futures_roll_evidence(payload, expected_result=result)
assert verified.status == "verified"
```

All functions above are exported from
`market_backtesting.cases.futures_roll_long`; preparation and preflight retain their
existing contracts. Reproduction has no dependency on the original process, objects,
cache contents, credentials or temporary paths.
