"""WP2 synthetic daily roles, completeness handoff and identity transitions."""

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from futures_basis_slot_fixtures import AFTER, BEFORE, MARCH, daily, metadata, proof, sessions
from market_research.descriptive.cases import futures_basis
from market_research.descriptive.cases.futures_basis import (
    SLOTS,
    CandidateSessions,
    ContractMetadata,
    DailySlotResolution,
    DailyUniverseEvidence,
    SlotResolutionError,
    detect_contract_transitions,
    resolve_daily_slots,
)

DAY = date(2026, 11, 19)


@pytest.mark.parametrize("months", [BEFORE, AFTER, MARCH])
@pytest.mark.parametrize("product", ["IF", "IH", "IC", "IM"])
def test_fixed_maturity_examples_and_products(months: tuple[str, ...], product: str) -> None:
    contracts = tuple(reversed(metadata(months, product)))
    evidence = proof(DAY, contracts, product)
    result = resolve_daily_slots(product, DAY, contracts, evidence=evidence)
    assert tuple(m.slot for m in result.mappings) == SLOTS
    assert tuple(m.contract.delivery_month for m in result.mappings if m.contract) == months
    assert tuple(m.contract_code for m in result.mappings) == tuple(
        f"{product}{month[2:]}.CFX" for month in months
    )
    assert all(m.status == "resolved" and m.reason is None for m in result.mappings)
    assert all(m.evidence is evidence and m.contract in contracts for m in result.mappings)
    assert result.evidence is evidence
    assert result == resolve_daily_slots(product, DAY, contracts, evidence=evidence)
    assert contracts == tuple(reversed(metadata(months, product)))
    with pytest.raises(FrozenInstanceError):
        result.trade_date = date(2026, 1, 1)  # type: ignore[misc]


def test_expiry_inclusive_and_listing_boundary_without_expiry_formula() -> None:
    # Synthetic Thursday expiry/listing: do not use a Friday formula.
    old = metadata()
    old = (replace(old[0], list_date=DAY, delist_date=DAY), *old[1:])
    result = resolve_daily_slots("IM", DAY, old, evidence=proof(DAY, old))
    assert result.mappings[0].contract is old[0]
    tomorrow = date(2026, 11, 20)
    with pytest.raises(SlotResolutionError, match="inactive inclusive lifecycle"):
        resolve_daily_slots("IM", tomorrow, old, evidence=proof(tomorrow, old))
    before_listing = (replace(old[0], list_date=tomorrow, delist_date=tomorrow), *old[1:])
    with pytest.raises(SlotResolutionError):
        resolve_daily_slots("IM", DAY, before_listing, evidence=proof(DAY, before_listing))


@pytest.mark.parametrize("next_day", [date(2026, 11, 20), date(2026, 11, 23), date(2026, 11, 30)])
def test_next_candidate_roll_and_identity_across_weekend_or_holiday(next_day: date) -> None:
    old = metadata()
    old = (replace(old[0], delist_date=DAY), *old[1:])
    previous = resolve_daily_slots("IM", DAY, old, evidence=proof(DAY, old))
    new = metadata(AFTER)
    new = (new[0], replace(new[1], list_date=next_day), *new[2:])
    current = resolve_daily_slots("IM", next_day, new, evidence=proof(next_day, new))
    result = detect_contract_transitions("IM", sessions(DAY, next_day), (previous, current))
    assert [t.slot for t in result.transitions] == ["M0", "M1"]
    assert [(t.previous_contract_code, t.contract_code) for t in result.transitions] == [
        ("IM2611.CFX", "IM2612.CFX"),
        ("IM2612.CFX", "IM2701.CFX"),
    ]
    assert previous.mappings[1].contract == current.mappings[0].contract
    for transition in result.transitions:
        assert (transition.product_code, transition.previous_date, transition.trade_date) == (
            "IM",
            DAY,
            next_day,
        )
        assert transition.previous_evidence is previous.evidence
        assert transition.evidence is current.evidence
        assert transition.previous_metadata.contract_code == transition.previous_contract_code
        assert transition.metadata.contract_code == transition.contract_code
    assert result.absence_boundaries == ()


def test_year_rollover_and_all_slot_event_order() -> None:
    a, b, c = date(2026, 12, 30), date(2027, 1, 4), date(2027, 4, 1)
    previous = daily(a, AFTER)
    current = daily(b, ("202701", "202702", "202703", "202706"))
    later = daily(c, ("202704", "202705", "202706", "202709"))
    result = detect_contract_transitions("IM", sessions(a, b, c), (previous, current, later))
    assert [(t.trade_date, t.slot) for t in result.transitions] == [
        (b, "M0"),
        (b, "M1"),
        (c, "M0"),
        (c, "M1"),
        (c, "Q1"),
        (c, "Q2"),
    ]


def test_proven_empty_and_distinct_absence_boundaries() -> None:
    a, b, c, d = (date(2026, 11, n) for n in (16, 17, 18, 19))
    absent = daily(a, ())
    assert len(absent.mappings) == 4
    assert all(m.contract_code is None and m.status == "not_applicable" for m in absent.mappings)
    assert all(m.reason == "no_active_contract" for m in absent.mappings)
    active = daily(b)
    empty = daily(c, ())
    still_empty = daily(d, ())
    result = detect_contract_transitions(
        "IM", sessions(a, b, c, d), (absent, active, empty, still_empty)
    )
    assert result.transitions == ()
    assert [(x.trade_date, x.slot, x.kind) for x in result.absence_boundaries] == [
        *((b, slot, "appeared") for slot in SLOTS),
        *((c, slot, "disappeared") for slot in SLOTS),
    ]
    boundary = result.absence_boundaries[0]
    assert boundary.previous_resolution is absent.mappings[0]
    assert boundary.resolution is active.mappings[0]
    assert boundary.previous_resolution.evidence is absent.evidence
    assert boundary.resolution.evidence is active.evidence


def test_stable_identity_and_per_day_metadata_versions_do_not_roll() -> None:
    next_day = date(2026, 11, 20)
    previous = daily(DAY)
    revised = tuple(replace(c, delist_date=date(2029, 1, 1)) for c in metadata())
    current = resolve_daily_slots("IM", next_day, revised, evidence=proof(next_day, revised))
    result = detect_contract_transitions("IM", sessions(DAY, next_day), (previous, current))
    assert result.transitions == result.absence_boundaries == ()
    assert previous.mappings[0].contract != current.mappings[0].contract
    assert previous.evidence.source_export_ref != current.evidence.source_export_ref


@pytest.mark.parametrize("complete", [False, 1, "true", None])
def test_incomplete_or_untyped_proof_is_not_empty_proof(complete: Any) -> None:
    evidence = replace(proof(DAY, ()), complete=complete)
    with pytest.raises(SlotResolutionError) as exc:
        resolve_daily_slots("IM", DAY, (), evidence=evidence)
    assert exc.value.category == "invalid_evidence"
    assert exc.value.evidence is evidence
    assert exc.value.metadata == ()


def test_missing_proof_is_explicit_failure_with_identity() -> None:
    with pytest.raises(SlotResolutionError) as exc:
        resolve_daily_slots("IM", DAY, (), evidence=None)
    assert exc.value.category == "missing_completeness_evidence"
    assert (exc.value.product_code, exc.value.trade_date) == ("IM", DAY)


@pytest.mark.parametrize(
    "changes",
    [
        {"product_code": "IF"},
        {"trade_date": date(2026, 11, 20)},
        {"trade_date": datetime(2026, 11, 19)},
        {"source_export_ref": ""},
        {"active_contract_codes": ()},
        {"active_contract_codes": ("IM2611.CFX",) * 4},
        {"active_contract_codes": ["IM2611.CFX"]},
        {"active_contract_codes": ([],)},
    ],
)
def test_bad_evidence_association(changes: dict[str, Any]) -> None:
    contracts = metadata()
    with pytest.raises(SlotResolutionError) as exc:
        resolve_daily_slots(
            "IM", DAY, contracts, evidence=replace(proof(DAY, contracts), **changes)
        )
    assert exc.value.category == "invalid_evidence"


@pytest.mark.parametrize(
    "changes",
    [
        {"contract_code": "IML.CFX"},
        {"contract_code": "IM2610.CFX"},
        {"product_code": "IF"},
        {"underlying_index_code": "000300.SH"},
        {"delivery_month": "202613"},
        {"delivery_month": "202600"},
        {"delivery_month": "000011"},
        {"delivery_month": "２０２６１１"},
        {"delivery_month": 202611},
        {"delivery_month": "2026-11"},
        {"list_date": date(2026, 11, 20)},
        {"delist_date": date(2026, 11, 18)},
        {"list_date": datetime(2025, 1, 1)},
        {"delist_date": datetime(2028, 12, 31)},
        {"list_date": date(2029, 1, 1), "delist_date": date(2025, 1, 1)},
    ],
)
def test_invalid_metadata(changes: dict[str, Any]) -> None:
    contracts = metadata()
    contracts = (replace(contracts[0], **changes), *contracts[1:])
    with pytest.raises(SlotResolutionError) as exc:
        resolve_daily_slots("IM", DAY, contracts, evidence=proof(DAY, contracts))
    assert exc.value.category == "invalid_contract_metadata"
    assert "contracts[0]" in exc.value.reason
    assert exc.value.metadata is contracts


@pytest.mark.parametrize(
    "months",
    [
        BEFORE[:3],
        (*BEFORE, "202709"),
        ("202611", "202701", "202703", "202706"),
        ("202611", "202612", "202706", "202709"),
        ("202603", "202604", "202605", "202609"),
        ("202603", "202604", "202606", "202612"),
    ],
)
def test_no_month_structure_fallback(months: tuple[str, ...]) -> None:
    contracts = metadata(months)
    with pytest.raises(SlotResolutionError) as exc:
        resolve_daily_slots("IM", DAY, contracts, evidence=proof(DAY, contracts))
    assert exc.value.category == "invalid_month_structure"


def test_duplicate_contracts_and_months_are_never_deduplicated() -> None:
    contracts = metadata()
    duplicate = (contracts[0], contracts[0], *contracts[2:])
    with pytest.raises(SlotResolutionError):
        resolve_daily_slots("IM", DAY, duplicate, evidence=proof(DAY, duplicate))
    # Even an asserted unique proof cannot hide duplicate metadata.
    with pytest.raises(SlotResolutionError, match="duplicate identity"):
        resolve_daily_slots("IM", DAY, duplicate, evidence=proof(DAY, contracts))
    bad_month = (contracts[0], replace(contracts[1], delivery_month="202611"), *contracts[2:])
    with pytest.raises(SlotResolutionError):
        resolve_daily_slots("IM", DAY, bad_month, evidence=proof(DAY, bad_month))


@pytest.mark.parametrize(
    "product,day", [("im", DAY), ("XX", DAY), ([], DAY), ("IM", datetime(2026, 11, 19))]
)
def test_invalid_request(product: Any, day: Any) -> None:
    with pytest.raises(SlotResolutionError) as exc:
        resolve_daily_slots(product, day, (), evidence=None)
    assert exc.value.category == "invalid_request"


def test_bad_carrier_types_fail_explicitly() -> None:
    with pytest.raises(SlotResolutionError):
        resolve_daily_slots("IM", DAY, metadata(), evidence=True)  # type: ignore[arg-type]
    with pytest.raises(SlotResolutionError):
        resolve_daily_slots("IM", DAY, list(metadata()), evidence=proof(DAY, metadata()))  # type: ignore[arg-type]
    with pytest.raises(SlotResolutionError):
        resolve_daily_slots("IM", DAY, (None,), evidence=proof(DAY, metadata()))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "dates,results",
    [
        ((date(2026, 11, 19), date(2026, 11, 20), date(2026, 11, 23)), (0, 2)),
        ((date(2026, 11, 19), date(2026, 11, 20)), (1, 0)),
        ((date(2026, 11, 19), date(2026, 11, 20)), (0, 2)),
        ((date(2026, 11, 19), date(2026, 11, 19)), (0, 0)),
        ((date(2026, 11, 20), date(2026, 11, 19)), (1, 0)),
        ((datetime(2026, 11, 19),), (0,)),
        ((), (0,)),
    ],
)
def test_candidate_gaps_and_invalid_order_fail_whole_call(
    dates: tuple[date, ...], results: tuple[int, ...]
) -> None:
    available = (daily(DAY), daily(date(2026, 11, 20)), daily(date(2026, 11, 23), AFTER))
    with pytest.raises(SlotResolutionError) as exc:
        detect_contract_transitions("IM", sessions(*dates), tuple(available[i] for i in results))
    assert exc.value.category == "invalid_resolution_sequence"


def test_transition_input_revalidates_caller_constructed_daily_results() -> None:
    original = daily(DAY)
    variants = [
        replace(original, product_code="IF"),
        replace(original, mappings=tuple(reversed(original.mappings))),
        replace(original, mappings=original.mappings[:3]),
        replace(
            original,
            mappings=(
                replace(original.mappings[0], status="not_applicable"),
                *original.mappings[1:],
            ),
        ),
        replace(
            original,
            mappings=(
                replace(
                    original.mappings[0],
                    evidence=replace(original.evidence, source_export_ref="wrong"),
                ),
                *original.mappings[1:],
            ),
        ),
    ]
    for result in variants:
        with pytest.raises(SlotResolutionError):
            detect_contract_transitions("IM", sessions(DAY), (result,))
    with pytest.raises(SlotResolutionError):
        detect_contract_transitions("IM", CandidateSessions((DAY,), ""), (original,))
    with pytest.raises(SlotResolutionError):
        detect_contract_transitions("IM", sessions(DAY), (daily(DAY, product="IF"),))
    assert detect_contract_transitions("IM", sessions(), ()).transitions == ()
    assert detect_contract_transitions("IM", sessions(DAY), (original,)).transitions == ()


def test_quotes_volume_and_open_interest_are_outside_the_resolver() -> None:
    contracts = metadata()
    evidence = proof(DAY, contracts)
    variants: tuple[dict[str, Any], ...] = (
        {},
        {"close": None, "volume": 0, "open_interest": 0},
        {"close": 1234.0, "volume": 100000, "open_interest": 250000},
    )
    outcomes = []
    for quotes in variants:
        synthetic_day: dict[str, Any] = {
            "metadata": contracts,
            "evidence": evidence,
            "quotes": quotes,
        }
        outcomes.append(
            resolve_daily_slots(
                "IM", DAY, synthetic_day["metadata"], evidence=synthetic_day["evidence"]
            )
        )
    assert outcomes[0] == outcomes[1] == outcomes[2]
    assert tuple(inspect.signature(resolve_daily_slots).parameters) == (
        "product_code",
        "trade_date",
        "contracts",
        "evidence",
    )
    assert {f.name for f in fields(ContractMetadata)} == {
        "contract_code",
        "product_code",
        "underlying_index_code",
        "delivery_month",
        "list_date",
        "delist_date",
    }
    assert {f.name for f in fields(DailyUniverseEvidence)} == {
        "product_code",
        "trade_date",
        "complete",
        "active_contract_codes",
        "source_export_ref",
    }


def test_mapping_evidence_cannot_exploit_bool_integer_equality() -> None:
    original = daily(DAY)
    bad_evidence = replace(original.evidence, complete=1)  # type: ignore[arg-type]
    tampered = replace(
        original,
        mappings=(replace(original.mappings[0], evidence=bad_evidence), *original.mappings[1:]),
    )
    with pytest.raises(SlotResolutionError, match="invalid mapping evidence"):
        detect_contract_transitions("IM", sessions(DAY), (tampered,))


def test_public_boundary_has_no_io_or_sibling_dependencies() -> None:
    root = Path(futures_basis.__file__).parent
    for source in (root / "models.py", root / "resolution.py"):
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(n.name in {"dataclasses", "datetime", "typing"} for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert node.module in {"dataclasses", "datetime", "typing"}
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "exec", "eval", "__import__"}
    assert futures_basis.resolve_daily_slots is resolve_daily_slots
    assert futures_basis.detect_contract_transitions is detect_contract_transitions
    assert DailySlotResolution.__module__.startswith(
        "market_research.descriptive.cases.futures_basis"
    )
