# R01-A offline evidence v1

Specializes [Delivery](DELIVERY.md). This is a case-specific, versioned interchange
and replay contract, not Publication V1 or a generic serializer framework.

## Package

- `inputs.canonical.json`: exact WP3 input-profile bytes and fingerprint, unchanged.
- `evidence.json`: `profile=futures_basis_report_evidence_v1`, explicit request,
  prepared acquisition attempts, observation records/resolutions/accounting,
  distributions, comparisons, persistence, definition version, runtime/code context.
- `views.json`: three complete V2 history Views and successful V1 count/frequency
  histogram Views, with deterministic identities.
- `associations.json`: point/event identities mapped to Slot-day/Contract-day/source
  references and Transition records. Analysis bindings reference retained Slot-days.
- `report-data.json`: Research-owned reader projection, including overview, exact
  numerical outputs/statuses, common dates, dropped outcomes, runs and limitations.
- `report.html`: ui_web's self-contained rendering of report-data and generic Views.
- `REPRODUCE.md`: human-readable verify/replay/generation instructions.
- `manifest.json`: profile `futures_basis_report_manifest_v1`, input fingerprint,
  status, and sorted relative file identities with sizes and SHA-256 digests.
- `SHA256SUMS`: all payload files plus manifest; excludes itself. The manifest
  excludes itself and SHA256SUMS. No absolute paths, credentials or raw exception
  text enter reader content. Diagnostic reasons in evidence are sanitized.

Evidence uses published field names, ISO dates, ordered JSON arrays and finite
round-trip JSON numbers. Binary64 input identity is preserved separately by WP3
hex-encoded canonical bytes, including signed zero. Shared observation sources
are stored once; analysis candidate/binding/dropped references are ordered
Slot-day identity arrays. Original method specs/results and failure categories
are retained verbatim as public semantic fields, including failed associations.
Runs retain references, transitions, both boundaries and observed session counts.
The operator script collects execution context and supplies it through the required
`write_evidence(..., runtime=...)` argument; Research neither invokes Node nor
reads frontend dependencies. Runtime context records Python/package/Node versions, Git revision and dirty flag,
and digests of root Python and frontend dependency locks. It is execution context,
not an input fingerprint or a claim that a dirty tree equals its HEAD.

## Reader, verification and replay

The canonical reader accepts only the WP3 profile, exactly four published Export
envelopes and their declared record fields/types. Decode the explicit binary64
markers, instantiate public Export/Row carriers, and pass exports through the
existing final-Export validation and prepared-handoff construction checks.
No service factory or ensure call is used. Re-encoded canonical bytes must match exactly.
Never import classes named by evidence, use pickle, open upstream storage or
silently upgrade unknown versions. Request validation remains WP3-owned.

Verification checks manifest shape/version, safe local regular-file identities,
complete package inventory, sizes/digests, SHA256SUMS, canonical fingerprint,
report profile and source linkage. Replay reconstructs from canonical inputs,
calls original observation/statistical APIs with retained explicit parameters,
and compares observations, ordered analyses, runs, associations, Views and reader
projection. Runtime context/acquisition attempts are retained historical metadata,
not regenerated scientific outputs. A changed or failed computation is a mismatch.

Input preparation/construction failures retain the explicit request, stage,
public category/dependency and obtained safe attempts in `failure.json`, alongside
reproduction instructions and a failure manifest. They emit no successful input
fingerprint, result or HTML; verification accepts the diagnostic package, while
replay rejects it as lacking successful inputs.

Hashes detect alteration relative to a manifest; they do not establish source
authenticity, provider freshness or independent provenance certification.
