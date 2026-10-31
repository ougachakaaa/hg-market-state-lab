# Price Segmentation Research V1

This independent Descriptive case specializes [Research](../../../ARCHITECTURE.md) and
[Descriptive](../../ARCHITECTURE.md). It observes the shape of one historical price
series using the [PIP algorithm](../../../algorithm/pip/ALGORITHM.md), then converts
adjacent important points into financial segments. It is not a peak/trough swing model,
forecast, backtest or trading strategy. The case owns financial input, date mapping,
segment meaning and evidence; the algorithm owns only numerical selection and diagnostics.
[INPUTS.md](INPUTS.md) owns its upstream and completeness contract.

Status: authority only; neither PIP nor this observation API is implemented. The numerical
precision decision in the algorithm authority, log base and fingerprint encoding below are
open before implementation-ready status can be claimed.

## Request and identity

Research identity is `price_segmentation_v1`. The explicit request fixes one canonical
Index Daily index_code, inclusive date-only start/end, Close, log-price fitting,
trading-session index time, `pip_vertical_error_bounded_v1`, and a finite positive epsilon
in log-price units. Dates and subject are required; there is no default or automatic window,
and no horizon or rolling window. The actual series must contain at least two sessions.
Index Daily's public date and code validation applies. Stocks are not supported; future
stock cases require an authorized upstream and explicit adjusted-price semantics.

The stable request identity is the structural tuple of this research/version, canonical
index_code, inclusive dates, close, log transform, session-index time, algorithm ID and
actual epsilon. It excludes actual mutable input facts, acquisition time and process/run
identifiers. Structural equality must not silently collapse distinct requests. A changed
window or epsilon may change every segment. Request identity is not input identity or
proof that two results used the same facts.

The approved design does not specify the logarithm base; it changes epsilon
calibration and must be explicitly decided before implementing the transform.

The future independent public Python observation entry belongs to
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

Input identity must distinguish changed ordered dates or actual close values and retain
sufficient immutable evidence to reproduce and validate the result; a mutable cache, request
or date window is insufficient. The exact canonical encoding, numerical value representation
and fingerprint algorithm were not specified by the approved design. Choose and document a
versioned collision-resistant encoding before implementation; do not invent a digest or
claim interoperability here. Preserve public provenance and no credentials or private data.
No mandatory persistence is introduced.

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
