"""Browser-only composition: real Auth/HTTP/worker, synthetic public facts."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "market_research/tests"))

from futures_basis_observation_fixtures import Services  # noqa: E402
from lab_config import futures_basis_run_root  # noqa: E402
from market_research.descriptive.cases.futures_basis import (  # noqa: E402
    FuturesBasisOnlineApplication,
    OnlineServices,
    preflight_inputs,
)
from ui_http.app import create_app as create_runtime  # noqa: E402


def create_app():
    # Explicit environment points at a temporary directory owned by the runner.
    configured = futures_basis_run_root()
    if configured is None:
        raise RuntimeError("Browser runner requires an isolated run root")
    root = Path(configured)
    services = Services()
    original = services.export

    def delayed(*args, **kwargs):
        time.sleep(0.4)
        return original(*args, **kwargs)

    services.export = delayed
    app = create_runtime()
    app.state.futures_basis_application = FuturesBasisOnlineApplication(
        root=root, services=OnlineServices(services, services, services)
    )
    def assess(request):
        readers = Services(request)
        return preflight_inputs(request, calendar_service=readers,
                                futures_service=readers, index_service=readers)

    app.state.futures_basis_preflight = assess
    return app
