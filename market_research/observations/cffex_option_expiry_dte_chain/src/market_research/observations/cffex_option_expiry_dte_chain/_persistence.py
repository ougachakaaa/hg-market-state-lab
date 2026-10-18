"""This Observation's business key and complete Artifact storage."""

from pathlib import Path

from .._codec import decode, encode
from .._sqlite import publish_payload, read_payload
from ._models import ExpiryDteChainArtifact, ExpiryDteChainRequest

DDL = """CREATE TABLE artifacts (
    product_code TEXT NOT NULL, expiry_date TEXT NOT NULL, target_dte INTEGER NOT NULL,
    payload TEXT NOT NULL, PRIMARY KEY (product_code, expiry_date, target_dte))"""
QUERY = "SELECT payload FROM artifacts WHERE product_code=? AND expiry_date=? AND target_dte=?"
INSERT = "INSERT INTO artifacts VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING"


def key(request: ExpiryDteChainRequest) -> tuple[object, ...]:
    return (request.product_code, request.expiry_date.isoformat(), request.target_dte)


def load(path: Path, request: ExpiryDteChainRequest) -> ExpiryDteChainArtifact | None:
    payload = read_payload(path, QUERY, key(request))
    return None if payload is None else decode(ExpiryDteChainArtifact, payload)


def publish(
    path: Path, request: ExpiryDteChainRequest, artifact: ExpiryDteChainArtifact
) -> ExpiryDteChainArtifact:
    payload = publish_payload(path, DDL, INSERT, QUERY, key(request), encode(artifact))
    return decode(ExpiryDteChainArtifact, payload)
