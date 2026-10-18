"""Tests of the MO Option Chain application boundary.

Authority: ``products/mo_option_chain/ARCHITECTURE.md`` (query identity),
``products/mo_option_chain/read-contract.md`` (failure categories) and
``products/mo_option_chain/http-contract.md`` (what the transport layer does with
the boundary).

These tests lock the seam the HTTP adapter calls and the next phase wires the real
``Capture -> Raw -> MO Option Chain Preparation -> read model`` implementation
into:

* the boundary is a resolved query identity in, one result out, and it depends on
  no transport concern;
* the result carries exactly one of chain / error;
* the retained bootstrap provider reports ``service_not_wired`` rather than
  returning an invented or empty chain.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import StrEnum

import pytest

from data_snapshot.products.mo_option_chain import service
from snapshot_support.fake_chain_service import (
    TARGET_DATE,
    chain_fixture,
    chain_result,
    error_result,
)


def query(price_type: service.PriceType = service.PriceType.CLOSE) -> service.ChainQuery:
    return service.ChainQuery(
        target_trade_date=TARGET_DATE,
        option_product=service.OptionProduct.MO,
        price_type=price_type,
    )


# ---------------------------------------------------------------------------
# Read model
# ---------------------------------------------------------------------------


def test_a_point_keeps_a_null_selected_price() -> None:
    """The read model expresses "no selected price fact" as ``None``, not as 0."""
    chain = chain_fixture()
    calls = chain.expiries[0].calls

    assert [point.price for point in calls] == [356.4, None, 0.0]
    assert calls[2].price == 0.0
    assert calls[2].price is not None


def test_the_chain_is_self_describing() -> None:
    chain = chain_fixture()

    assert chain.target_trade_date == TARGET_DATE
    assert chain.option_product == "MO"
    assert chain.price_type is service.PriceType.CLOSE
    assert chain.underlying.instrument_id == "000852.SH"
    assert chain.underlying.price is not None


def test_the_read_model_carries_no_option_type_or_expiry_on_a_point() -> None:
    """Grouping is expressed by the parent, not repeated on every point."""
    point = chain_fixture().expiries[0].calls[0]

    assert not hasattr(point, "option_type")
    assert not hasattr(point, "expiry_date")


def test_the_read_model_is_immutable() -> None:
    """A delivery surface serializes the read model; it does not edit it."""
    chain = chain_fixture()

    with pytest.raises(FrozenInstanceError):
        chain.price_type = service.PriceType.HIGH  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Query identity
# ---------------------------------------------------------------------------


def test_price_type_defaults_to_close() -> None:
    assert service.DEFAULT_PRICE_TYPE is service.PriceType.CLOSE


def test_v1_supports_exactly_the_authority_price_types() -> None:
    assert {price_type.value for price_type in service.PriceType} == {
        "open",
        "high",
        "low",
        "close",
    }


def test_v1_supports_mo_and_keeps_the_product_dimension() -> None:
    assert service.SUPPORTED_OPTION_PRODUCTS == ("MO",)
    assert service.DEFAULT_OPTION_PRODUCT is service.OptionProduct.MO


def test_the_product_dimension_has_one_authoritative_type() -> None:
    """The supported list is derived from the enum, not maintained beside it."""
    assert tuple(product.value for product in service.OptionProduct) == (
        service.SUPPORTED_OPTION_PRODUCTS
    )
    assert service.DEFAULT_OPTION_PRODUCT.value in service.SUPPORTED_OPTION_PRODUCTS
    assert issubclass(service.OptionProduct, StrEnum)
    assert issubclass(service.PriceType, StrEnum)


# ---------------------------------------------------------------------------
# Result and provider boundary
# ---------------------------------------------------------------------------


def test_a_result_carries_exactly_one_of_chain_or_error() -> None:
    assert chain_result().chain is not None
    assert chain_result().error is None
    assert error_result(service.DateNotAvailableError("no facts")).error is not None

    with pytest.raises(ValueError):
        service.ChainReadResult()
    with pytest.raises(ValueError):
        service.ChainReadResult(
            chain=chain_fixture(), error=service.DateNotAvailableError("no facts")
        )


def test_every_read_failure_has_its_own_category() -> None:
    """The boundary exposes the read contract's failure categories as types."""
    categories = {
        service.InvalidQueryError.kind,
        service.UnsupportedQueryError.kind,
        service.DateNotAvailableError.kind,
        service.OptionChainUnavailableError.kind,
        service.ServiceNotWiredError.kind,
    }

    assert categories == {
        "invalid_query",
        "unsupported_query",
        "date_not_available",
        "option_chain_unavailable",
        "service_not_wired",
    }
    for error_type in (
        service.InvalidQueryError,
        service.UnsupportedQueryError,
        service.DateNotAvailableError,
        service.OptionChainUnavailableError,
        service.ServiceNotWiredError,
    ):
        assert issubclass(error_type, service.ChainReadError)


def test_the_placeholder_provider_reports_not_wired_without_market_data() -> None:
    """The retained bootstrap provider fails instead of inventing a chain."""
    result = service.read_chain_not_wired(query())

    assert result.chain is None
    assert isinstance(result.error, service.ServiceNotWiredError)
    assert result is service.SERVICE_NOT_WIRED_RESULT


def test_the_placeholder_provider_needs_no_data_to_answer() -> None:
    """It reads nothing: no Raw Artifact, no Source call, no filesystem access."""
    assert service.read_chain_not_wired(query(service.PriceType.HIGH)).error is not None
