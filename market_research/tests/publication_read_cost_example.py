"""Synthetic local read-cost instrumentation; run from the repository root.

poetry run python market_research/tests/publication_read_cost_example.py
Timings and tracemalloc peaks are observations, not performance targets.
"""

import json
import time
import tracemalloc
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

from batch_execution_example import run
from market_research.descriptive.execution import BatchResult
from market_research.publication import PublicationStore, publish, retain_source
from market_research.publication import store as storage


def one_job(batch: BatchResult) -> BatchResult:
    plan = replace(
        batch.plan,
        subjects=batch.plan.subjects[:1],
        horizons=batch.plan.horizons[:1],
        windows=batch.plan.windows[:1],
    )
    return BatchResult(plan, batch.job_results[:1])


def inspect(store: PublicationStore, pid: str) -> dict[str, Any]:
    manifest = store.get_publication_manifest(pid)
    analysis = manifest["analyses"][0]
    view = analysis["views"][0]
    reads: list[tuple[str, int]] = []
    parsed_source = 0
    real_read, real_json = store._storage.blob, storage._json
    real_envelope = store._envelope

    def track_read(
        connection: Any, publication_id: str, group: str, identity: str, *args: Any
    ) -> bytes:
        result = real_read(connection, publication_id, group, identity, *args)
        reads.append((group, len(result)))
        return result

    def track_envelope(publication_id: str, connection: Any = None) -> Any:
        result = real_envelope(publication_id, connection)
        if connection is not None:
            reads.append(("manifest", len(storage.canonical_json(result["manifest"]))))
        return result

    source_size = manifest["source"]["size"]

    def track_json(data: bytes) -> Any:
        nonlocal parsed_source
        if len(data) == source_size and b'"schema":"research-source-v1"' in data:
            parsed_source += 1
        return real_json(data)

    operations = {
        "list": lambda: store.list_publications(limit=1),
        "manifest": lambda: store.get_publication_manifest(pid),
        "analysis": lambda: store.get_analysis(pid, analysis["analysis_id"]),
        "view": lambda: store.get_chart_view(pid, view["view_id"]),
    }
    output: dict[str, Any] = {
        "jobs": len(manifest["jobs"]),
        "analyses": len(manifest["analyses"]),
        "source_bytes": source_size,
        "operations": {},
    }
    for name, operation in operations.items():
        reads.clear()
        parsed_source = 0
        tracemalloc.start()
        started = time.perf_counter()
        with (
            patch.object(store._storage, "blob", side_effect=track_read),
            patch.object(store, "_envelope", side_effect=track_envelope),
            patch.object(storage, "_json", side_effect=track_json),
        ):
            operation()
        elapsed = (time.perf_counter() - started) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        groups = {
            name: sum(group == kind for group, _ in reads)
            for name, kind in (
                ("manifest", "manifest"),
                ("source", "source"),
                ("analysis", "analyses"),
                ("view", "views"),
                ("layer", "layers"),
            )
        }
        output["operations"][name] = {
            "record_reads": len(reads),
            "bytes_read": sum(size for _, size in reads),
            "read_groups": groups,
            "source_json_parses": parsed_source,
            "elapsed_ms": round(elapsed, 3),
            "tracemalloc_peak_bytes": peak,
        }
    return output


def main() -> None:
    batch = run("continue", inject_failure=False)
    results = []
    with TemporaryDirectory() as directory:
        root = Path(directory)
        for name, evidence in (("small", one_job(batch)), ("multi", batch)):
            source = retain_source(evidence, name, root / f"{name}.json")
            store = PublicationStore(root / name)
            pid = publish(evidence, source, "synthetic benchmark", store)
            results.append({"fixture": name, **inspect(store, pid)})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
