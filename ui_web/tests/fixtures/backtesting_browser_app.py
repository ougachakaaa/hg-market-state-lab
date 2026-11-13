"""Real HTTP/Auth/worker with accepted synthetic public-service fixtures only."""
import sys
import time
from pathlib import Path

from lab_config import backtesting_run_root
from market_backtesting.cases.futures_roll_long import create_futures_roll_online_application
from ui_http.app import create_app as create_runtime

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "market_backtesting/tests"))
from public_input_fixtures import fake_services  # noqa: E402


class DelayedService:
    def run(self, request):
        time.sleep(5)
        return fake_services()[0].run(request)

    def preflight(self, request):
        return fake_services()[0].preflight(request)


def create_app():
    configured = backtesting_run_root()
    if configured is None:
        raise RuntimeError("Browser runner requires an isolated run root")
    app = create_runtime()
    app.state.backtesting_application = create_futures_roll_online_application(
        root=Path(configured), service=DelayedService()
    )
    return app
