# 2026 four-index return distributions

This package describes the historical return distributions for four major indices. Start with [scope.json](scope.json) for the frozen research question and parameters, then [REPORT.md](REPORT.md) for findings and limitations, [MATRIX.md](MATRIX.md) for quantiles and [DISTRIBUTIONS.md](DISTRIBUTIONS.md) for all intervals. [results.json](results.json) retains full-precision results and coverage.

The [evidence index](evidence/evidence.json) identifies the separate Cold and Warm Runs, workflows and original artifacts; [cache audit](evidence/cache_audit.json) summarizes reuse. Original blobs remain in the local Workbench RunStore. Use `poetry run python workbench/run_store.py read --run RUN_ID` to inspect a Run and verify its registered artifacts. Repository reports are curated documents, not the original frozen report artifacts. These results grant no execution authorization. See the [results contract](../../authority/RESULTS.md).
