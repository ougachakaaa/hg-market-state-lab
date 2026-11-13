# WP-A private real research examples — 2026-11-13

Execution evidence under [Examples](EXAMPLES.md) and [Authenticity](AUTHENTICITY.md).
Required baseline `69cd25f15dd35d086582726439236ebe472f36d3`, branch
`feat/github-pages-demo`; initial worktree was clean. Producer business source remains
unchanged. Technical checkpoints and public rights are independent; market and output
Publication Rights remain **BLOCKED**. No D4 composition or public release is accepted.

## W2 checkpoint

Both formal `futures_roll_long_v1` / IM requests retain the inclusive
`2026-01-01..2026-11-11` window. Each independently ran
`create_futures_roll_service().run(request)`, Result construction/validation and
portable Evidence construction/encoding. The tool redirects only Dataset storage
placement using WP8's existing isolation pattern. No existing cache or R3 Export
supplies W2's proof, and no Dataset tables are queried or assembled by the tool.

| Check | M1 | Q1 |
| --- | --- | --- |
| Strategy | `expiry_to_M1_v1` | `expiry_to_Q1_v1` |
| Actual observed sessions | 206; January 5–November 11 | 206; January 5–November 11 |
| Execution legs / rolls | 20 / 9 | 8 / 3 |
| Final Flat, daily accounting, actual expiry/Close bindings | PASS | PASS |
| Complete Result, returns/drawdown V2 Views and full Evidence | PASS | PASS |
| Formal guarded offline reproduction | PASS | PASS |
| Existing Embedded Result validator | PASS | PASS |

Final Exports prove 315/315 CFFEX natural days, 206/206 IM product-days with 824
Contract-day facts, 315/315 auxiliary SSE natural days, and 206/206 CSI1000 Index
sessions. Missing/pending/failed counts are zero. SSE remains auxiliary, outside
the official three-export fingerprint. Both strategies consume identical input
fingerprint `c7e9bdadf1881be9d6a60256d50e857a579de7f7cec40938bdb876e4a2657631`.
Result/definition profiles remain `futures_roll_long_result_v1` /
`futures_roll_long_definition_v1`.

Separate Results retain full PnL, equity, return, benchmark, drawdown, Trades/Rolls,
limitations and producer Views privately. No financial values are copied here.
Offline reproduction runs in a separate process with credential lookup, socket
connections and SQLite connections forbidden. Complete reproduced Results match the
retained JSON. Eight negative frontend probes reject Profile, window, missing View
and Strategy mismatches. The existing validator returns the producer payload unchanged.

Private tooling is [the explicit runner](../../scripts/private_wpa_examples.py) and
[the validator runner](../../scripts/validate_private_wpa.mjs). Neither is a build input.
The complete private handoff, Research checkpoint and final regression matrix follow
in subsequent WP-A checkpoints; this section alone is not overall WP-A acceptance.
