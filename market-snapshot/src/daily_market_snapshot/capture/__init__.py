"""Source Capture implementations.

Each module owns one Source Capture: its endpoint query, query parameters,
Source-domain scope selection, minimal normalization and Raw artifact records.
Captures never know an analyzer-specific transformation (``ARCHITECTURE.md`` 2).
"""
