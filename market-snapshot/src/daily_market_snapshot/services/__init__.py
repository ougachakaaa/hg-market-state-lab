"""Data Service orchestration and the explicit, static Data Service catalog.

A service runs the required Source Captures, writes Raw Artifacts, calls Analysis
Preparation and publishes the canonical analysis-ready artifact
(``ARCHITECTURE.md`` 2, ``services/ARCHITECTURE.md``).
"""

from __future__ import annotations


class DataServiceError(Exception):
    """Raised when a Data Service request cannot be completed as requested.

    A service reports its stage failures with this type, so the CLI can present
    any Data Service failure without knowing the stages of that service.
    """
