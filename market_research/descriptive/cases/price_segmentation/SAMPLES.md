# Price Segmentation Base sample semantics V1

This authority specializes [Price Segmentation](ARCHITECTURE.md) and defines its
formal one-dimensional sample semantics, not an implemented converter or Statistics
research. The canonical source is one valid, complete `SegmentationObservationSet`;
the existing [scalar converter](../../SAMPLE_CONVERSION.md) and scalar Observation
contract remain unchanged. Numerical legality and methods belong to the public
[Statistics contract](../../../../market_statistics/CONTRACT.md).

## Population, grain and selection

A `PriceSegment` is the geometric line between adjacent PIP important points, not
itself a statistical sample or necessarily a complete market swing. The candidate
population is **all canonical Base segments of one specified ObservationSet**, in
source order. Each candidate occurs exactly once and retains its source segment
identity, indices, dates, endpoint closes, duration, signed amplitude, direction,
boundary flags, request identity and input fingerprint through the source.

A numerical sample is one metric value for one candidate selected under a Research
sample policy. The baseline policy `base_direction_v1` has an explicit direction
parameter `all`, `up`, `down` or `flat`. `all` selects every candidate; the other
values select exactly those with the corresponding original `direction`. This policy
does not exclude one-session, small-amplitude, flat or boundary-touching segments
merely for those properties. Directional nonmatches are excluded with reason
`direction_mismatch`. The policy identity is the pair (`base_direction_v1`, direction);
there is no implicit default. Further filtering requires a separately specified,
versioned policy with explicit criteria, parameters, identity and exclusion reasons;
it is not authorized by this baseline.

For each selection, partition the original candidates into eligible and excluded
records, each in source order, each with its original segment identity; excluded records
also retain their reason. Every candidate appears exactly once in this partition:
`candidate_count = eligible_count + excluded_count`. Report all three counts and the
policy, even for an empty selection. The denominator of selection coverage is the
original candidate count; the count analyzed by Statistics is the eligible count.
The direction groups up/down/flat partition all candidates; `all` overlaps each of
them. Different analyses may reference the same segment, but never duplicate it within
one selection. Equal numerical values from distinct segments retain their multiplicity.

## Values and direction

Each selected segment supplies one value per requested metric. Metric identities and
units are fixed as follows:

| Metric / version | Value from the original segment | Unit |
| --- | --- | --- |
| `duration_v1` | `duration_sessions = end_index - start_index` | `trading_session_intervals` |
| `signed_amplitude_v1` | `amplitude_ratio = end_close / start_close - 1` | `decimal_ratio` |
| `absolute_amplitude_v1` | `abs(amplitude_ratio)` | `decimal_ratio` |

Duration counts trading-session index intervals, not calendar days or inclusive price
rows. Signed amplitude is the simple endpoint return, not log difference. Absolute
amplitude is the magnitude of that return, not maximum drawdown, maximum rise or an
intrasegment excursion. Up/down/flat use the source direction derived from actual price
change; do not reclassify by rounded amplitude or a threshold. Down signed returns and
absolute declines are distinguishable views; do not silently mix absolute declines
into an up-only sample. The three values for a segment refer to the same source event,
not three independent market events.

## Boundaries and dependence

Preserve both `touches_start_boundary` and `touches_end_boundary`. Base geometric
segment endpoints are actual observed inputs; touching the research window does not
make their values missing or invalid, and neither endpoint segment is excluded by
default. A boundary flag is not a swing-censoring classification. Complete market
swing duration, completeness and censoring require a separate future decision.

Samples are not automatically independent or identically distributed. Adjacent
segments share a price endpoint, all derive from one historical series, and PIP point
selection depends on the entire research window. Changing window or epsilon may change
the historical population; results from different epsilons cannot simply be pooled as
one independent population. Quantiles and counts describe the selected population's
empirical distribution; segment counts are not independent experiment counts and do
not establish significance, predictive power or trading win rate.

## Identity and evidence

The source defines segment identity as `(request_identity, start_index, end_index)`;
it does not include actual facts. A candidate occurrence is identified by that original
segment identity **and** the source input fingerprint. The fingerprint identifies actual
ordered price facts, independently of the structural request, which includes algorithm ID
and epsilon. Preserve both: equal facts with different epsilon have different requests;
equal requests with changed facts have different fingerprints. As specified by the source,
the digest is collision-resistant identification, not proof of inequality.

The identity of a numerical sample is the tuple `(candidate occurrence identity,
metric/version, selection identity)`; selection identity includes policy version and
all parameters. Thus values from different metrics or selection views remain separately
identifiable while linking to the same original segment. This is a structural business
identity, not a random run ID or a new hash/persistence protocol.

Research retains an immutable or effectively immutable binding to the actual source
ObservationSet and an ordered sequence of eligible segment identities aligned
positionally with numerical values, plus the selection identity and complete exclusion
records. The source supplies request, fingerprint, algorithm, epsilon, dates, flags,
diagnostics and retained public input evidence; do not copy the full price history or
source evidence into every sample. This follows the existing source/binding principle,
without claiming the scalar `SampleBinding` accepts this structured source or defining
durable resolution. For each successful projection, `len(values) = eligible_count =
len(ordered eligible identities)`. Preserve original order and provenance, without
reacquisition, PIP rerun, point discovery, source mutation or silent repair.

## Numerical boundary and implementation readiness

A separate Research-owned segmentation sample adapter is required: existing `convert`
accepts scalar `ObservationSet`, not `SegmentationObservationSet`. For a selected metric
it must produce one ordered one-dimensional public `NumericSample` and its Research
binding. Only the NumericSample crosses into Statistics. Retain the existing finite
binary64 amplitude value; adapt integer duration to binary64 only if exactly representable,
without changing its mathematical value. Reject an invalid/inconsistent source, an
unrepresentable duration or an otherwise illegal numerical sample; do not drop, round,
substitute or repair values. Statistics owns `InvalidSample` and numerical legality.
An empty directional selection remains a valid accounted selection but cannot produce
an empty NumericSample; report conversion failure with its counts and evidence intact.
Singletons are valid. The adapter is deterministic and pure. One successful projection
can be consumed by public Quantile and IntervalCount for compatible specs; association
of those results to this structured binding is future work, not the existing scalar
association's automatically supported path.

Duration × amplitude analysis requires paired values joined by the same candidate
occurrence and same selection, retaining their respective units and binding. The current
Statistics public contract supports no multivariate sample; a future independently
authorized numerical contract is needed before joint distribution computation. No 2D
engine or statistical interface is specified here.

Status: **Semantic Ready / Implementation Pending**. Base one-dimensional semantics
are not implemented or runtime accepted. Deterministic adapter acceptance must cover exact metric values and units,
one-session/small/flat/boundary cases, direction partitions and empty selections,
conservation and exclusion reasons, equal values, positional linkage, changed request
versus changed fingerprint, exact duration conversion, invalid sources/numerics, purity,
and public Statistics compatibility. It must not access Provider or user caches.

## Deferred populations

[Review](REVIEW.md)'s Light and Medium are experimental diagnostic views, not canonical
observations or authorized formal statistical populations; they cannot enter this
adapter. Promotion requires explicit decisions on profile identity/version, merge
algorithm and parameters, ordered source mapping, result identity, boundary meaning,
selection, reproducibility and the loss of the original PIP error guarantee. It does
not follow merely from this contract. A complete Swing population likewise requires
separate definitions of swings, completeness, boundary censoring and selection. Both
remain deferred pending business decisions; this authority changes no review algorithm.
