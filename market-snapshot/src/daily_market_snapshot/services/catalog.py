"""The explicit, static Data Service catalog.

Authority: ``guides/data-services.md`` section 2. The catalog is written out by
hand and is never discovered by scanning the filesystem, and there is no dynamic
registry, plugin discovery or service lifecycle framework: the first version
holds exactly one Data Service.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..sources import tushare
from . import csi1000_5d_analysis

# The per-service implementation binding of a catalog entry: it runs the whole
# Data Service orchestration for one target trade date and returns the path of
# the canonical user-facing artifact.
Orchestration = Callable[[tushare.TushareApi, str], Path]


@dataclass(frozen=True)
class DataService:
    """One catalog entry: what the service is and how to execute it."""

    service_id: str
    description: str
    run: Orchestration


CATALOG: tuple[DataService, ...] = (
    DataService(
        service_id=csi1000_5d_analysis.SERVICE_ID,
        description=csi1000_5d_analysis.SERVICE_DESCRIPTION,
        run=csi1000_5d_analysis.run_csi1000_5d_analysis,
    ),
)


def find_service(service_id: str) -> DataService | None:
    """Return the catalog entry of ``service_id``, or ``None`` if unsupported."""
    for service in CATALOG:
        if service.service_id == service_id:
            return service
    return None
