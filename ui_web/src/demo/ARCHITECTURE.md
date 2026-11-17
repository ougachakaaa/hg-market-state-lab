# Demo authority routing

The canonical current design is [Demo authority](../../demo/ARCHITECTURE.md), specializing
[module authority](../../ARCHITECTURE.md) and [directory ownership](../../STRUCTURE.md).
Follow it to Bundle, collection/build, feasibility and implementation handoff contracts.

DDB-04 moved retained hash routing and workspace composition into demo/runtime.
This directory retains historical acceptance evidence. Actual capture and delivery
evidence enters the [current handoff](../../demo/build/HANDOFF.md#current-delivery-and-historical-evidence);
the earlier unverified capture state is superseded.
Current runtime, Bundle and Build behavior is owned by the canonical Demo authority.
