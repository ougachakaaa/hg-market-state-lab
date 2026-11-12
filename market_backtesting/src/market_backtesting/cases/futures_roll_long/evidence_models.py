"""Immutable portable evidence values; bytes preserve complete ordered records."""

from dataclasses import dataclass
from typing import Literal

from .application_models import FuturesRollRequest
from .result_models import BacktestResult


@dataclass(frozen=True, slots=True)
class FuturesRollEvidencePackage:
    request: FuturesRollRequest
    canonical_inputs: bytes
    auxiliary_sse_calendar: bytes
    input_fingerprint: str
    replay: bytes
    performance: bytes
    result: bytes
    associations: bytes
    profile: str = "futures_roll_long_evidence_v1"


@dataclass(frozen=True, slots=True)
class EvidenceVerification:
    status: Literal["verified"]
    input_fingerprint: str
    result: BacktestResult
    daily_record_count: int
    state_event_count: int
