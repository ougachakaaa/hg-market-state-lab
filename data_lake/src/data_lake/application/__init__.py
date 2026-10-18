"""Composition helpers for Dataset-owned services, not a consumer-facing registry."""

import logging
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

from data_lake.domain import CachedUnit, ExecutionFailure, Status, Unit, UnitRecords
from data_lake.ports import Repository, Snapshot, Source
from data_lake.results import (
    CoverageResult,
    EnsureResult,
    ExportEnvelope,
    InvalidRequestError,
    OperationError,
    UnitFailure,
)

logger = logging.getLogger(__name__)


def single_batch(units: tuple[Unit, ...]) -> Iterable[tuple[Unit, ...]]:
    return (units,)


class Core[Request, View: ExportEnvelope]:
    """Dataset services compose this internal helper and keep their semantic boundary."""

    def __init__(
        self,
        repository: Repository,
        *,
        targets: Callable[[Request], Sequence[Unit]],
        prepare_source: Callable[[], Source],
        normalize: Callable[[Unit, object], UnitRecords],
        check_complete: Callable[[Unit, UnitRecords], None],
        project: Callable[[Request, CoverageResult, tuple[CachedUnit, ...]], View],
        batches: Callable[[tuple[Unit, ...]], Iterable[tuple[Unit, ...]]] = single_batch,
        prefetch: bool = False,
    ) -> None:
        self._repository = repository
        self._targets = targets
        self._prepare_source = prepare_source
        self._normalize = normalize
        self._check_complete = check_complete
        self._project = project
        self._batches = batches
        self._prefetch = prefetch

    def _units(self, request: Request) -> tuple[Unit, ...]:
        # Serialize immediately to validate identities and deduplicate semantic targets.
        return tuple({unit.key: unit for unit in self._targets(request)}.values())

    def _snapshot(self, units: tuple[Unit, ...]) -> Snapshot:
        snapshot = self._repository.snapshot(units)
        for cached in snapshot.successful:
            try:
                self._check_complete(
                    cached.unit, UnitRecords(cached.records, cached.instruments, cached.basis)
                )
            except ExecutionFailure as exc:
                raise OperationError("Successful cache violates Dataset completeness") from exc
        return snapshot

    def coverage(self, request: Request) -> CoverageResult:
        try:
            return self._snapshot(self._units(request)).coverage
        except (InvalidRequestError, OperationError):
            raise
        except Exception as exc:
            raise OperationError("Coverage operation could not be executed") from exc

    def export(self, request: Request) -> View:
        try:
            snapshot = self._snapshot(self._units(request))
            view = self._project(request, snapshot.coverage, snapshot.successful)
            if view.dataset != self._repository.dataset or view.coverage != snapshot.coverage:
                raise OperationError("Dataset projection returned inconsistent export metadata")
            return view
        except (InvalidRequestError, OperationError):
            raise
        except Exception as exc:
            raise OperationError("Export operation could not be executed") from exc

    def ensure(self, request: Request) -> EnsureResult:
        try:
            return self._ensure(request)
        except (InvalidRequestError, OperationError):
            raise
        except Exception as exc:
            raise OperationError("Ensure operation could not be executed") from exc

    def _partitions(
        self,
        source: Source,
        batches: tuple[tuple[Unit, ...], ...],
    ) -> Generator[tuple[tuple[Unit, ...], Mapping[str, object] | ExecutionFailure]]:
        def fetch(batch: tuple[Unit, ...]) -> Mapping[str, object] | ExecutionFailure:
            try:
                return source.fetch(batch)
            except ExecutionFailure as failure:
                return failure

        def pending(batch: tuple[Unit, ...]) -> None:
            for unit in batch:
                self._repository.pending(unit)

        if not self._prefetch:
            for batch in batches:
                pending(batch)
                yield batch, fetch(batch)
            return
        worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="datalake-source")
        future = None
        completed = False
        try:
            pending(batches[0])
            future = worker.submit(fetch, batches[0])
            for index, batch in enumerate(batches):
                partition = future.result()
                if index + 1 < len(batches):
                    next_batch = batches[index + 1]
                    pending(next_batch)
                    future = worker.submit(fetch, next_batch)
                yield batch, partition
            completed = True
        finally:
            try:
                cancel = getattr(source, "cancel", None)
                if not completed and callable(cancel):
                    cancel()
            finally:
                if future is not None:
                    future.cancel()
                worker.shutdown(wait=True, cancel_futures=True)

    def _ensure(self, request: Request) -> EnsureResult:
        units = self._units(request)
        checked = self._snapshot(units)
        before = Snapshot(checked.coverage, (), checked.statuses)
        del checked
        selected = tuple(unit for unit in units if before.statuses.get(unit.key) != Status.SUCCESS)
        logger.info(
            "ensure_start dataset=%s requested=%d already_successful=%d selected=%d",
            self._repository.dataset,
            len(units),
            before.coverage.successful_units,
            len(selected),
        )
        if not selected:
            logger.info(
                "ensure_complete dataset=%s attempted=0 complete=%s",
                self._repository.dataset,
                before.coverage.complete,
            )
            return EnsureResult(len(units), len(units), 0, 0, 0, 0, before.coverage.complete, ())

        source = self._prepare_source()
        # Validate the finite request grouping before changing persistence state.
        batches = tuple(self._batches(selected))
        keys = [unit.key for batch in batches for unit in batch]
        if (
            any(not batch for batch in batches)
            or len(keys) != len(set(keys))
            or set(keys) != {unit.key for unit in selected}
        ):
            raise OperationError("Source batches must partition the selected units")
        failures: list[UnitFailure] = []
        succeeded = written = 0

        def report_progress() -> None:
            finished = succeeded + len(failures)
            if finished % 25 == 0 or finished == len(selected):
                logger.info(
                    "ensure_progress dataset=%s finished=%d/%d succeeded=%d failed=%d",
                    self._repository.dataset,
                    finished,
                    len(selected),
                    succeeded,
                    len(failures),
                )

        with self._repository.write_session(), closing(self._partitions(source, batches)) as parts:
            for batch, partition in parts:
                if isinstance(partition, ExecutionFailure):
                    failure = partition
                    for unit in batch:
                        self._repository.failed(unit, failure)
                        failures.append(UnitFailure(unit.identity, failure.reason))
                        logger.warning(
                            "unit_failed dataset=%s identity=%s code=%s reason=%s",
                            self._repository.dataset,
                            unit.identity,
                            failure.code,
                            failure.reason,
                        )
                    report_progress()
                    continue
                for unit in batch:
                    try:
                        if unit.key not in partition:
                            raise ExecutionFailure(
                                "Source returned no facts for the requested unit", "missing_unit"
                            )
                        normalized = self._normalize(unit, partition[unit.key])
                        self._check_complete(unit, normalized)
                        written += self._repository.succeed(unit, normalized)
                        succeeded += 1
                    except ExecutionFailure as failure:
                        self._repository.failed(unit, failure)
                        failures.append(UnitFailure(unit.identity, failure.reason))
                        logger.warning(
                            "unit_failed dataset=%s identity=%s code=%s reason=%s",
                            self._repository.dataset,
                            unit.identity,
                            failure.code,
                            failure.reason,
                        )
                report_progress()
        after = self._snapshot(units)
        logger.info(
            "ensure_complete dataset=%s attempted=%d succeeded=%d failed=%d "
            "records_written=%d complete=%s",
            self._repository.dataset,
            len(selected),
            succeeded,
            len(failures),
            written,
            after.coverage.complete,
        )
        return EnsureResult(
            len(units),
            before.coverage.successful_units,
            len(selected),
            succeeded,
            len(failures),
            written,
            after.coverage.complete,
            tuple(failures),
        )
