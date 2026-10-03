"""Owned chain projection and whole-Artifact validation."""

from dataclasses import fields
from datetime import date, timedelta

from data_lake.datasets.tushare_equity_index_options import OptionsDailyExport

from ._date_resolution import validate_calendar_context
from ._models import (
    CalendarProvenance,
    ExpiryDteChainArtifact,
    ExpiryDteChainRequest,
    ExpiryDteChainRow,
)
from ._upstream import options_provenance, require, validate_options_context, validate_row

IDENTITY = "cffex_option_expiry_dte_chain"


def derive(
    request: ExpiryDteChainRequest,
    ideal: date,
    candidate: date,
    view: OptionsDailyExport,
    contexts: tuple[CalendarProvenance, ...],
) -> ExpiryDteChainArtifact:
    rows = tuple(
        ExpiryDteChainRow(
            **{field.name: getattr(row, field.name) for field in fields(ExpiryDteChainRow)}
        )
        for row in view.records
        if row.expiry == request.expiry_date
    )
    return ExpiryDteChainArtifact(
        IDENTITY,
        request.product_code,
        request.expiry_date,
        request.target_dte,
        ideal,
        candidate,
        (request.expiry_date - candidate).days + 1,
        rows,
        contexts,
        options_provenance(view),
        True,
    )


def validate(artifact: ExpiryDteChainArtifact, request: ExpiryDteChainRequest) -> None:
    require(
        artifact.complete is True
        and artifact.semantic_identity
        == (
            IDENTITY,
            request.product_code,
            request.expiry_date,
            request.target_dte,
        ),
        "Invalid chain Artifact identity / completeness",
    )
    require(
        type(artifact.ideal_calendar_date) is date
        and type(artifact.observation_date) is date
        and (request.expiry_date - artifact.ideal_calendar_date).days + 1 == request.target_dte
        and artifact.observation_date <= artifact.ideal_calendar_date <= request.expiry_date,
        "Invalid chain dates",
    )
    require(
        type(artifact.actual_dte) is int
        and artifact.actual_dte == (request.expiry_date - artifact.observation_date).days + 1
        and artifact.actual_dte >= request.target_dte,
        "Invalid actual DTE",
    )
    require(
        type(artifact.rows) is tuple and bool(artifact.rows), "Empty / mutable chain population"
    )
    contracts = []
    for row in artifact.rows:
        require(
            isinstance(row, ExpiryDteChainRow) and row.expiry == request.expiry_date,
            "Invalid matching chain row",
        )
        validate_row(
            row, request.product_code, artifact.observation_date, artifact.observation_date
        )
        contracts.append(row.contract_code)
    require(contracts == sorted(set(contracts)), "Unordered / duplicate chain contracts")
    validate_options_context(
        artifact.options_provenance,
        request.product_code,
        artifact.observation_date,
        artifact.observation_date,
    )
    coverage = artifact.options_provenance.coverage
    require(
        coverage.complete is True and coverage.requested_units == coverage.successful_units == 1,
        "Incomplete selected Options proof",
    )
    contexts = artifact.calendar_provenance
    require(type(contexts) is tuple and bool(contexts), "Missing Calendar proof")
    end = artifact.ideal_calendar_date
    for index, context in enumerate(contexts):
        start = context.window.start_date
        require(type(start) is date and start <= end, "Invalid Calendar proof range")
        validate_calendar_context(context, start, end)
        require(context.coverage.complete is True, "Incomplete Calendar proof")
        if index < len(contexts) - 1:
            require(start > artifact.observation_date, "Extraneous Calendar proof window")
            end = start - timedelta(days=1)
        else:
            require(start <= artifact.observation_date <= end, "Calendar proof gap")
