# WB-06 acceptance scope and procedure

Acceptance evidence, not new Task or business authority. Commissioned by the WB-06
user request on 2026-10-29 (Asia/Shanghai). Baseline: `develop`,
`2611c18e21208282f3b7da130e67160998816509`; initially clean. Task v1 is unchanged.

The declared completion scope is natural-language planning and deterministic isolated
G1/G3/G4/G5 integration, output inspection, historical read-back and problem reporting.
Full-history live research is a separate, conditional acceptance: BLOCKED unless both
operational controls and genuine exact-workflow user consent are established. The Goal
does not authorize live acquisition. G2/G6 remain explicitly SKIPPED.

The Agent first interpreted the fully specified synthetic research request supplied
in WB-06, then ran the official G1/G3 recorders against a backend launched from this
checkout on isolated loopback port 18061. The actual catalog contained one supported
capability, `trailing_cumulative_return_v1`. Only after reading its returned descriptor
did the Agent author [candidate.json](candidate.json) directly. No existing Candidate
JSON was loaded, copied or modified to produce this candidate. Reading older acceptance
tests informed interface usage, not the research parameter selection.

The request supplies index, H, inclusive dates, metric, parameters, analyses, unit and
failure policy. No clarification or market default is needed. The Agent assigned only
the nonsemantic request IDs `wb06_quantiles` and `wb06_intervals`. The full window needs
the public Python surface because HTTP POST has a 93-day limit. No partitioning occurs.

The test-only [harness](../../../tests/wb06_e2e_example.py) accepts that candidate and
an already discovered Run, freezes through G4, independently reads it in a fresh
process, and exercises ordinary G5 through the existing isolated simulated-host helper.
The helper's generated approval is **test simulation only**, never real consent. It is
active only with public Calendar/Index fakes and forbidden sockets/SQLite. Production
G5 has no synthetic execution seam. Actual Research and Statistics implementations run.

Fixture Calendar facts cover every natural day requested. Its open-session schedule
is explicitly artificial (weekdays, ignoring exchange holidays); close values are
`80 + ((7*i) % 41)` for ordered fixture sessions beginning 2009-12-01. This is not SSE
history. One primary complete fixture and one deliberately missing-row diagnostic
preserve the full requested window and H=10. The independent oracle derives returns
from saved public Exports and separately verifies Type 7 and bin membership. No
fixture values are described as market observations.

Acceptance additionally appends an expected, test-injected G3 FAIL after completion,
checks current G4 ineligibility, and verifies the original result survives fresh-process
G5 read-back without any invocation. A separate planning-only Run tests absent consent:
G5 must BLOCK before intent with no Research call. This supplies no live execution proof.

Original results stay in ignored `workbench/.runs/` under the shared Storage contract.
Commit only public summary/reference artifacts, this procedure, the authored candidate,
problem log and human report. Preserve all failure attempts and their dispositions.
No new Gate, public semantics, calculation, planner or business source change is intended.
