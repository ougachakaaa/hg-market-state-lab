# Demo Bundle contract

Specializes [Demo authority](ARCHITECTURE.md). Formal DTO fields and meaning remain owned
by the [HTTP product contracts](../../ui_http/HTTP_PRODUCTS.md) and their business owners.

## Envelope

Each Bundle is a closed JSON object with the following required fields.

| Field | Current meaning |
| --- | --- |
| `bundle_format` | Literal `demo_bundle_v1`, the current structural format |
| `bundle_id` | Exact registered ID |
| `preset_id` | Exact registered Preset ID, initially equal to Bundle ID |
| `request` | Formal query/body identity, or the composite selection described below |
| `result_contract` | Exact Registry contract reference |
| `source` | Closed object with `kind` equal to `formal_http` and nonempty `description` |
| `result` | Complete formal response or static assembly defined in the Registry table |

Format identifiers describe the current structure. Only the current identifiers are
accepted. Source descriptions state actual HTTP capture and relevant provenance limitations.
Secrets, Cookie values, credentials and machine-local paths stay outside committed data.
Source descriptions cannot assert unverified provider authenticity or publication rights.

## Registry, Presets and active data

`demo/build/registry.ts` is a small static table owning required IDs, exact paths,
Preset association, contract reference and validator dispatch. All seven rows below are
required. The Python Collector consumes this table through the offline Node tooling's JSON
registry export, keeping one machine-readable registry owner. No plugin discovery is needed.

`demo/build/presets.json` maps each `preset_id` to `{request}`. It records explicit
formal query/body inputs. Initial Basis and Backtesting requests use IM, 2026-01-01 through
2026-11-11. M1/Q1 have independent strategy profiles. Chain and Premium use MO,
2026-11-11 and explicit close prices. Catalog uses `{}` and Publications uses
`{limit: 50}`. These selections are committed with DDB-02. There are
no implicit latest-date choices. M1/Q1 requests have their respective strategy fixed.

`demo/bundles/manifest.json` is the only active Manifest. It is a closed object with
`manifest_format` equal to `demo_manifest_v1` and `bundles`, an array of closed entries
`{bundle_id, path, sha256}` sorted by Bundle ID. Paths are relative to `demo/bundles/` and
must equal `<bundle_id>.json`. SHA-256 is exactly 64 lowercase hexadecimal characters.
The Manifest records current bytes. Registry owns expected capability and required membership.

| ID | Feature owner | `result_contract` | Envelope request and result |
| --- | --- | --- | --- |
| `chain` | `mo_option_chain` | `mo_option_chain:OptionChainDTO` | Request query; result is full 200 body |
| `premium` | `mo_option_premium` | `mo_option_premium:PremiumPlaneResponse` | Request query; result is full 200 body |
| `basis` | `futures_basis_research` | `futures_basis_research:FuturesBasisReportResponse.data` | Immutable response request; result is full response data |
| `catalog` | `research_catalog` | `research:CapabilityDescription[]+CapabilityDescription` | Request `{}`; result `{list, details}` of complete HTTP DTOs |
| `publications` | `research_explorer` | `research_publication:PublicationList+Manifest+Analysis+ChartView` | Request `{limit: 50}`; result `{pages, manifests, analyses, views}` |
| `expiry_to_M1_v1` | `backtesting` | `backtesting:FuturesRollResultResponse.data` | Immutable response request; result is full response data |
| `expiry_to_Q1_v1` | `backtesting` | `backtesting:FuturesRollResultResponse.data` | Independent immutable response request and full response data |

Contract references are exact dispatch identities anchored to existing generated contracts,
not remote URLs to fetch during build. Basis/Backtesting Presets contain the formal submit
body. Their Bundle requests contain the richer immutable identity returned by HTTP.
Collector and Build compare shared request fields and server-owned case/profile identity
through existing formal validators. They preserve result fields, nested timestamps, decimal
values, arrays, nulls and zero values. Outer run_id and lifecycle timestamps are omitted.
Basis outer result_status is checked against data.status before extraction.
MO Presets record resolved price_type explicitly so the returned query identity can be
compared directly. Catalog details must equal their matching complete list descriptors.
Publication arrays retain collection order, with details fetched in formal reference order.

Catalog details cover every ID in the complete list. Publications pages retain full list
responses including opaque cursors. Manifests/analyses hold the complete response `data`;
views hold `{publication_id, view_id, view}` with the complete View response `data`.
IDs come from formal references. Every listed publication has one Manifest, every declared
Analysis has its detail, and every referenced View has its payload. Pagination ends at a
real null cursor. Empty formal lists remain valid empty captures, with one terminal page
for Publications. HTTP reading never creates Publications.

## Admission and exact bytes

Reject duplicate JSON keys, duplicate IDs/paths, missing required IDs, unknown IDs, extra
active Bundle JSON, extra envelope/Manifest fields, unsupported formats and mismatched
Registry/Manifest/Envelope/Preset/contract identities. Require exactly the registered files
and Manifest in the active directory. Reject absolute paths, parent traversal, alternate
separators, symlinks/reparse points and any resolved target outside the active directory.

Generation serializes strict JSON as UTF-8 without BOM, recursively sorted object keys,
two-space indentation, LF line endings and one final LF. Array order and decoded business
values are preserved. Nonfinite numbers are rejected. DDB-03 must preserve numeric values
without lossy coercion when parsing/serializing HTTP JSON, including unknown nested fields.
Hash covers all final Bundle bytes, including the final LF. Build hashes original bytes
before decoding and checks canonical formatting using equivalent lossless JSON rules.
The Manifest is serialized by the same rules and has no self-hash.

DDB-02 uses Number-compatible numeric admission. Every JSON numeric token, including
unknown nested fields, must retain its exact decimal value after Number conversion and
JSON serialization. Unsafe integers, overflow, underflow and rounded decimals fail
admission. Ordinary decimal values such as 0.1 remain valid when their decimal round trip
is unchanged. Signed zero is rejected because serialization loses its sign. Numeric strings
remain strings. Object keys use UTF-16 lexical order and numeric tokens use JSON.stringify
formatting after this check. Canonical serialization explicitly orders even integer-like
object keys. Build checks UTF-8 decoding strictly and rejects BOM.

Single-Bundle generation replaces only the selected Bundle and its Manifest entry. Other
Bundle files and their hashes remain byte-for-byte unchanged. Registry entries are ordered
by Bundle ID, matching Manifest entry order independently of collection order. Full generation publishes only
after every required capture passes admission. Transaction rules belong to
[build authority](build/ARCHITECTURE.md#dataset-update-transaction).

Adding a Bundle updates this catalog, Registry, Preset, formal validator dispatch and
runtime route/composition as needed, then captures its data and extends the single Manifest.
Existing unrelated Bundles need no regeneration. A business-contract change first follows
the feature's [contract feedback loop](../contracts.md).

## Offline admission interface

Run `npm run demo:check -- --dir <directory>` from `ui_web`. The default is
`demo/bundles/` resolved relative to the tool. Success prints PASS and exits zero.
Failure prints a registered Bundle ID (or `dataset`), stage and fixed safe reason, and
exits nonzero without echoing payloads or filesystem exception messages.
`npm run --silent demo:registry` emits the static Registry as JSON for Collector consumption.
Tool compilation uses the existing npm Vite toolchain and ignored `.build/demo-tools/`.
Windows additionally uses its built-in PowerShell filesystem attributes to reject all
reparse tags, including tags Node does not expose as symbolic links. Attribute-check
failure rejects admission. Other platforms use lstat and resolved-path checks.
Admission reads local bytes only. Dataset locking, transaction recovery and build staging
remain assigned to DDB-03/DDB-04. Callers must supply a quiescent input directory for DDB-02.
Focused tests run with `npx vitest run --config demo/build/vitest.config.ts`.
The tool's type check is `npx tsc -p demo/build/tsconfig.json`.
