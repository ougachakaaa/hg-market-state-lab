"""Bind operation-local domain policies, source and owned persistence."""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, cast

from data_lake._runtime import database_path
from data_lake.adapters.outbound.sqlite import Repository as SQLiteRepository
from data_lake.application import Core
from data_lake.domain import Unit, UnitRecords
from data_lake.ports import Repository, Source
from data_lake.providers.tushare import TushareExecutor

from ._domain import (
    DATASET,
    CompletenessChecker,
    check_complete,
    identity,
    metadata_representatives,
    normalize,
    project,
)
from ._models import IndexDailyExport, IndexDailyRange
from ._source import DailySource, batches


def create_repository() -> Repository:
    return SQLiteRepository(
        database_path(DATASET, Path(__file__).resolve().parents[4] / "data"), DATASET, "tushare"
    )


def prepare_source(repository: Repository, codes: Sequence[str] = ()) -> Source:
    cached: dict[str, dict[str, Any]] = {}
    representatives = metadata_representatives(repository.successful_keys(), codes)
    for item in repository.snapshot(representatives).successful:
        check_complete(item.unit, UnitRecords(item.records, item.instruments, item.basis))
        cached[identity(item.unit)[0]] = cast(dict[str, Any], item.basis)["metadata"]
    return DailySource(TushareExecutor().prepare(), cached, tuple(codes))


def compose(
    repository: Repository,
    units: tuple[Unit, ...],
    source_factory: Callable[[], Source],
    *,
    reuse_rows: bool = False,
) -> Core[IndexDailyRange, IndexDailyExport]:
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
