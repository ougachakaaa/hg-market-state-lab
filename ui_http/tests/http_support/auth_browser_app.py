"""Loopback browser fixture: real Auth, deterministic product public providers.

Only the explicit browser verification command imports this test factory. Runtime
composition is unchanged; no market Source or default market cache is touched.
"""

from fastapi import FastAPI

from data_snapshot.products.mo_option_premium import service
from http_support.fake_chain_service import FakeChainReadProvider
from test_mo_option_premium_api import premium_plane
from ui_http import create_app as create_runtime
from ui_http.products.mo_option_chain.endpoint import get_chain_read_provider
from ui_http.products.mo_option_premium.endpoint import get_premium_plane_provider


def create_app() -> FastAPI:
    application = create_runtime()
    application.dependency_overrides[get_chain_read_provider] = lambda: FakeChainReadProvider()
    application.dependency_overrides[get_premium_plane_provider] = lambda: (
        lambda query: service.PremiumPlaneResult(plane=premium_plane())
    )
    return application
