"""Reproducible synthetic-data acceptance; no network or default market cache.

Run: poetry run python market_research/tests/publication_example.py
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from batch_execution_example import run
from market_research.publication import PublicationStore, publish, retain_source
from market_research.publication.visualization import validate_view


def main() -> None:
    # The controlled services in batch_execution_example use artificial market facts.
    batch = run("stop", inject_failure=True)
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = retain_source(batch, "synthetic-batch", root / "evidence.json")
        store = PublicationStore(root / "publications")
        with (
            patch(
                "market_research.descriptive.execution.batch.execute_job",
                side_effect=AssertionError("execution forbidden"),
            ),
            patch(
                "market_research.descriptive.execution.api.compute",
                side_effect=AssertionError("compute forbidden"),
            ),
            patch(
                "market_research.descriptive.execution.api.prepare_inputs",
                side_effect=AssertionError("acquisition forbidden"),
            ),
        ):
            pid = publish(batch, source, "synthetic test data", store)
            reader = PublicationStore(root / "publications")
            manifest = reader.get_publication_manifest(pid)
            sample = next(a for a in manifest["analyses"] if a["views"])
            analysis = reader.get_analysis(pid, sample["analysis_id"])
            view = reader.get_chart_view(pid, sample["views"][0]["view_id"])
            validate_view(view)
        print(
            json.dumps(
                {
                    "source": "synthetic test data",
                    "publication_id": pid,
                    "batch_status": manifest["status"],
                    "job_count": len(manifest["jobs"]),
                    "analysis_count": len(manifest["analyses"]),
                    "analysis_id": analysis["summary"]["analysis_id"],
                    "analysis_status": analysis["summary"]["status"],
                    "layer_type": view["layers"][0]["layer"]["type"],
                    "mark_count": len(view["layers"][0]["layer"]["data"]),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
