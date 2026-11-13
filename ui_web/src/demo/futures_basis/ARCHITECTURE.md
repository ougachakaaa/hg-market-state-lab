# Futures Basis static demo data

V1 fixture authority and historical WP3/WP4 implementation record. The target multi-page
architecture is now owned by [Static Demo V2](../ARCHITECTURE.md), with its
[Example contract](../EXAMPLES.md). One-page/no-router/independent-shell statements below
describe V1 only; V2 shares the formal shell and all seven business surfaces. The V1
fixture profile/window remains unchanged. Historical acceptance is not V2 evidence.

Specializes [ui_web](../../../ARCHITECTURE.md), the
[R01-A delivery](../../../../market_research/descriptive/cases/futures_basis/DELIVERY.md)
and the shared [Futures Basis reader](../../features/futures_basis_research/ARCHITECTURE.md).
It owns one small, versioned, publicly committable demo fixture and its static
consumption contract. It is not an application feature, HTTP product, Publication or
new Research capability, and it never executes Research, acquires facts or calculates
financial values.

## Data source and generation

The committed [`report.v1.json`](report.v1.json) is producer output over deterministic
synthetic public facts. [`market_research/scripts/futures_basis_demo_fixture.py`](../../../../market_research/scripts/futures_basis_demo_fixture.py)
builds a 44-session IM window (2024-09-02 through 2024-10-31) with the fixed active-month
structure, a deterministic discount/premium cycle and real-format contract identities,
then runs the unchanged `prepare_inputs` → `construct_observations` → `compose_report`
path with the canonical `standard_report_request`. The reader projection comes from the
existing producer `scientific_payload`. No Tushare token, dataset cache, provider call or
network access is involved, so public redistribution needs no market-data permission.

Regenerate and verify from the repository root:

```bash
poetry run python market_research/scripts/futures_basis_demo_fixture.py
poetry run python market_research/scripts/futures_basis_demo_fixture.py --check
```

The fixture must not be edited by hand. The generator is deterministic; a change to the
synthetic facts or analyst profile is a new fixture revision, not an incidental edit.

## Fixture contract

The envelope profile is `futures_basis_demo_fixture_v1`:

| Field | Meaning |
| --- | --- |
| `fixture_profile` | Demo envelope version; incompatible changes require a new profile and file name. |
| `classification` | Always `synthetic`; a real-data fixture would need a new authority decision. |
| `generated_by` | Repository-relative generator path for traceability. |
| `report_profile` | Always `futures_basis_report_evidence_v1`. |
| `disclosure` | Human-readable `label`, `data_source` and `notice` for the demo surface. |
| `report` | The unchanged `futures_basis_report_evidence_v1` reader projection. |

`report` keeps every scientific field, chart View, transition, coverage counter,
limitation and input fingerprint as produced. Two producer fields are intentionally
not carried verbatim: `sources` is replaced by an explicit Synthetic Demo provenance
label, and `runtime` is omitted because this fixture is not a sealed computation
evidence package. No other field may diverge; the Python test compares the committed
reader with a fresh producer projection.

`report` must pass the shared `validateReportData` reader validation, including the
[V2 date-series contract](../../../VISUALIZATION_V2.md) for history and
V1 categorical Views for histograms. The demo does not introduce a second DTO, a
parallel schema, a mock API or browser-side financial computation.

## Disclosure and consumption

- The static demo must show `disclosure.label` and `disclosure.notice` next to the
  report. The data is synthetic and is not real market data, trading performance or
  investment advice.
- The report has no adjacent `evidence.json`, `inputs.canonical.json`, manifest or
  SHA256SUMS. Demo presentation must not claim a sealed offline evidence package or
  link to files that do not exist.
- WP3 consumes the fixture through [`fixture.ts`](fixture.ts), which validates at
  import time and exports `futuresBasisDemoFixture`. Importing the module performs no
  fetch, authentication or backend call.
- Rendering reuses the shared `Report` reader and ChartView; the demo must not fork a
  second report component or recompute Basis, annualized Basis, Quantile, distribution,
  PnL or any other financial value.

## Public safety

The committed JSON contains no token, credential, cookie, local path, runtime machine
metadata, private dataset or redistributable market data. Tests scan the fixture for
credentials and local paths and pin the section coverage; review any regeneration diff
before commit.

This V1 fixture owns one case only. V2 MO Option Chain, MO Premium Plane and Backtesting
Examples follow the parent Example contract and their existing feature/producer authorities;
this fixture does not define their business semantics.

## Static presentation entry (WP3)

The independent `index.html` / `main.tsx` entry composes the shared application
Ant Design theme, a public introduction, fixture disclosure, shared six-section
Reader and repository/documentation links. It imports neither the authenticated
application shell nor HTTP clients and reads no authentication state. All assets
are bundled locally; no CDN, remote font, mock server or business request is allowed.

The fixture is loaded through a dynamic import of `fixture.ts`: import-time
validation failures show a visible error instead of mounting report results.
Loading shows only a pending message; reader rendering failures have their own
error boundary. The reader's `demo` evidence copy describes static delivery:
it makes no claim to an online HTTP response or adjacent sealed evidence files.
Disclosure label, notice and data_source are consumed verbatim above the report;
a compact synthetic label stays visible while scrolling, with the full notice
available through its anchor. In demo mode, narrow screens scroll the shared
chart frames horizontally to preserve readable labels; chart semantics do not change.

`vite.demo.config.ts` owns the standalone build, fixed `/hg-market-state-lab/`
base and ignored `dist-demo/` output. There is one page, no router and no change
to production app routes, auth, proxies or build. Building needs only npm dependencies
and the committed fixture, never Python, a token or fixture generation.
Usage and deployment: [Demo guide](README.md#deployment-guide-wp4).

## Static deployment boundary (WP4)

[Pages workflow](../../../../.github/workflows/deploy-demo-pages.yml) builds only
this entry with Node 22 and the committed fixture. Pushes to the existing
`feat/github-pages-demo` branch deploy only the contents of `ui_web/dist-demo/`
to the `github-pages` Environment using the standard GitHub token and OIDC.
No Python, fixture regeneration, secret or application runtime is part of delivery.
The repository Pages Source must be GitHub Actions; existing Environment protection
must be respected. Public availability requires a successful deployment and separate
public HTTP/browser acceptance, never inferred from a local preview.
The former WP5 eventual-trigger plan is superseded: V2 D7 owns the reviewed trigger
change to `main` under the parent release authority. Until D7, the current branch trigger
is an implementation fact, not the long-term release policy.

## V1 cross-platform regression comparison (WP-C)

The retained JSON remains byte-for-byte historical evidence. Generation still emits
unchanged producer values. `--check` verifies canonical JSON serialization and exact
structural/scientific equality except finite `y` values in the annualized history
View: platform libm `log` can differ at binary64 rounding boundaries. These values
may differ by at most two ULPs, with no absolute floor. Each corresponding `结果`
detail must equal `repr` of its own point value before comparison. All other detail
text, dates, identities, input fingerprint, statistics, nulls and Views remain exact.
This tolerance belongs only to V1 fixture regression; it changes neither financial
computation nor sealed Evidence/Result digests or real-market admission.
