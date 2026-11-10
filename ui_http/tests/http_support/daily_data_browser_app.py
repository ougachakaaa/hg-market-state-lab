"""Daily Data browser acceptance only: real Auth, synthetic public results.

No Source, market cache or production auth database is used. Metric values are
fixture facts; the frontend must export them without recalculation.
"""

from dataclasses import replace
from datetime import date

from fastapi import FastAPI

from data_snapshot.products.mo_option_chain import service as chain
from data_snapshot.products.mo_option_premium import service as premium
from http_support.fake_chain_service import chain_fixture
from ui_http import create_app as create_runtime
from ui_http.products.mo_option_chain.endpoint import get_chain_read_provider
from ui_http.products.mo_option_premium.endpoint import get_premium_plane_provider


def chain_result(query: chain.ChainQuery) -> chain.ChainReadResult:
    original = chain_fixture()
    extra = chain.ExpiryGroup(
        expiry_date="2026-10-23",
        futures=None,
        calls=(chain.OptionPoint("MO2610-C-9000.CFE", 9000.0, 12.3456789012345),),
        puts=(chain.OptionPoint("MO2610-P-7400.CFE", 7400.0, 0.0),),
    )
    return chain.ChainReadResult(
        chain=replace(
            original,
            target_trade_date=query.target_trade_date,
            price_type=query.price_type,
            expiries=(*original.expiries, extra),
        )
    )


def premium_result(query: premium.PremiumPlaneQuery) -> premium.PremiumPlaneResult:
    observation = premium.ObservationAnchor(query.as_of)
    underlying = premium.UnderlyingReference("000852.SH", 7300.0)
    points = []
    reference = premium.FuturesReference("IM2609.CFE", 7290.0)
    for expiry, side, strike, price, futures in [
        ("2026-09-25", premium.OptionType.CALL, 7300.0, 0.0, reference),
        ("2026-09-25", premium.OptionType.CALL, 7400.0, None, reference),
        ("2026-09-25", premium.OptionType.PUT, 7300.0, 12.3456789012345, reference),
        ("2026-10-23", premium.OptionType.CALL, 9000.0, 1.23456789012345, None),
    ]:
        dte = (date.fromisoformat(expiry) - date.fromisoformat(query.as_of)).days + 1

        def values(
            reference: float | None,
            price: float | None = price,
            strike: float = strike,
            side: premium.OptionType = side,
            dte: int = dte,
        ) -> premium.ValueMetrics:
            def normalized(value: float | None) -> premium.TimeNormalizedMetrics:
                ratio = (
                    None
                    if value is None or reference is None or reference == 0
                    else value / reference
                )
                return premium.TimeNormalizedMetrics(
                    unannualized=premium.MetricValues(value, ratio),
                    annualized=premium.MetricValues(
                        None if value is None else value * 365 / dte,
                        None if ratio is None else ratio * 365 / dte,
                    ),
                )

            intrinsic = (
                None
                if reference is None
                else max(
                    0,
                    reference - strike if side == premium.OptionType.CALL else strike - reference,
                )
            )
            return premium.ValueMetrics(
                total=normalized(price),
                time_value=normalized(
                    None if price is None or intrinsic is None else price - intrinsic
                ),
            )

        points.append(
            premium.PremiumPoint(
                observation=observation,
                instrument_id=(
                    f"MO{expiry[2:4]}{expiry[5:7]}-"
                    f"{'C' if side == premium.OptionType.CALL else 'P'}-{int(strike)}.CFE"
                ),
                option_product=query.option_product,
                option_type=side,
                expiry_date=expiry,
                strike=strike,
                price_type=query.price_type,
                premium=price,
                underlying=underlying,
                futures=futures,
                calculation_basis=premium.CalculationBasis(),
                dte=dte,
                metrics=premium.PremiumMetrics(
                    values(7300.0), values(None if futures is None else futures.price)
                ),
            )
        )
    return premium.PremiumPlaneResult(
        plane=premium.PremiumPlane(
            observation=observation,
            option_product=query.option_product,
            price_type=query.price_type,
            underlying=underlying,
            calculation_basis=premium.CalculationBasis(),
            points=tuple(points),
        )
    )


def create_app() -> FastAPI:
    app = create_runtime()
    app.dependency_overrides[get_chain_read_provider] = lambda: chain_result
    app.dependency_overrides[get_premium_plane_provider] = lambda: premium_result
    return app
