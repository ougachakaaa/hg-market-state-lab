# Price Segmentation Research V1

This independent Descriptive case specializes [Research](../../../ARCHITECTURE.md) and
[Descriptive](../../ARCHITECTURE.md). It observes the shape of one historical price
series using the [PIP algorithm](../../../algorithm/pip/ALGORITHM.md), then converts
adjacent important points into financial segments. It is not a peak/trough swing model,
forecast, backtest or trading strategy. The case owns financial input, date mapping,
segment meaning and evidence; the algorithm owns only numerical selection and diagnostics.
[INPUTS.md](INPUTS.md) owns its upstream and completeness contract.

Status: the independent PIP algorithm, Input Preparation and segmentation observation
Python APIs are implemented. Real-market E2E acceptance remains outstanding; Statistics,
converter, HTTP and Workbench integration are not implemented.

## Request and identity

Research identity is `price_segmentation_v1`. The explicit request fixes one canonical
Index Daily index_code, inclusive date-only start/end, Close, natural-log-price fitting,
trading-session index time, `pip_vertical_error_bounded_v1`, and a finite positive epsilon
in natural-log price difference units. Dates and subject are required; there is no default or automatic window,
and no horizon or rolling window. The actual series must contain at least two sessions.
Index Daily's public date and code validation applies. Stocks are not supported; future
stock cases require an authorized upstream and explicit adjusted-price semantics.

The stable request identity is the structural tuple of this research/version, canonical
index_code, inclusive dates, close, log transform, session-index time, algorithm ID and
actual epsilon. It excludes actual mutable input facts, acquisition time and process/run
identifiers. Structural equality must not silently collapse distinct requests. A changed
window or epsilon may change every segment. Request identity is not input identity or
proof that two results used the same facts.

The fixed transformation is `y_t = ln(close_t)`, using the natural logarithm; the base
is not configurable. Signed amplitude is the simple return from actual endpoint prices,
not the difference of their log prices.

The independent public Python observation entry belongs to
`market_research.descriptive.cases.price_segmentation`; it performs input preparation
through authorized public services and invokes the PIP public algorithm. A pure construction
boundary consumes validated prepared inputs without I/O. The precise callable names and
carrier types are implementation choices, not an authorization to add a generic engine.

## Observation result

Return a structured result with request identity and four components:

* Important points: original zero-based session index, actual date and original close,
  with links to the retained input evidence. They are strictly increasing and include
  indices 0 and N-1; reconstructed values are never substituted for actual prices.
* Segments: one per adjacent important-point pair in ascending order. A stable segment
  identity is `(request_identity, start_index, end_index)`; actual input fingerprint remains
  separate and must accompany a result when comparing occurrences across changed facts.
  Include both indices, dates and real endpoint prices, duration `end_index - start_index`
  in trading-session intervals, signed amplitude `end_close / start_close - 1` in
  `decimal_ratio`, direction `up`, `down` or `flat` according to the sign of the actual
  price change, and flags identifying contact with the first and last scope endpoints.
* Diagnostics: input point, important point and segment counts, actual maximum log-space
  reconstruction error, algorithm ID and actual epsilon.
* Provenance: full request/version, selected public source identities and actual requests,
  validated exports and coverage/completeness evidence or adequate immutable references,
  actual input identity/fingerprint, log transform, session-index time and algorithm definition.

For M important points there are M-1 segments, covering the entire input in order. Adjacent
segments share exactly their common endpoint; that endpoint creates no extra independent
segment event. The sum of durations is N-1. Flat is legal, as are adjacent segments with
the same direction. Scope boundary flags only indicate contact with the selected input;
they do not assert complete market swings. Amplitude always uses actual closes, never a
reconstructed line. Fail explicitly if derived numbers are non-finite or invariants fail.

## Input fingerprint and retained evidence

Input fingerprint identifies the actual ordered price facts, independently of the request
identity and PIP algorithm version. Retain the final consumed public exports, coverage proofs,
actual requests and preliminary/ensure diagnostics as specified by [INPUTS.md](INPUTS.md),
or adequate immutable references; a hash alone cannot reconstruct the inputs. Failed
preparation retains available diagnostics without claiming a successful fingerprint.

`price_segmentation_inputs_v1` is SHA-256 of the UTF-8 bytes, without BOM, of compact
JSON with `ensure_ascii=true` and separators `(',', ':')`, encoding this ordered array:

```text
["price_segmentation_inputs_v1", "tushare_index_daily", "index_daily", 1,
 index_code, [[trade_date, close_hex], ...]]
```

Use the validated selected index's complete final public Index Export and complete SSE
Calendar proof. Include exactly one pair per consumed session, in strictly ascending calendar
order, after validating that the final rows match those sessions. `trade_date` is a
`YYYY-MM-DD` string and `close_hex` is Python binary64 `float.hex()` of the actual consumed
finite positive Close; never hash its logarithm or a reconstructed price. The encoding retains
unchanged canonical index_code and has no unordered objects. Do not reorder invalid data to
make it pass validation. The version literal identifies this encoding, not the algorithm.
The digest is the lowercase hexadecimal SHA-256 representation of those bytes.

Different consumed dates, Close binary64 values or index identity change the canonical
payload; SHA-256 supplies collision-resistant identification, not mathematical proof of
inequality. Calendar/export proofs and other source fields remain retained evidence, not
part of this minimal fingerprint. Request dates, epsilon, algorithm version and transform
are recorded separately in request/result provenance; changed requests can consume identical
facts. Acquisition attempts, runtime, random IDs, credentials and internal database paths
are excluded. No persistence, cache lifecycle or general fingerprint framework is imposed.

Verify exact canonical bytes and digest against an independent fixture, deterministic repeats,
changed date/close/index sensitivity, request/algorithm separation and unchanged fingerprint
for different preliminary diagnostics with identical final consumed facts. Verify retained
proof and failure evidence separately.

## Reconciliation and acceptance

The existing [scalar Observation](../../OBSERVATION.md) requires horizon and scalar values;
its public API and case-specific Trailing Return dispatch remain unchanged. Existing
[converter](../../SAMPLE_CONVERSION.md), [execution](../../EXECUTION.md) and
[capability/preview](../../RESEARCH_CAPABILITY.md) are for that scalar path: the implementation
binds execution and capability publication to Trailing Return. None blocks this separate
entry; none publishes or executes segmentation. Any future integration requires its own
semantic decision and implementation, not a fabricated horizon, scalar or empty Statistics
AnalysisRequest. Trailing Return contracts and Statistics are unchanged.

Tests for a future implementation must independently verify the input rules and evidence,
PIP invocation, all result invariants and exact endpoint mapping, first/last/both boundary
flags, flat and same-direction segments, N=2, missing dates and invalid closes, failure
diagnostics, identity stability and sensitivity to changed inputs, window and epsilon.
Changing source facts under the same request must preserve request identity while changing
actual input identity. Verify independently constructed results do not claim runtime/live
acceptance until those checks and applicable integration tests have run.
