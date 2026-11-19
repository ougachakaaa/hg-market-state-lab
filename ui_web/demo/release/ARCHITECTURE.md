# Release Requirements authority

Specializes [Demo](../ARCHITECTURE.md) and [deployment](../../deploy/ARCHITECTURE.md).
`requirements.json` declares required publication content, independently of Presets.
Its closed schema is `requirements.schema.json`. Registry and formal feature validators
remain the sole owners of Bundle membership and business DTO admission.

Each registered Bundle has an exact request selection and a content policy. Initial
Basis/backtest actual coverage starts 2026-03-02 and ends 2026-09-30. Dates must be
ordered, unique and inside request bounds; no fixed session count or calendar padding
is imposed. Producer coverage must be complete. Backtest dates agree with Basis's
formal candidate domain; View dates must belong to that domain. At least one finite
plotted value is required. Formal validation precedes these additional requirements.
No financial metric or external trading calendar is recomputed. Captured evidence
cannot independently prove provider authenticity; source disclosure stays truthful.

Catalog must contain a real capability with all corresponding details. Complete empty
Publication captures are permitted. No release action collects or fabricates data.
Requirements changes must be committed to main before publication. Their identity is
the SHA-256 of exact committed bytes, retained in the release gate evidence outside
the site with source SHA, Manifest identity and existing Artifact Receipt.

`npm run demo:release-check` validates requirements, admission and required content,
then public safety, the existing offline build and Receipt scan/verification. Any
failure returns nonzero and invalidates prior release evidence. The publisher runs it
in a clean checkout of the exact remote-main candidate; CI runs it independently.
Receipt source identity covers `ui_web/` and the canonical map and schema
referenced by the [Strategy Research Map contract](../../../docs/strategy-research/MAP_CONTRACT.md).

Agent intent, integration and recovery steps enter the [Release Runbook](RUNBOOK.md).

## WP7 Calendar Spread predicates

Daily requires the exact preset date/product, an open session and six valid actual
contract/metric rows. Research requires the exact request, valid current observations,
all six pairs' complete historical series, at least 30 all-stage samples per pair,
Quantile, current Percentile and nonempty matching-stage comparison. All history is
strictly before evaluation. Small matching-stage populations retain their warnings.
These additional content predicates never change business availability definitions.
Histogram remains optional and is rendered only when actually captured.
