"""``market_snapshot``: co-located market data product contexts.

Implementation areas (see ``market-snapshot/ARCHITECTURE.md``):

    sources/       Source integration (Tushare credentials / client)
    capture/       shared Source Capture endpoints and minimal normalization
    products/      product-owned Capture adapters, Preparation and application boundaries
    artifacts.py   shared local artifact filesystem capability
"""
