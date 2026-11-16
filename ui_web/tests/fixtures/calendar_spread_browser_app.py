"""Composed FastAPI/Auth with synthetic public Research inputs; no real market cache."""
import sys
from pathlib import Path
from ui_http.app import create_app as composed_app
from ui_http.products.futures_calendar_spread.endpoint import get_daily_query
from ui_http.products.calendar_spread_relative_value.endpoint import get_historical_query
from market_research.descriptive.cases import futures_calendar_spread as case

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'market_research/tests'))
from calendar_spread_fixtures import Services  # noqa: E402


def daily(code, day):
    services = Services(day, day, code)
    return case.query_daily_spreads(code, day, calendar_service=services, futures_service=services)


def history(code, start, end, **kwargs):
    services = Services(start, end, code)
    return case.query_historical_relative_value(code, start, end, calendar_service=services, futures_service=services, **kwargs)


def create_app():
    app = composed_app()
    app.dependency_overrides[get_daily_query] = lambda: daily
    app.dependency_overrides[get_historical_query] = lambda: history
    return app
