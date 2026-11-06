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
