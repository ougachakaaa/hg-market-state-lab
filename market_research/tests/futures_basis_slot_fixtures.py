"""Fixed artificial metadata/evidence; never call a market provider."""

from datetime import date

from market_research.descriptive.cases.futures_basis import (
    CandidateSessions,
    ContractMetadata,
    DailySlotResolution,
    DailyUniverseEvidence,
    resolve_daily_slots,
)

BEFORE = ("202611", "202612", "202703", "202706")
AFTER = ("202612", "202701", "202703", "202706")
MARCH = ("202603", "202604", "202606", "202609")
UNDERLYING = {"IF": "000300.SH", "IH": "000016.SH", "IC": "000905.SH", "IM": "000852.SH"}


def metadata(months: tuple[str, ...] = BEFORE, product: str = "IM") -> tuple[ContractMetadata, ...]:
    return tuple(
        ContractMetadata(
            f"{product}{month[2:]}.CFX",
            product,
            UNDERLYING[product],
            month,
            date(2025, 1, 1),
            date(2028, 12, 31),
        )
        for month in months
    )


def proof(
    day: date,
    contracts: tuple[ContractMetadata, ...],
    product: str = "IM",
) -> DailyUniverseEvidence:
    return DailyUniverseEvidence(
        product,
        day,
        True,
        tuple(c.contract_code for c in contracts),
        f"synthetic-final-futures-export:{product}:{day.isoformat()}",
    )


def daily(day: date, months: tuple[str, ...] = BEFORE, product: str = "IM") -> DailySlotResolution:
    contracts = metadata(months, product)
    return resolve_daily_slots(product, day, contracts, evidence=proof(day, contracts, product))


def sessions(*days: date) -> CandidateSessions:
    return CandidateSessions(days, "synthetic-final-cffex-calendar-export")
