"""Create a temporary publication from explicitly synthetic Research facts."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'market_research/tests'))
from batch_execution_example import run  # noqa: E402
from market_research.publication import PublicationStore, publish, retain_source  # noqa: E402

root = Path(sys.argv[1])
batch = run('continue', inject_failure=False)
source = retain_source(batch, 'synthetic-browser', root / 'evidence.json')
print(publish(batch, source, 'synthetic browser test', PublicationStore(root / 'publications')))
