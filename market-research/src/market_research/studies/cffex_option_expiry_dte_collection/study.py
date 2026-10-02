"""Orchestration-only workflow; METHOD.md / RESULTS.md own bindings and outcomes."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from market_research.observations import ObservationInvalidRequestError
from market_research.observations.cffex_option_expiry_dte_chain import (
    ExpiryDteChainArtifact,
    ExpiryDteChainRequest,
    ExpiryDteChainService,
)
from market_research.observations.cffex_option_expiry_universe import (
    ExpiryUniverseArtifact,
    ExpiryUniverseRequest,
    ExpiryUniverseService,
)


class CollectionInvalidRequestError(ValueError):
    """Invalid Study inputs; no workflow or dependency access is allowed."""


@dataclass(frozen=True)
class CollectionRequest:
    product_code: str
    expiry_start_date: date
    expiry_end_date: date
    target_dte: int

    def __post_init__(self) -> None:
        # The public producers own these domains. Construction performs no operations.
        try:
            ExpiryUniverseRequest(self.product_code, self.expiry_start_date, self.expiry_end_date)
            ExpiryDteChainRequest(self.product_code, self.expiry_end_date, self.target_dte)
        except ObservationInvalidRequestError as error:
            raise CollectionInvalidRequestError(str(error)) from error

    @property
    def semantic_identity(self) -> tuple[str, str, date, date, int]:
        return (
            "cffex_option_expiry_dte_collection",
            self.product_code,
            self.expiry_start_date,
            self.expiry_end_date,
            self.target_dte,
        )


@dataclass(frozen=True)
class Failure:
    stage: str
    expiry_date: date | None
    reason: str


@dataclass(frozen=True)
class CollectionOutcome:
    product_code: str
    expiry_start_date: date
    expiry_end_date: date
    target_dte: int
    status: str
    discovered_expiry_count: int | None
    planned_observation_count: int | None
    completed_observation_count: int
    failed_observation_count: int
    failures: tuple[Failure, ...]


def _outcome(
    request: CollectionRequest,
    discovered: int | None,
    planned: int | None,
    completed: int,
    failed: int,
    failures: tuple[Failure, ...],
) -> CollectionOutcome:
    return CollectionOutcome(
        request.product_code,
        request.expiry_start_date,
        request.expiry_end_date,
        request.target_dte,
        "failure" if failures else "success",
        discovered,
        planned,
        completed,
        failed,
        failures,
    )


def run(
    request: CollectionRequest,
    *,
    universe_factory: Callable[[], ExpiryUniverseService],
    chain_factory: Callable[[], ExpiryDteChainService],
) -> CollectionOutcome:
    if not isinstance(request, CollectionRequest):
        raise CollectionInvalidRequestError("Expected CollectionRequest")
    request.__post_init__()
    universe_request = ExpiryUniverseRequest(
        request.product_code,
        request.expiry_start_date,
        request.expiry_end_date,
    )
    try:
        universe = universe_factory().ensure(universe_request)
        if (
            not isinstance(universe, ExpiryUniverseArtifact)
            or universe.complete is not True
            or type(universe.expiries) is not tuple
            or universe.semantic_identity
            != (
                "cffex_option_expiry_universe",
                request.product_code,
                request.expiry_start_date,
                request.expiry_end_date,
            )
        ):
            raise ValueError("Universe returned an incomplete / mismatched Artifact")
    except Exception as error:
        return _outcome(
            request, None, None, 0, 0, (Failure("ensure_expiry_universe", None, str(error)),)
        )
    discovered = len(universe.expiries)
    try:
        plan = tuple(
            ExpiryDteChainRequest(request.product_code, expiry, request.target_dte)
            for expiry in universe.expiries
        )
        expiries = tuple(item.expiry_date for item in plan)
        if expiries != tuple(sorted(set(expiries))) or any(
            not request.expiry_start_date <= expiry <= request.expiry_end_date
            for expiry in expiries
        ):
            raise ValueError("Universe plan dates must be sorted, unique and in-range")
    except Exception as error:
        return _outcome(
            request,
            discovered,
            None,
            0,
            0,
            (Failure("build_runtime_expiry_plan", None, str(error)),),
        )
    service = None
    completed = 0
    failures = []
    for chain_request in plan:
        try:
            if service is None:
                service = chain_factory()
            artifact = service.ensure(chain_request)
            if (
                not isinstance(artifact, ExpiryDteChainArtifact)
                or artifact.complete is not True
                or artifact.semantic_identity
                != (
                    "cffex_option_expiry_dte_chain",
                    chain_request.product_code,
                    chain_request.expiry_date,
                    chain_request.target_dte,
                )
            ):
                raise ValueError("Chain returned an incomplete / mismatched Artifact")
            completed += 1
        except Exception as error:
            failures.append(Failure("ensure_expiry_chains", chain_request.expiry_date, str(error)))
    return _outcome(request, discovered, len(plan), completed, len(failures), tuple(failures))
