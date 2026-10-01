"""Internal credential composition and provider transport partitioning."""

import os
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Protocol

from dotenv import dotenv_values

from data_lake._domain import ExecutionFailure, Unit
from data_lake.results import OperationError


class Client(Protocol):
    def trade_cal(self, **kwargs: str) -> object: ...


def provider_date(value: object) -> date:
    if not isinstance(value, str) or len(value) != 8 or not value.isascii() or not value.isdigit():
        raise ExecutionFailure("Source date must be a valid YYYYMMDD value", "invalid_date")
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:]))
    except ValueError as exc:
        raise ExecutionFailure("Source date is invalid", "invalid_date") from exc


def batches(units: tuple[Unit, ...]) -> Iterable[tuple[Unit, ...]]:
    # Bound the queried calendar span even when selected dates have cached gaps.
    groups: dict[int, list[Unit]] = {}
    for unit in units:
        _, day = identity(unit)
        groups.setdefault(day.year, []).append(unit)
    return tuple(tuple(group) for group in groups.values())


def identity(unit: Unit) -> tuple[str, date]:
    value = unit.identity
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or not isinstance(value[0], str)
        or type(value[1]) is not date
    ):
        raise OperationError("Invalid internal calendar identity")
    return value[0], value[1]


class TradeCalSource:
    def __init__(self, client: Client) -> None:
        self._client = client

    def fetch(self, units: tuple[Unit, ...]) -> dict[str, object]:
        exchange, _ = identity(units[0])
        targets = {identity(unit)[1]: unit for unit in units}
        try:
            response = self._client.trade_cal(
                exchange=exchange,
                start_date=min(targets).isoformat().replace("-", ""),
                end_date=max(targets).isoformat().replace("-", ""),
                fields="exchange,cal_date,is_open,pretrade_date",
            )
        except Exception as exc:
            raise ExecutionFailure("Tushare trade_cal request failed", "source_request") from exc
        try:
            rows = response.to_dict(orient="records")  # type: ignore[attr-defined]
        except Exception as exc:
            raise ExecutionFailure(
                "Source response cannot be partitioned", "source_response"
            ) from exc
        if not isinstance(rows, list):
            raise ExecutionFailure("Source response cannot be partitioned", "source_response")
        partition: dict[str, object] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise ExecutionFailure("Source row cannot be partitioned", "source_identity")
            # An unaddressable row cannot safely attest to any target in this batch.
            day = provider_date(row.get("cal_date"))
            if day not in targets:
                continue
            key = targets[day].key
            if key in partition:
                partition[key] = ExecutionFailure("Duplicate Source identity", "duplicate_identity")
            elif row.get("exchange") != exchange:
                partition[key] = ExecutionFailure("Source exchange identity mismatch", "identity")
            else:
                partition[key] = row
        return partition


def prepare_source() -> TradeCalSource:
    try:
        token = os.environ.get("TUSHARE_TOKEN")
        if token is None:
            root = Path(__file__).resolve().parents[7]
            token = dotenv_values(root / "market-snapshot/.env").get("TUSHARE_TOKEN")
        if not token or not token.strip():
            raise OperationError("TUSHARE_TOKEN credential is required to fetch calendar facts")
        import tushare

        return TradeCalSource(tushare.pro_api(token))
    except OperationError:
        raise
    except Exception as exc:
        raise OperationError("Calendar Source could not be initialized") from exc
