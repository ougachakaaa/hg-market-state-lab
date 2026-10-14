"""Bind Calendar policies to its Source and owned SQLite adapters."""

from collections.abc import Callable
from pathlib import Path

from data_lake._runtime import database_path
from data_lake.adapters.outbound.sqlite import Repository
from data_lake.application import Core
from data_lake.ports import Repository as RepositoryPort
from data_lake.ports import Source

from ._domain import DATASET, check_complete, normalize, project, targets
from ._models import (
    TradeCalendarExport,
    TradeCalendarRange,
)
from ._source import batches


def _compose(
    repository: RepositoryPort, source_factory: Callable[[], Source]
) -> Core[TradeCalendarRange, TradeCalendarExport]:
    return Core(
        repository,
        targets=targets,
        prepare_source=source_factory,
        normalize=normalize,
        check_complete=check_complete,
        project=project,
        batches=batches,
    )


def create_repository() -> RepositoryPort:
    return Repository(
        database_path(DATASET, Path(__file__).resolve().parents[4] / "data"),
        DATASET,
        "tushare",
    )
