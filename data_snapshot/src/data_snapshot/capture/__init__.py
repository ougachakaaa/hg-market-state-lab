"""Source Capture implementations.

Each module owns one Source Capture: its endpoint query, query parameters,
Source-domain scope selection, minimal normalization and Raw artifact records.
Each module exposes Product-appropriate Capture functions, so a caller asks
for a Capture instead of binding a Source endpoint itself. Captures never know an
analyzer-specific transformation (``ARCHITECTURE.md``).
"""
