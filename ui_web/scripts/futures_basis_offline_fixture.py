"""Generate a normal offline regression report using synthetic public facts only."""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "market_research/tests"))

from market_research.descriptive.cases.futures_basis.evidence import write_evidence  # noqa: E402
from test_futures_basis_report import report  # noqa: E402

if __name__ == "__main__":
    output = Path(sys.argv[1]).resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Synthetic reports must use external temporary storage")
    output.mkdir(parents=True, exist_ok=False)
    context = runpy.run_path(str(ROOT / "market_research/scripts/futures_basis_report.py"))
    write_evidence(report(), output, runtime=context["runtime_context"]())
