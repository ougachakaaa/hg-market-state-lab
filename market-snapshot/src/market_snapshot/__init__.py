"""``market_snapshot``: co-located market data product contexts.

Layers (see ``ARCHITECTURE.md`` section 9):

    sources/       Source integration (Tushare credentials / client)
    capture/       shared Source Capture endpoints and minimal normalization
    services/      shared Data Service catalog, CLI and persisted delivery
    products/      product-owned Capture adapters, Preparation and application boundaries
    artifacts.py   shared local artifact filesystem capability
    cli.py         thin CLI adapter over the Data Service catalog
"""
