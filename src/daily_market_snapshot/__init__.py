"""``daily_market_snapshot``: market data product for external analyzers.

Layers (see ``ARCHITECTURE.md`` section 9):

    sources/       Source integration (Tushare credentials / client)
    capture/       Source Capture: endpoint query, scope, minimal normalization
    preparation/   Analysis Preparation: deterministic Raw -> analysis-ready
    services/      Data Service orchestration and the explicit service catalog
    artifacts.py   shared local artifact filesystem capability
    cli.py         CLI over the Data Service catalog
"""
