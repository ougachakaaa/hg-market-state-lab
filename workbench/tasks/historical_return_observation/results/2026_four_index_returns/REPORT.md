# 2026 four-index return distributions

The study describes trailing cumulative returns for four indices over inclusive ending-session dates 2026-01-01 through 2026-10-29, at horizons of 1, 3, 5 and 10 SSE trading sessions. The precise question and parameters are in [scope.json](scope.json).

All 16 Jobs and 32 analyses succeeded. Each Job contains 197 eligible observations, with zero unavailable or excluded observations, complete observation and market-fact coverage. The first anchor is 2026-01-05 and the last is 2026-10-29; the H=10 warm-up begins 2025-12-18. Full results are retained outside the repository.

Across all four indices the P5?P95 spread is wider at H=10 than H=1. CSI1000 and CSI500 have wider spreads than CSI300 and SSE50 at each requested horizon. H=10 medians range from -0.5547% for CSI1000 to -0.8747% for CSI300.

These are descriptive historical endpoint returns. Overlapping lookbacks create dependence; the results are not annualized returns, forecasts, causal findings or trading recommendations. Complete historical coverage does not establish provider-current freshness.

Cold and Warm are separate Runs for the same scope. Independent saved-export verification passed for each; all 16 observations, statistics, final public exports and input fingerprints matched. Cold used 77 provider calls; Warm used none and wrote no new cache records. The full evidence index and cache audit are retained outside the repository. The original BatchResult artifacts remain in RunStore; this report is a curated view and is not an original artifact.
