"""Fake application boundary for the MO Option Chain HTTP contract tests.

The HTTP delivery adapter is tested against this provider independently of the
real ``Capture -> Raw -> Preparation -> read model`` chain, which is also covered
by integration tests
(``products/mo_option_chain/http-contract.md`` section 7).

The fake carries test data only. It is never imported by ``src/``: fabricated
market facts must not live in the business semantics layer.
"""

from __future__ import annotations

from dataclasses import replace

from data_snapshot.products.mo_option_chain import service

TARGET_DATE = "2026-09-17"
EXPIRY_DATE = "2026-09-25"
UNDERLYING_ID = "000852.SH"
UNDERLYING_PRICE = 7312.45
FUTURES_ID = "IM2609.CFE"
FUTURES_PRICE = 7487.6

CALL_WITH_PRICE = "MO2609-C-7000.CFE"
CALL_WITH_NULL_PRICE = "MO2609-C-7200.CFE"
CALL_WITH_ZERO_PRICE = "MO2609-C-7400.CFE"
PUT_WITH_PRICE = "MO2609-P-7000.CFE"


def chain_fixture() -> service.OptionChain:
    """The read model of one complete chain, as the documented example.

    It deliberately carries all three selected-price states of the read contract:
    a numeric price, a ``null`` price and a numeric ``0``.
    """
    return service.OptionChain(
        target_trade_date=TARGET_DATE,
        option_product=service.OptionProduct.MO,
        price_type=service.PriceType.CLOSE,
        underlying=service.UnderlyingRef(
            instrument_id=UNDERLYING_ID, price=UNDERLYING_PRICE
        ),
        expiries=(
            service.ExpiryGroup(
                expiry_date=EXPIRY_DATE,
                futures=service.FuturesRef(FUTURES_ID, FUTURES_PRICE),
                calls=(
                    service.OptionPoint(
                        instrument_id=CALL_WITH_PRICE, strike=7000.0, price=356.4
                    ),
                    service.OptionPoint(
                        instrument_id=CALL_WITH_NULL_PRICE, strike=7200.0, price=None
                    ),
                    service.OptionPoint(
                        instrument_id=CALL_WITH_ZERO_PRICE, strike=7400.0, price=0.0
                    ),
                ),
                puts=(
                    service.OptionPoint(
                        instrument_id=PUT_WITH_PRICE, strike=7000.0, price=41.8
                    ),
                ),
            ),
        ),
    )


def chain_result() -> service.ChainReadResult:
    """The successful read-model result of :func:`chain_fixture`."""
    return service.ChainReadResult(chain=chain_fixture())


def error_result(error: service.ChainReadError) -> service.ChainReadResult:
    """A failed read-model result carrying ``error``."""
    return service.ChainReadResult(error=error)


class FakeChainReadProvider:
    """A scripted read-model provider that records the queries it receives.

    A successful result echoes the resolved query identity back into the chain,
    as the real read model does: ``price_type`` and ``target_trade_date`` of the
    response are the resolved ones, not the caller's omission.
    """

    def __init__(self, result: service.ChainReadResult | None = None) -> None:
        self.result = result
        self.queries: list[service.ChainQuery] = []

    def __call__(self, query: service.ChainQuery) -> service.ChainReadResult:
        self.queries.append(query)
        if self.result is not None:
            return self.result
        return service.ChainReadResult(
            chain=replace(chain_fixture(), target_trade_date=query.target_trade_date,
                          price_type=query.price_type)
        )

    @property
    def last_query(self) -> service.ChainQuery:
        assert self.queries, "the provider was never asked for a chain"
        return self.queries[-1]
