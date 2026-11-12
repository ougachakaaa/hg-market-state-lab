"""Case-owned portable evidence and pure offline reconstruction; no persistence."""

from dataclasses import asdict
from datetime import date
from typing import Any

from .application_models import (
    FuturesRollExecution,
    FuturesRollRequest,
    PreparedFuturesRollInputs,
)
from .evidence_models import EvidenceVerification, FuturesRollEvidencePackage
from .fingerprint import (
    canonical_calendar_bytes,
    canonical_input_bytes,
    decode_calendar_bytes,
    decode_canonical_inputs,
    decode_date,
    evidence_error,
    exact_object,
    input_fingerprint,
    strict_json,
)
from .performance import analyze_futures_roll
from .public_inputs import build_replay_input, public_requests_for
from .replay import replay_futures_roll
from .result import build_backtest_result
from .result_models import DEFINITION_VERSION, RESULT_PROFILE, BacktestResult
from .result_validation import validate_backtest_result

ASSUMPTIONS = (
    "Validated complete public exports; CFFEX sessions define the replay clock.",
    "SSE calendar is an independently retained Index prerequisite.",
    "Public metadata/active sets are assumed available at historical decision time.",
    "Pure W1 Slot resolution; entry M1, expiry-driven profile target, terminal Flat.",
    "Ideal session Close valuation/execution; Core single-position accounting.",
    "Fixed initial index-equivalent capital; gross simple strategy returns.",
)


def _json(raw: Any) -> bytes:
    import json

    def default(value: Any) -> str:
        if type(value) is date:
            return value.isoformat()
        return evidence_error()

    try:
        return json.dumps(
            raw,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
            default=default,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError):
        return evidence_error()


def build_evidence_package(
    execution: FuturesRollExecution, result: BacktestResult
) -> FuturesRollEvidencePackage:
    validate_backtest_result(result, execution)
    return FuturesRollEvidencePackage(
        execution.request,
        canonical_input_bytes(execution.inputs.exports),
        canonical_calendar_bytes(execution.inputs.index_calendar_export),
        execution.input_fingerprint,
        _json(asdict(execution.replay)),
        _json(asdict(execution.performance)),
        _json(asdict(result)),
        _json(
            {
                "public_requests": asdict(execution.inputs.public_requests),
                "auxiliary_sse_request": asdict(execution.inputs.index_calendar_request),
                "definition_version": DEFINITION_VERSION,
                "result_profile": RESULT_PROFILE,
                "policy": "MechanicalRollPolicy",
                "strategy_profile": execution.request.strategy_profile,
                "assumptions": ASSUMPTIONS,
            }
        ),
    )


def encode_evidence_package(package: FuturesRollEvidencePackage) -> bytes:
    if not isinstance(package, FuturesRollEvidencePackage):
        evidence_error()
    return _json(
        {
            "profile": package.profile,
            "request": asdict(package.request),
            "canonical_inputs": strict_json(package.canonical_inputs),
            "auxiliary_sse_calendar": strict_json(package.auxiliary_sse_calendar),
            "input_fingerprint": package.input_fingerprint,
            "replay": strict_json(package.replay),
            "performance": strict_json(package.performance),
            "result": strict_json(package.result),
            "associations": strict_json(package.associations),
        }
    )


def _reconstruct(payload: bytes) -> tuple[FuturesRollEvidencePackage, EvidenceVerification]:
    raw = exact_object(
        strict_json(payload),
        (
            "profile",
            "request",
            "canonical_inputs",
            "auxiliary_sse_calendar",
            "input_fingerprint",
            "replay",
            "performance",
            "result",
            "associations",
        ),
    )
    if raw["profile"] != "futures_roll_long_evidence_v1":
        evidence_error()
    r = exact_object(
        raw["request"], ("case", "product_code", "start_date", "end_date", "strategy_profile")
    )
    request = FuturesRollRequest(
        r["product_code"],
        decode_date(r["start_date"]),
        decode_date(r["end_date"]),
        r["strategy_profile"],
    )
    if r["case"] != request.case:
        evidence_error()
    exports = decode_canonical_inputs(_json(raw["canonical_inputs"]))
    auxiliary = decode_calendar_bytes(_json(raw["auxiliary_sse_calendar"]))
    fingerprint = input_fingerprint(exports)
    if fingerprint != raw["input_fingerprint"]:
        evidence_error()
    from .public_inputs import validate_retained_exports

    validate_retained_exports(request, exports, auxiliary)
    public_requests, sse_request = public_requests_for(request, exports)
    inputs = PreparedFuturesRollInputs(
        request,
        build_replay_input(request, exports, fingerprint),
        exports,
        public_requests,
        (),
        fingerprint,
        sse_request,
        auxiliary,
    )
    replay = replay_futures_roll(inputs.replay_input)
    execution = FuturesRollExecution(
        request,
        replay.sessions[0],
        replay.sessions[-1],
        replay,
        analyze_futures_roll(replay),
        inputs,
    )
    result = build_backtest_result(execution)
    package = build_evidence_package(execution, result)
    # Encoding comparison rejects all missing/extra fields, wrong scalar types,
    # changed events, pricing, states, accounting, performance and public metadata.
    if encode_evidence_package(package) != _json(raw):
        evidence_error()
    return package, EvidenceVerification(
        "verified",
        fingerprint,
        result,
        len(replay.replay.daily),
        sum(len(record.transition.events) for record in replay.replay.daily),
    )


def decode_evidence_package(payload: bytes) -> FuturesRollEvidencePackage:
    return _reconstruct(payload)[0]


def reproduce_futures_roll_evidence(
    payload: bytes, expected_result: BacktestResult | None = None
) -> EvidenceVerification:
    outcome = _reconstruct(payload)[1]
    if expected_result is not None and _json(asdict(expected_result)) != _json(
        asdict(outcome.result)
    ):
        evidence_error()
    return outcome
