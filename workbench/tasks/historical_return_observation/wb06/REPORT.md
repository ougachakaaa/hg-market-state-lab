# WB-06 research and execution report

**Natural-language planning and deterministic E2E passed. Actual 2010-2026 market
research remains BLOCKED and was not executed.** The numbers below come from real
Research/Statistics computation over artificial service fixtures. They describe the
test data only, and provide no finding about historical CSI1000 returns.

The supplied example asked for CSI1000 index `000852.SH`, inclusive
2010-01-01..2026-10-28, trailing returns over 10 trading sessions, quantiles at
0.1/0.5/0.9 and interval edges [-0.15,-0.05,0,0.05,0.15] in decimal_ratio. Metric is
`trailing_cumulative_return_v1`, parameters `{}`, failure policy `continue`.
All inputs were explicit; no clarification or default was required.

Codex discovered the sole published capability from an actual backend, then authored
[the complete candidate](candidate.json). It understood anchors as return-ending
sessions and the formula as `close(T)/close(T-10)-1` on the complete selected calendar.
Public Python Preview produced one Job and two analyses; G4 froze that exact full
window. Comparison with the original request found **no interpretation mistakes**.
Only analysis request IDs were assigned by the Agent. The full question exceeded the
HTTP window limit, so Codex selected the public Python surface without splitting it.

Actual operations were official G1 OpenAPI inspection, G3 list/detail HTTP discovery,
G4 public Research Preview/freeze/read-back, then one G5 public Batch call per test
scenario. Preparation, observation construction, conversion, Statistics Quantile and
IntervalCount, and Research result association all used existing implementations.
Only Calendar/Index services and user interaction were simulated, under network/SQLite
guards. G2 authentication and G6 visualization were explicitly SKIPPED under MVP policy.
No real provider was contacted. A separate absent-consent Run correctly blocked G5.

The artificial calendar opens weekdays and ignores real exchange holidays. Its
ordered closes follow `80+((7*i)%41)` beginning 2009-12-01. Fixture metadata labels
the requested code, but proves no current provider identity. Historical published live
evidence separately identifies `000852.SH` as 中证1000. These are distinct claims.

Both final fixture Batches had status `success`, one Job `Success`, and both analyses
`success`; planned/success/failed/skipped = 1/1/0/0. Statistics use Type 7 linear
quantiles (`type7_linear_v1`), explicit interval geometry and the entire Eligible
sample as frequency denominator. The final interval alone includes its right edge.

| Quantile | Complete fixture (n=4,389) | Missing-row fixture (n=4,387) |
| --- | --- | --- |
| 0.1 | -0.125 | -0.125 |
| 0.5 | -0.1071428571428571 | -0.1071428571428571 |
| 0.9 | 0.34523809523809534 | 0.34523809523809534 |

All values use decimal_ratio: for example -0.125 means -12.5% **in this fixture**.
The unchanged quantiles in the partial test reflect these actual saved values, not
inferred equality or imputation.

| Interval / outside category | Complete count / frequency | Missing-row count / frequency |
| --- | --- | --- |
| below -0.15 | 0 / 0 | 0 / 0 |
| [-0.15,-0.05) | 3,104 / 0.7072226019594441 | 3,102 / 0.707089126966036 |
| [-0.05,0) | 0 / 0 | 0 / 0 |
| [0,0.05) | 0 / 0 | 0 / 0 |
| [0.05,0.15] | 0 / 0 | 0 / 0 |
| above 0.15 | 1,285 / 0.2927773980405559 | 1,285 / 0.29291087303396396 |

The complete fixture retains E=4,389/U=0/X=0 out of 4,389 candidates, observation
coverage 1.0, overall Index coverage 4,399/4,399 and warm-up 10/10. The partial diagnostic
deliberately lacks the 2024-01-10 row: E=4,387/U=2/X=0, observation coverage
0.9995443153337891, overall facts 4,398/4,399, sample facts 4,388/4,389, warm-up 10/10.
One missing row affects its own anchor and another anchor's lookback. Research exports,
ensures the exact incomplete range once, then consumes the legal final partial Export;
it does not infer why a provider lacks a row. Calendar slices remain complete in both
fixtures. Actual earliest warm-up Index date is 2009-12-18 in this artificial calendar.

Independent checks recomputed every endpoint return from the retained public Exports,
verified exact binary64 sample values and binding order, Type 7 values, bin membership
and count/frequency conservation. All association references and fingerprint bytes were
verified. Input profile is `trailing_return_inputs_v2`; complete fingerprint is
`db234ddf6f710d5d6dcaa3f3a05a51cee8d6803539b58b0210bf0f0a09325edc`, partial fingerprint
`390d93a627f6544401f88dbc5530078b7ccb2d169cc5286ecf314e4d31027b9a`.
Overlapping 10-session windows share inputs. No IID, causal, predictive, uncertainty
or trading conclusion follows. No complete real-market population has been measured.

Original immutable results and evidence:

| Scenario | Run | Workflow artifact | Result artifact |
| --- | --- | --- | --- |
| Complete fixture | `35ab3cf0064444feac135d9cac29ac8e` | `2dd7a998db4a454b815f1e81a580378e` | `f727242d936c43bf934358418964cdca` |
| Missing-row diagnostic | `d2400af9382540daabe06da074fba33d` | `3c4ccce00a7b4561a47c647a31904490` | `6143a824784c4a66a376467d608abf61` |
| No consent | `407cf8e7450e43afb059077c64ab4b08` | `a4423d4c94f84cb6ba7975e8827a4c8f` | No invocation/result; G5 BLOCKED |

Store root is `workbench/.runs/`; join Run ID and `blobs/ARTIFACT_ID` to locate each
original. All exact hashes, Preview, simulated approval, G5 reports, independent
inspection and historical-read references are in [results.json](results.json).
Complete Workflow SHA-256:
`d1f77eae7eb37f6bb77d681e289bccef3bb0fe726f41c2692e84a18046698bad`.
Complete result SHA-256:
`c6294250e4361943590bebaeafade6abd78130f1a50e70dcd4af564fa631625d`.
RunStore independently verifies registered bytes. Saved results remain readable after
later test-injected G3 FAIL, while current G4 execution eligibility is revoked.
Local ignored Runs are not shipped in Git; committed public summaries retain their
locations/hashes but are not a substitute for the original complete blobs.

The [full problem report](PROBLEMS.md) and [machine log](problems.json) retain all
encountered issues, including resolved ones. Agent-authored harness bugs caused a
context-manager failure, incorrect recorder/window fields and malformed fixture
accounting. They were corrected and covered by regression; two already completed Runs
were recovered read-only, never reinvoked, and have identical saved results to the
complete fixture ([references](development_runs.json)). Console decoding and shell
quoting problems were also resolved. Deliberate missing-row/later-Gate failures were
expected test conditions, not production defects. The existing Starlette warning and
historical default-cache limitation remain explicit. No production semantic defect or
authority gap was found.

Live completion is blocked by an unverified full-history resource/control envelope,
current provider permissions/history and absent genuine Workflow-bound authorization.
Credential resolution and no-Source factory isolation succeeded, but neither proves
those conditions. See [live readiness and exact next actions](LIVE_READINESS.md).
No smaller live smoke was substituted and no default cache was repaired.

The user can make this type of request in natural language without constructing JSON.
Codex must repeat discovery and owner validation, ask for missing research intent,
freeze/read back the plan and obtain separate real execution consent. This acceptance
demonstrates one fully specified request; it does not prove general natural-language
planning quality or an interactive missing-parameter dialogue. Workflow validation,
research computation, market-data completeness and full-history acceptance remain
four separate conclusions.
