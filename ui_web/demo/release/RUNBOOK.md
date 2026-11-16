# Demo Release Agent Workflow

## Ownership and entry

This Runbook owns Agent execution, source integration and recovery. Read inherited
[Agent rules](../../AGENTS.md), [deployment authority](../../deploy/ARCHITECTURE.md)
and [Release Requirements](ARCHITECTURE.md). Stable publication invariants belong to
deployment authority, content constraints belong to Release Requirements, and CLI
usage belongs to the [release guide](../../deploy/README.md#verified-demo-pages-release-ddb-06).
Retain one Publisher, one Pages workflow, one Requirements file, one active Bundle
dataset and the single deployment branch `release/demo-pages`.

## Intent and authorization

Recognize “发布最新静态 Demo”, “发布 Demo”, “按照 XXX 分支发布静态 Demo”,
“把 XXX 分支发布到 Demo Pages” and “使用 XXX 的最新版本更新作品集” as release requests.
XXX selects the source branch. Without XXX select fetched remote main. Never infer
the current feature HEAD as the source. “检查是否可以发布” and “预览发布内容” authorize
inspection and candidate checks only. Keep all formal branch refs unchanged for those requests.

A release request authorizes the deterministic integration and publication steps below
without repeated approval. Business choices, ambiguous conflicts, changed release content
and permission changes require the user's decision at the stop boundary.

## A. Resolve and record source

1. At repository root record `git branch --show-current`, `git rev-parse HEAD`,
   `git status --short` and `git remote -v`. Select the configured GitHub remote,
   default `github`, and fetch it. Resolve the requested branch to its full fetched SHA.
2. Compare local and fetched source, develop, main and release refs. Inspect untracked
   files, uncommitted changes and unpushed commits. Missing or ambiguous source, local/remote
   drift requiring a version choice, uncommitted changes or unpushed commits require a stop.
   Do not stash, reset or choose a version implicitly.
3. Record merge bases, ancestor relationships, complete candidate diff and commit range
   relative to main and develop. Explain all commits that integration would include.
   If main already contains the source plus additional commits, ask which scope to release.
   Also escalate additional target-branch changes whose inclusion makes the requested scope unclear.
4. Record source SHA separately from the eventual integration/release SHA. Re-fetch and
   compare recorded refs before each formal branch advancement. Changed refs require
   renewed scope inspection and candidate checks. A version choice requires user input.

## B. Prepare and integrate the candidate

The integration policy is feature → develop with `--no-ff`, develop → main with
`--ff-only`, and main → release/demo-pages with FF-only publication through the Publisher.
Never force push, rewrite history or resolve a semantically ambiguous conflict automatically.

For a feature source, inspect its complete diff and merge base first. Create an isolated
temporary integration branch/worktree from the recorded develop SHA. Merge the exact
source SHA with `git merge --no-ff`, retaining the resulting merge commit as the candidate.
If the source is already integrated, use the existing integration commit after resolving
any scope ambiguity. Perform authority reconciliation and Phase C on this candidate
before changing develop or main. Semantic reconciliation requiring a new decision stops here.

After PASS, verify refs have stayed unchanged. Advance develop to that exact tested merge
commit with FF-only movement, then advance main with `git merge --ff-only` to the same SHA.
Use normal explicit-ref pushes to update develop and main, rechecking remote state before
each push. Never recreate the tested merge commit during promotion. Respect existing
branch protections. A rejection requires a stop and a report of any partial advancement.

For develop source, require main to be its ancestor, check the exact develop SHA in an
isolated checkout, then FF-only advance main and push normally. For main source, use its
exact fetched SHA directly. The Publisher requires local main, when present, to equal
remote main. Confirm this alignment after promotion.

Source integration is an Agent Git operation. The Publisher accepts only `--remote NAME`
and always selects remote main. It has no source-branch argument or integration mode.

## C. Release Preflight on the actual candidate

Run commands from the candidate checkout's `ui_web` directory using its locked npm
dependencies. Record the exact HEAD and inspect Requirements against the user's approved
content. Run `npm run demo:release-check`. Its existing validators check the seven
registered Bundles, exact request selections, complete formal Results, actual observation
coverage, meaningful plotted values, Manifest/hash/tracked identity, Public Safety,
offline build and Artifact Receipt. Keep content details in `requirements.json` and its
authority. Diagnose a mismatch with Bundle ID, field, actual value and required value.

The release-check command does not execute browser acceptance or Git promotion checks.
After it passes, invoke the existing eight-page acceptance helper in that same checkout
against its freshly built local artifact.

```powershell
node --input-type=module -e "import { verifyBrowser } from './demo/build/browserAcceptance.mjs'; await verifyBrowser()"
```

This exercises eight hash routes, expected results/charts, read-only local interactions,
history and network/runtime errors. Check main ancestry and release FF eligibility
separately. Every part must pass before publication. Unavailable prerequisites are
NOT VERIFIED and prevent publication until resolved. This complete release acceptance
is specific to an explicit release request. Ordinary development follows scoped verification.

On any failure, keep release/demo-pages unchanged. Do not recollect market data, change
Requirements, relax validators or change financial calculations to obtain PASS. Ask the
user to decide the correction when content or semantics differ.

## D. Publish through the existing entry

After integration, verify the approved candidate is remote main and recheck its scope.
Run `npm run demo:publish`, or `npm run demo:publish -- --remote NAME` for an explicitly
selected GitHub remote. Never substitute a direct release-branch push or another workflow.

The Publisher checks GitHub permissions, Pages/Environment settings, relevant dirty
sources, local-main drift, release ancestry and concurrent runs. It gates a clean detached
remote-main checkout, records its SHA, rechecks remote refs and pushes only that SHA normally.
It then waits for Actions, verifies downloaded artifacts and actual public file bytes
against the CI Receipt, and executes the existing browser acceptance helper on Pages.
Its remote-ref recheck detects changes during its own preflight. Record the selected SHA
and compare it with the approved candidate. A changed main before invocation requires
renewed source-scope review. Remote main has no atomic lock across Agent and Publisher
steps, so coordinate concurrent main updates before starting publication.

## E. Remote acceptance and result

Continue through the build job, Requirements gate, artifact verification, deployment job,
successful deployment URL, public receipt verification and eight-page browser acceptance.
Retain Actions URL, deployment URL, exact source/release SHA, Requirements hash, Manifest
hash and evidence paths. A standalone gate writes ignored `.build/demo-release.json`.
The Publisher copies its temporary gate evidence into the invoking checkout's ignored
`.build/demo-publish.json` before cleaning up its temporary checkout. CI evidence has
finite retention. These evidence files remain outside the site.

Report `RELEASED_AND_VERIFIED` only after actual Pages and online acceptance pass.
Report the precise failed stage otherwise, including whether a release push occurred.
Local build or release push success alone cannot establish completion.

## Stop and escalation

Stop for ambiguous source/scope, local/remote version choices, semantic merge conflicts,
substantive authority/implementation conflicts, Requirements/Bundle mismatch, absent or
incomplete formal Results, required market-data regeneration or formal-content changes,
non-FF divergence, permission/Environment/protection rejection, CI failures requiring
recovery decisions, or unexpected online results.

Provide the current phase, failed check, evidence and cause, feasible options, recommended
option and exact develop/main/release refs already advanced locally and remotely. Ask a
specific decision question and resume from the interruption after the answer. Keep recovery
within the requested release scope. Never weaken protections to proceed.

## Idempotency and recovery

- If the candidate is already release HEAD, inspect its existing run and deployment evidence
  and verify current Pages acceptance. Report `ALREADY_PUBLISHED` once verified. The existing
  Publisher rechecks that candidate without pushing or implicitly rerunning the workflow
  and emits `RELEASED_AND_VERIFIED`. The Agent maps this verified unchanged-release case
  to `ALREADY_PUBLISHED`. Missing/expired artifacts leave acceptance NOT VERIFIED.
- If already pushed with a failed or missing deployment, inspect the existing run and failure.
  Propose the precise recovery action. Obtain explicit rerun authorization when needed.
  Never create empty commits to trigger publication.
- If develop/main advanced before a later gate or deployment failure, report their exact
  updated refs. Preserve history and wait for the recovery decision.
- On `demo-publish.lock`, resolve the absolute Git common directory using
  `git rev-parse --path-format=absolute --git-common-dir`. Confirm there is no active
  Publisher before removing only that exact empty lock directory. Inspect leftover
  Publisher-owned worktree registration and paths before precise cleanup under existing
  deployment rules. Preserve user worktrees, Bundles and market caches.
- Publisher polling is bounded. On timeout retain SHA/run evidence and inspect that same
  run before choosing recovery. A timeout does not establish successful deployment.

## Final report

Report requested source branch and full SHA, tested integration/release SHA, all advanced
refs, gate and page acceptance outcomes, Actions/deployment URLs, evidence paths and final
status. Mark every unavailable or unrun check NOT VERIFIED. Include any pending recovery
decision. A check-only request ends with its inspection results and unchanged formal refs.
