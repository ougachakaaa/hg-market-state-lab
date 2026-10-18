"""Bind operation-local domain policies, source and owned persistence."""

from collections.abc import Callable
from pathlib import Path

from data_lake._runtime import database_path
from data_lake.adapters.outbound.sqlite import Repository as SQLiteRepository
from data_lake.application import Core
from data_lake.domain import Unit
from data_lake.ports import Repository, Source
from data_lake.providers.tushare import TushareExecutor

from ._domain import DATASET, CompletenessChecker, normalize, project
from ._models import (
    OptionsDailyExport,
    OptionsDailyRange,
)
from ._source import DailySource, batches


def create_repository() -> Repository:
    return SQLiteRepository(
        database_path(DATASET, Path(__file__).resolve().parents[4] / "data"), DATASET, "tushare"
    )


def prepare_source() -> Source:
    return DailySource(TushareExecutor().prepare())


def compose(
    repository: Repository,
    units: tuple[Unit, ...],
    source_factory: Callable[[], Source],
    *,
    reuse_rows: bool = False,
) -> Core[OptionsDailyRange, OptionsDailyExport]:
    checker = CompletenessChecker(reuse_rows=reuse_rows)
    return Core(
        repository,
        targets=lambda _: units,
        prepare_source=source_factory,
        normalize=normalize,
        check_complete=checker,
        project=lambda req, coverage, cached: project(req, coverage, cached, checker.row),
        batches=batches,
        prefetch=True,
    )
