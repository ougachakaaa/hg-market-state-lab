"""Observed-window expiry extraction and whole-Artifact invariants."""

from datetime import date

from data_lake.datasets.tushare_equity_index_options import OptionsDailyExport

from ._models import ExpiryUniverseArtifact, ExpiryUniverseRequest
from ._upstream import options_provenance, require, validate_options_context

IDENTITY = "cffex_option_expiry_universe"


def derive(request: ExpiryUniverseRequest, view: OptionsDailyExport) -> ExpiryUniverseArtifact:
    return ExpiryUniverseArtifact(
        IDENTITY,
        request.product_code,
        request.expiry_start_date,
        request.expiry_end_date,
        tuple(
            sorted(
                {
                    row.expiry
                    for row in view.records
                    if request.expiry_start_date <= row.expiry <= request.expiry_end_date
                }
            )
        ),
        True,
        options_provenance(view),
    )


def validate(artifact: ExpiryUniverseArtifact, request: ExpiryUniverseRequest) -> None:
    require(
        artifact.complete is True
        and artifact.semantic_identity
        == (
            IDENTITY,
            request.product_code,
            request.expiry_start_date,
            request.expiry_end_date,
        ),
        "Invalid Universe Artifact identity / completeness",
    )
    require(
        type(artifact.expiries) is tuple
        and all(type(value) is date for value in artifact.expiries),
        "Invalid Universe dates",
    )
    require(
        artifact.expiries == tuple(sorted(set(artifact.expiries)))
        and all(
            request.expiry_start_date <= value <= request.expiry_end_date
            for value in artifact.expiries
        ),
        "Universe dates must be sorted, unique and in-range",
    )
    validate_options_context(
        artifact.provenance,
        request.product_code,
        request.expiry_start_date,
        request.expiry_end_date,
    )
    require(artifact.provenance.coverage.complete is True, "Incomplete Universe provenance")
