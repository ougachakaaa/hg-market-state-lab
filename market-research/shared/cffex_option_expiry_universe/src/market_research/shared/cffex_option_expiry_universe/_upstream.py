"""Validate the selected public Options contract and project owned provenance.

Field meanings remain owned by Options SERVICE.md / FACTS.md; this consumer
checks public legality without reconstructing catalog completeness.
"""

import math
import re
from dataclasses import fields
from datetime import date
from typing import Any, cast

from data_lake import EnsureResult, UnitFailure
from data_lake.datasets.tushare_equity_index_options import OptionsDailyExport, OptionsDailyRow

from ._models import Coverage, OptionsProvenance, OptionsScope, Window


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def validate_coverage(coverage: Any) -> None:
    counts = tuple(
        getattr(coverage, name)
        for name in (
            "requested_units",
            "successful_units",
            "missing_units",
            "pending_units",
            "failed_units",
        )
    )
    require(all(type(value) is int and value >= 0 for value in counts), "Invalid coverage counters")
    require(sum(counts[1:]) == counts[0], "Inconsistent coverage counters")
    require(type(coverage.complete) is bool, "Invalid coverage complete flag")
    require(coverage.complete == (counts[0] == counts[1]), "Inconsistent coverage complete flag")


def require_ensure(result: EnsureResult, *, context: str) -> None:
    require(isinstance(result, EnsureResult), f"{context}: Invalid ensure result")
    counts = (
        result.requested_units,
        result.already_successful_units,
        result.attempted_units,
        result.succeeded_units,
        result.failed_units,
        result.records_written,
    )
    require(
        all(type(value) is int and value >= 0 for value in counts),
        f"{context}: Invalid ensure counters",
    )
    require(
        result.already_successful_units + result.attempted_units == result.requested_units
        and result.succeeded_units + result.failed_units == result.attempted_units,
        f"{context}: Inconsistent ensure counters",
    )
    require(type(result.complete) is bool, f"{context}: Invalid ensure complete flag")
    require(type(result.failures) is tuple, f"{context}: Invalid ensure failures")
    details = []
    for failure in result.failures:
        require(isinstance(failure, UnitFailure), f"{context}: Invalid ensure failure")
        require(type(failure.identity) is tuple, f"{context}: Invalid ensure failure identity")
        identity = cast(tuple[object, ...], failure.identity)
        require(
            len(identity) == 2
            and type(identity[0]) is str
            and bool(identity[0])
            and type(identity[1]) is date,
            f"{context}: Invalid ensure failure identity",
        )
        require(
            type(failure.reason) is str and bool(failure.reason),
            f"{context}: Invalid ensure failure reason",
        )
        selector, day = cast(tuple[str, date], identity)
        details.append(f"unit=({selector}, {day.isoformat()}): {failure.reason}")
    require(
        result.complete is True
        and not result.failures
        and result.failed_units == 0
        and result.already_successful_units + result.succeeded_units == result.requested_units,
        f"{context}: Upstream ensure did not complete; "
        f"requested_units={result.requested_units} attempted_units={result.attempted_units} "
        f"succeeded_units={result.succeeded_units} failed_units={result.failed_units}; "
        + ("; ".join(details) if details else "failures=none"),
    )


def validate_row(row: Any, product: str, start: date, end: date) -> None:
    for name in (
        "contract_code",
        "product_code",
        "symbol",
        "name",
        "exchange",
        "source_underlying_code",
        "underlying_index_code",
        "option_type",
        "exercise_type",
        "quote_unit",
        "settlement_month",
        "call_put",
    ):
        value = getattr(row, name)
        require(isinstance(value, str) and bool(value), f"Invalid Options row {name}")
    for name in ("list_date", "delist_date", "expiry", "last_exercise_date", "trade_date"):
        require(type(getattr(row, name)) is date, f"Invalid Options row {name}")
    require(
        row.last_delivery_date is None or type(row.last_delivery_date) is date,
        "Invalid last_delivery_date",
    )
    require(row.product_code == product and row.exchange == "CFFEX", "Wrong Options row scope")
    require(start <= row.trade_date <= end, "Options row outside window")
    require(row.list_date <= row.trade_date <= row.delist_date, "Invalid Options row lifecycle")
    match = re.fullmatch(
        r"([A-Z]+)([0-9]{2})(0[1-9]|1[0-2])-([CP])-([0-9]+(?:\.[0-9]+)?)", row.symbol
    )
    require(
        match is not None and row.contract_code == row.symbol + ".CFX",
        "Invalid Options contract identity",
    )
    assert match is not None
    require(
        match[1] == product
        and row.call_put == ("CALL" if match[4] == "C" else "PUT")
        and re.fullmatch(r"[0-9]{4}(0[1-9]|1[0-2])", row.settlement_month) is not None
        and row.settlement_month[2:] == match[2] + match[3]
        and float(match[5]) == row.strike,
        "Inconsistent Options contract metadata",
    )
    underlying = {"IO": "000300.SH", "HO": "000016.SH", "MO": "000852.SH"}[product]
    require(
        row.underlying_index_code == underlying and row.source_underlying_code == "OP" + underlying,
        "Inconsistent Options underlying",
    )
    for name in (
        "per_unit",
        "opt_multiplier",
        "strike",
        "pre_settle",
        "close",
        "settle",
        "volume",
        "amount",
        "open_interest",
        "pre_close",
        "open",
        "high",
        "low",
    ):
        value = getattr(row, name)
        if value is None:
            require(
                (name == "pre_close" and row.trade_date == row.list_date)
                or (name in ("open", "high", "low") and row.volume == 0 and row.amount == 0),
                f"Illegal nullable Options row {name}",
            )
        else:
            require(type(value) is float and math.isfinite(value), f"Invalid Options row {name}")
            if name in ("per_unit", "opt_multiplier", "strike"):
                require(value > 0, f"Nonpositive Options row {name}")
            if name in ("volume", "amount", "open_interest"):
                require(value >= 0, f"Negative Options row {name}")


def validate_options_context(context: Any, product: str, start: date, end: date) -> None:
    require(
        context.dataset == "tushare_equity_index_options"
        and context.view == "options_daily"
        and type(context.export_schema_version) is int
        and context.export_schema_version == 2,
        "Invalid Options export identity / schema",
    )
    require(tuple(context.scope.product_codes) == (product,), "Wrong Options export scope")
    require(
        type(context.window.start_date) is date
        and type(context.window.end_date) is date
        and context.window.start_date == start
        and context.window.end_date == end,
        "Wrong Options export window",
    )
    validate_coverage(context.coverage)


def validate_options_export(view: OptionsDailyExport, product: str, start: date, end: date) -> None:
    require(isinstance(view, OptionsDailyExport), "Invalid Options export type")
    validate_options_context(view, product, start, end)
    keys = []
    for row in view.records:
        require(isinstance(row, OptionsDailyRow), "Invalid Options public row type")
        validate_row(row, product, start, end)
        keys.append((row.product_code, row.trade_date, row.contract_code))
    require(keys == sorted(set(keys)), "Unordered / duplicate Options public rows")
    require(view.coverage.successful_units > 0 or not keys, "Rows without successful units")
    require(
        len({key[:2] for key in keys}) <= view.coverage.successful_units,
        "Options row product-days exceed successful units",
    )


def options_provenance(view: OptionsDailyExport) -> OptionsProvenance:
    return OptionsProvenance(
        dataset=view.dataset,
        view=view.view,
        export_schema_version=view.export_schema_version,
        scope=OptionsScope(tuple(cast(Any, view.scope).product_codes)),
        window=Window(cast(Any, view.window).start_date, cast(Any, view.window).end_date),
        coverage=Coverage(
            **{field.name: getattr(view.coverage, field.name) for field in fields(Coverage)}
        ),
    )
