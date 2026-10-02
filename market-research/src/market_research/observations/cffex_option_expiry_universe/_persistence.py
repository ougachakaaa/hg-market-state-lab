"""This Observation's business key and complete Artifact storage."""

from pathlib import Path

from .._codec import decode, encode
from .._sqlite import publish_payload, read_payload
from ._models import ExpiryUniverseArtifact, ExpiryUniverseRequest

DDL = """CREATE TABLE artifacts (
    product_code TEXT NOT NULL, expiry_start_date TEXT NOT NULL, expiry_end_date TEXT NOT NULL,
    payload TEXT NOT NULL, PRIMARY KEY (product_code, expiry_start_date, expiry_end_date))"""
QUERY = """SELECT payload FROM artifacts
           WHERE product_code=? AND expiry_start_date=? AND expiry_end_date=?"""
INSERT = "INSERT INTO artifacts VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING"


def key(request: ExpiryUniverseRequest) -> tuple[object, ...]:
    return (
        request.product_code,
        request.expiry_start_date.isoformat(),
        request.expiry_end_date.isoformat(),
    )


def load(path: Path, request: ExpiryUniverseRequest) -> ExpiryUniverseArtifact | None:
    payload = read_payload(path, QUERY, key(request))
    return None if payload is None else decode(ExpiryUniverseArtifact, payload)


def publish(
    path: Path, request: ExpiryUniverseRequest, artifact: ExpiryUniverseArtifact
) -> ExpiryUniverseArtifact:
    payload = publish_payload(path, DDL, INSERT, QUERY, key(request), encode(artifact))
    return decode(ExpiryUniverseArtifact, payload)
