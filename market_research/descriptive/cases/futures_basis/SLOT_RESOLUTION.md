# Contract identity and relative tenor resolution

This contract owns SD02–SD04 for the [case](ARCHITECTURE.md). DataLake remains
the owner of [metadata](../../../../data_lake/datasets/tushare_equity_index_futures/FACTS.md)
and [complete active-universe proof](../../../../data_lake/datasets/tushare_equity_index_futures/CONTRACT_UNIVERSE.md).
Research assigns relative roles to those facts; it does not acquire a second catalog.

## Identity and evidence

Immutable `contract_code` identifies a real ordinary CFFEX contract; its day fact
has natural identity `(contract_code, trade_date)`. Product, continuous/main
series and relative Slot are not real contracts. Validate the public product,
underlying, delivery_month and lifecycle association; do not infer expiry from a
code, delivery month or a third-Friday formula.

For product p and CFFEX open date d, use only the proven complete active set:

```text
active(p, d) = contracts in the complete producer basis with
              product_code == p and list_date <= d <= delist_date
```

[Input preparation](INPUTS.md) obtains this set from the metadata attached to a
complete successful product-day export. A complete Export proves its successful
rows exactly represent that day's expected set; arbitrary available quote rows
do not. The pure resolver receives metadata, product/date and completeness
evidence, not prices. Missing prices in a resolver fixture cannot alter mapping.
Never union metadata across days to reconstruct an unknown day's catalog; each
day retains the producer's successful historical basis.

## Relative roles

| Public Slot | Optional internal spelling | Meaning |
| --- | --- | --- |
| M0 | FRONT | First active delivery month |
| M1 | NEXT | Next active delivery month, consecutive to M0 |
| Q1 | QUARTER_1 | First subsequent quarter month not occupied by M0/M1 |
| Q2 | QUARTER_2 | Second subsequent quarter month not occupied by M0/M1 |

Public order is M0, M1, Q1, Q2. Internal spellings are exact aliases, not another
business vocabulary. M0 means the front valid month: after its expiry it need
not equal the natural month containing d. This resolves the informal “当月” term.

For a nonempty set, require exactly four ordinary contracts in four unique
delivery months. Sort validated YYYYMM maturity facts; the first two months must
be consecutive, including December→January. The last two must be the first two
March/June/September/December months strictly after M1. A quarter month already
occupied by either near month is consumed once and cannot also hold Q1/Q2.
Do not truncate additional contracts, deduplicate a month, skip an absent expected
month or promote a later quote to repair the structure. An irregular/ambiguous
nonempty set fails Slot resolution with product, date, metadata and reason.

A proven empty active set yields all four Slots Not Applicable (`no_active_contract`),
not four missing-price observations. A missing completeness proof fails preparation;
it is never evidence of legal emptiness or pre-listing.

## Lifecycle and transitions

Re-resolve every candidate open date. The expiry date still includes the expiring
contract. On the next open date it is absent, and new roles follow the actual
active set. Do not assume an unlisted replacement exists. For example, active
months `[202611, 202612, 202703, 202706]` resolve in that order; a subsequent
proven set `[202612, 202701, 202703, 202706]` moves December into M0.
For `[202603, 202604, 202606, 202609]`, March occupies M0, not Q1.

Return ordered `(product_code, trade_date, slot, contract_code)` mappings with
metadata/evidence association, or the explicit empty-set outcome. A change of a
Slot's mapped contract between adjacent CFFEX candidates emits a Transition even
if its prices are unavailable. [Observation](OBSERVATION.md) owns series segments.

WP2 must test expiry-day inclusion, next-open-day changes across holidays,
year/month rollover, near/quarter overlap, empty proof, invalid month structures,
duplicate identities/months, missing proof and unchanged mapping when quote
availability/volume/open interest changes. No live market data is needed for WP2.

## Python boundary and evidence handoff

The public boundary is `market_research.descriptive.cases.futures_basis`:
`resolve_daily_slots(product_code, trade_date, contracts, *, evidence)` returns
`DailySlotResolution`; `detect_contract_transitions(product_code,
candidate_sessions, resolutions)` returns `TransitionResult`. Carriers are frozen
dataclasses with ordered tuples; calls perform no I/O and do not mutate inputs.

`ContractMetadata` contains exactly contract_code, product_code,
underlying_index_code, delivery_month, list_date and delist_date; trade_date is
supplied separately. The caller supplies the day's complete active
metadata, not a union/catalog to filter. Inactive/unlisted entries, duplicate codes
or months, malformed ordinary identity, product/underlying conflicts and evidence
membership mismatches fail explicitly. Only validated maturity sorting is allowed.

`DailyUniverseEvidence` binds product_code, trade_date, `complete=True`, the exact
unique `active_contract_codes` tuple and a nonempty `source_export_ref` to the
caller's retained final Futures Export. This is a Research handoff from already
validated producer evidence, not a new DataLake proof API or an assertion that a
boolean/reference authenticates completeness. Input Preparation alone constructs
it after validating the complete final Export and Calendar under [Inputs](INPUTS.md).
WP3 must retain that full Export; references/digests alone cannot reproduce inputs.
No coverage, catalog, cache, price or source acquisition is reimplemented here.

Each daily result has product/date, four `SlotMapping` entries in public order
and the evidence. A mapping carries slot, actual metadata (or None), evidence,
`resolved`/`not_applicable` status and None/`no_active_contract` reason. Source
metadata and evidence remain associated independently on each date; a changed
metadata version alone does not create a contract-code Transition.

`CandidateSessions` carries the complete already-validated CFFEX `dates` tuple
and a nonempty `calendar_export_ref`. Transition detection requires strictly
increasing unique dates and exactly one valid daily result per candidate, for
one product. Missing, extra, unordered or mismatched results fail the whole call;
no transitions bridge an omitted candidate. It trusts the caller's validated
Calendar, never infers openings from weekdays or an exchange holiday formula.
An empty candidate sequence with no results is legal.

Real-to-real code changes produce `ContractTransition` with product, slot, both
dates/codes, metadata and evidence. Proven absent-to-present/present-to-absent
changes instead produce `AbsenceBoundary` with `appeared`/`disappeared` direction
and both Slot mappings. Both output tuples retain date then public Slot order.
Same-code and absent-to-absent pairs produce neither record. These records do not
define execution, returns or chart segments. `SlotResolutionError` retains category,
product/date, reason, metadata and available evidence; invalid inputs never yield
a partial successful result.
