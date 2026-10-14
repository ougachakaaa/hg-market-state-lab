"""Internal credential composition and provider transport partitioning."""

from collections.abc import Iterable
from typing import Protocol

from data_lake.domain import ExecutionFailure, Unit
from data_lake.providers.tushare import TushareExecutor

from ._domain import identity, provider_date


class Client(Protocol):
    def call(self, endpoint: str, **kwargs: str) -> object: ...


def batches(units: tuple[Unit, ...]) -> Iterable[tuple[Unit, ...]]:
    # Bound the queried calendar span even when selected dates have cached gaps.
    groups: dict[int, list[Unit]] = {}
    for unit in units:
        _, day = identity(unit)
        groups.setdefault(day.year, []).append(unit)
    return tuple(tuple(group) for group in groups.values())


class TradeCalSource:
    def __init__(self, client: Client) -> None:
        self._client = client

    def fetch(self, units: tuple[Unit, ...]) -> dict[str, object]:
        exchange, _ = identity(units[0])
        targets = {identity(unit)[1]: unit for unit in units}
        response = self._client.call(
            "trade_cal",
            exchange=exchange,
            start_date=min(targets).strftime("%Y%m%d"),
            end_date=max(targets).strftime("%Y%m%d"),
            fields="exchange,cal_date,is_open,pretrade_date",
        )
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
    return TradeCalSource(TushareExecutor().prepare())
