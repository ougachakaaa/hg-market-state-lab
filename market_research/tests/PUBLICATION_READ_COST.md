# Publication V1 read-cost observation

Reproduce from the repository root with
`poetry run python market_research/tests/publication_read_cost_example.py`. The example
constructs a public Research Batch using explicitly synthetic market inputs, then captures
and publishes a one-Job/two-Analysis subset and an eight-Job/sixteen-Analysis Batch in
separate temporary stores. Each measurement executes once, with Python `tracemalloc`
active and payload-read instrumentation around the actual reader. File counts and bytes count
`_read` payloads, not directory opens, directory scans or `stat` calls. Time and traced peak are
single-run observations, including instrumentation overhead; they are not throughput,
process RSS, a benchmark target or a production capacity guarantee.

On the closeout environment, the following values were observed:

| Fixture | Operation | Bytes read | Files read | Source JSON parses | Time ms | Traced peak bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 Job, 2 Analyses | list | 4,479 | 1 | 0 | 2.665 | 57,276 |
| 1 Job, 2 Analyses | manifest | 4,479 | 1 | 0 | 1.797 | 52,397 |
| 1 Job, 2 Analyses | analysis | 97,860 | 3 | 1 | 13.002 | 749,360 |
| 1 Job, 2 Analyses | view | 97,668 | 4 | 1 | 10.879 | 745,628 |
| 8 Jobs, 16 Analyses | list | 26,320 | 1 | 0 | 6.238 | 186,526 |
| 8 Jobs, 16 Analyses | manifest | 26,320 | 1 | 0 | 5.982 | 180,087 |
| 8 Jobs, 16 Analyses | analysis | 881,265 | 3 | 1 | 96.824 | 6,479,309 |
| 8 Jobs, 16 Analyses | view | 881,073 | 4 | 1 | 114.122 | 6,479,981 |

The respective retained source sizes were 92,346 and 853,910 bytes. Both list and
manifest read only the selected Manifest envelope; the measured analysis read loads its
Manifest, entire copied source, and selected Analysis file; the View read loads its
Manifest, entire copied source, selected View definition and selected Layer file. Tests
assert these file counts and source parses, including absence of unrelated Analysis/Layer
file reads. The source is parsed completely: it itself contains all Jobs and outcomes,
even though unrelated standalone Analysis payload files are not loaded.

Every detailed read currently rereads, hashes and parses the entire retained source and
validates all source associations. Its cost grows with the full source size and expanded
JSON object graph, not merely the selected Analysis or Layer. Python object allocations
make peak memory exceed raw bytes; `tracemalloc` does not include all process/native memory.
The manifest and source-association verification perform linear scans for each analysis,
so their matching work can be quadratic in Analysis count in addition to source-byte and
nested-evidence comparison costs. Listing scans and sorts the whole publication index,
then verifies up to `limit` complete Manifests; the limit bounds returned records, not
index scanning or each Manifest's size. These are implementation observations for WP3's
capacity and deployment decisions, not a new semantic contract. This closeout adds no
cache, index, splitting or performance guarantee and does not weaken integrity checks.
