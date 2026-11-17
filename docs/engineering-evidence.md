# Engineering evidence

The maintainer declares sole human project ownership from inception, Codex-generated
project code, and human direction of decisions and acceptance. Git verifies the
changes and their sequence; author metadata alone cannot independently prove that
division of responsibility. This entry connects two decisions to current reviewable
contracts, implementations and tests; it is not an execution diary.

## A — Calendar Spread: financial definition to Demo

**Problem.** Compare a near-to-far long-position roll's Close-price relationship
with comparable historical observations, consistently across daily and research pages.

**Human decision and trade-off.** The accepted
[Definition](../market_research/descriptive/cases/futures_calendar_spread/DEFINITION.md)
fixes six ordered Slot pairs, near-minus-far sign and three metrics; annualization
uses the contracts' actual last-trading-date gap. The
[relative-value contract](../market_research/descriptive/cases/futures_calendar_spread/RELATIVE_VALUE.md)
keeps same-expiry-stage and all-stage populations distinct, with samples strictly
before evaluation. This bounds descriptive interpretation and excludes strategy/timing advice.
Maintainer responsibility for choosing and accepting this scope is declared above;
the contracts independently expose what was accepted.

**Codex implementation.** The delivery can be inspected across these commits and current consumers:

| Delivery | Commit | Current evidence |
| --- | --- | --- |
| Pure financial calculation | [cb9f778](https://github.com/ougachakaaa/hg-market-state-lab/commit/cb9f778ae72cb5a331ea890b61bda99c8d8777d8) | [financial.py](../market_research/src/market_research/descriptive/cases/futures_calendar_spread/financial.py) |
| Research queries and numerical association | [6e20f1e](https://github.com/ougachakaaa/hg-market-state-lab/commit/6e20f1e4fcf6976069adaf70f46675b0250f3767) | [queries.py](../market_research/src/market_research/descriptive/cases/futures_calendar_spread/queries.py), [Statistics percentile contract](../market_statistics/EMPIRICAL_PERCENTILE.md) |
| Authenticated HTTP and generated-contract Web | [e18c52c](https://github.com/ougachakaaa/hg-market-state-lab/commit/e18c52c3dc4a494c0163665bd3c371561f2b7b1a), [29736db](https://github.com/ougachakaaa/hg-market-state-lab/commit/29736db8402c29c69ea740c4048ecb5cfa7a4954) | [HTTP contract](../ui_http/products/calendar_spread_relative_value/http-contract.md), [shared Presentation](../ui_web/src/features/calendar_spread_relative_value/components/RelativeValuePresentation.tsx) |
| Formal HTTP capture and offline consumption | [10a2743](https://github.com/ougachakaaa/hg-market-state-lab/commit/10a2743119d20a60e7ea143e49abbc96670bb58d) | [Demo integration](../ui_web/demo/CALENDAR_SPREAD.md), [static composition](../ui_web/demo/runtime/StaticWorkspace.tsx) |

**Verification.** Current [financial tests](../market_research/tests/test_futures_calendar_spread_financial.py)
check sign, units, logarithmic annualization and date spacing;
[query tests](../market_research/tests/test_calendar_spread_queries.py) check no-lookahead,
small samples and result association. [HTTP tests](../ui_http/tests/test_calendar_spread_http.py),
[Web tests](../ui_web/src/features/calendar_spread_relative_value/page/RelativeValuePage.test.tsx)
and [static tests](../ui_web/demo/runtime/calendarSpread.test.tsx) expose delivery checks.
These files establish inspectable coverage, not a fresh passing run.

**Outcome and limits.** One implemented path supplies two products and shared Online/Demo
Presentation. Demo reads captured results; no browser financial recomputation or research
execution occurs. Metadata is not proven point-in-time; small samples and historical
Close relationships do not establish realized returns or future performance.

## B — Issue #13: preparation belongs to explicit execution

**Problem.** Legal incomplete caches forced users to prepare DataLake manually before
Calendar Spread research. [Issue #13](https://github.com/ougachakaaa/hg-market-state-lab/issues/13)
records both the user feedback and the previous deliberate read-only contract.

**Human decision and trade-off.** Required-fact preparation moved into owning-case explicit
execution; [UPSTREAM](../market_research/UPSTREAM.md#execution-oriented-input-preparation)
and [Inputs](../market_research/descriptive/cases/futures_calendar_spread/INPUTS.md)
preserve read-only queries, preflight and static consumers. Synchronous requests retain
bounded shared capacity rather than introducing a durable job framework. Cold requests
can take longer; classified failures remain visible and no unconditional retry is added.

**Codex implementation.** [98b6458](https://github.com/ougachakaaa/hg-market-state-lab/commit/98b6458ed11ca66f100008fff2b1730ee129d637)
changed authority first; [e465a05](https://github.com/ougachakaaa/hg-market-state-lab/commit/e465a050fd57e92cf7f05695db8e76c08198bc88)
implemented [preparation.py](../market_research/src/market_research/descriptive/cases/futures_calendar_spread/preparation.py):
validate Export → at most one Ensure per incomplete dependency → validate final Export.
[010815f](https://github.com/ougachakaaa/hg-market-state-lab/commit/010815fedb689b04c0e673765675afd6699647d5)
connected explicit HTTP/Web submission and safe reason-specific feedback while preserving
successful result identities and financial/statistical definitions.

**Verification.** [Execution tests](../market_research/tests/test_calendar_spread_execution.py)
cover cold/hot sequencing, malformed inputs and typed failures;
[preparation acceptance tests](../ui_http/tests/test_calendar_spread_preparation_acceptance.py),
added in [0782c34](https://github.com/ougachakaaa/hg-market-state-lab/commit/0782c3440deeb3f8af24fe4750bea3b809453ed6),
exercise formal submission with real services/SQLite and controlled Source inputs.
HTTP tests cover cancellation retaining worker capacity. The
[closure comment](https://github.com/ougachakaaa/hg-market-state-lab/issues/13#issuecomment-6915917819)
reports bounded live/local acceptance and integration at
[514a233](https://github.com/ougachakaaa/hg-market-state-lab/commit/514a2335672b31c851e4358074a71c857fd7b613).
The [Actions run](https://github.com/ougachakaaa/hg-market-state-lab/actions/runs/43863311389)
linked by that comment has a successful changed-source/credential job; manual regression and Demo jobs were
skipped. CI success does not independently verify the comment's live/browser results.

**Outcome and limits.** Issue #13 is closed; explicit execution prepares missing facts
through public Dataset services, while read-only paths remain export-only. Maximum
windows, other deployment deadlines, prolonged load and cold concurrent Source behavior
remain unverified under [Application limits](../market_research/descriptive/cases/futures_calendar_spread/APPLICATION.md#operational-verification-limits).
No new runtime, business regression, browser, build or live-data checks were run for this
documentation entry; their current execution status is NOT_VERIFIED.
