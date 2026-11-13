"""Private D3-R2 acquisition and credential-free evidence verification.

Run with root Poetry. No financial formula or alternate transport schema lives here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from data_snapshot.products.mo_option_chain import service as chain
from data_snapshot.products.mo_option_premium import service as premium
from ui_http.products.mo_option_chain.endpoint import to_chain_dto
from ui_http.products.mo_option_chain.schemas import OptionChainDTO
from ui_http.products.mo_option_premium.endpoint import project_plane
from ui_http.products.mo_option_premium.schemas import PremiumPlaneResponse

REPO = Path(__file__).resolve().parents[2]
DAY = "2026-11-11"
PROFILE = "d3-r2-private-mo-v1"
PRODUCTS = {"chain": "mo-option-chain", "premium": "mo-option-premium"}
RAW_NAMES = (
    "index_daily",
    "mo_option_basic",
    "mo_option_daily",
    "im_futures_basic",
    "im_futures_daily",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(UTC).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


def isolation(root):
    require(root.is_absolute(), "--output must be absolute")
    root = root.resolve()
    worktrees = [
        Path(line[9:]).resolve()
        for line in git("worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    ]
    for worktree in worktrees:
        require(
            not root.is_relative_to(worktree) and not worktree.is_relative_to(root),
            "package must be outside all worktrees",
        )
        for directory, dirs, files in os.walk(worktree, followlinks=False):
            for name in dirs + files:
                path = Path(directory) / name
                if path.is_symlink():
                    target = path.resolve()
                    require(
                        not root.is_relative_to(target) and not target.is_relative_to(root),
                        "worktree symlink reaches private package",
                    )
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "node_modules"}]
    require(
        "publicDir: false" in (REPO / "ui_web/vite.demo.config.ts").read_text(),
        "review changed Pages build inputs first",
    )
    return root


def checked_file(root, relative):
    path = root / relative
    require(
        not Path(relative).is_absolute() and ".." not in Path(relative).parts,
        "invalid package reference",
    )
    require(path.resolve().is_relative_to(root), "escaped package reference")
    require(path.is_file() and not path.is_symlink(), "missing or symlinked evidence")
    return path


def inventory(root):
    return {
        p.relative_to(root).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size}
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name not in {"manifest.json", "manifest.sha256"}
    }


def verify_inventory(root, records):
    for relative, item in records.items():
        path = checked_file(root, relative)
        require(
            digest(path) == item["sha256"] and path.stat().st_size == item["bytes"],
            f"integrity failure: {relative}",
        )


def frontend(root):
    result = subprocess.run(
        ["node", str(REPO / "ui_web/scripts/validate_private_mo.mjs"), str(root)],
        cwd=REPO / "ui_web",
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def consistency(root, key):
    """Evidence comparisons only: no DTE, Premium metric or market-selection calculation."""
    namespace = PRODUCTS[key]
    raw = root / key / "raw" / namespace / DAY
    facts = {name: read(raw / f"{name}.json") for name in RAW_NAMES}
    body = read(root / key / "response.json")
    dto = OptionChainDTO if key == "chain" else PremiumPlaneResponse
    require(
        dto.model_validate(body).model_dump(mode="json", by_alias=True) == body,
        "published DTO mismatch",
    )
    require(body["option_product"] == "MO" and body["price_type"] == "close", "wrong product/price")
    require(
        (body.get("target_trade_date") if key == "chain" else body["observation"]["value"]) == DAY,
        "wrong observation",
    )
    require(key == "chain" or body["observation"]["kind"] == "trade_date", "wrong observation kind")
    require(body["underlying"]["instrument_id"] == "000852.SH", "wrong underlying")
    index = [
        r for r in facts["index_daily"] if r["ts_code"] == "000852.SH" and r["trade_date"] == DAY
    ]
    require(
        len(index) == 1 and index[0]["close"] == body["underlying"]["price"],
        "underlying source mismatch",
    )
    # Captures already own active-universe selection; check retained lifecycle proof
    # rather than building another option-universe selector.
    basic = facts["mo_option_basic"]
    require(
        all(
            r["exchange"] == "CFFEX"
            and r["opt_code"] == "OP000852.SH"
            and r["list_date"] <= DAY <= r["delist_date"]
            for r in basic
        ),
        "invalid captured MO lifecycle",
    )
    by_id = {r["ts_code"]: r for r in basic}
    require(len(by_id) == len(basic) > 0, "duplicate/empty basic")
    daily = facts["mo_option_daily"]
    require(all(r["trade_date"] == DAY for r in daily), "daily date mismatch")
    daily_ids = [r["ts_code"] for r in daily]
    require(
        len(daily_ids) == len(set(daily_ids)) and set(daily_ids) == set(by_id),
        "incomplete daily identities",
    )
    quotes = {r["ts_code"]: r for r in daily}
    groups = body["expiries"]
    dates = [g["expiry_date"] for g in groups]
    require(dates == sorted(set(dates)), "expiry ordering/duplicates")
    require(set(dates) == {r["maturity_date"] for r in basic}, "expiry coverage mismatch")
    flattened = []
    if key == "chain":
        for group in groups:
            for side, field in [("call", "calls"), ("put", "puts")]:
                points = group[field]
                require(
                    points == sorted(points, key=lambda p: (p["strike"], p["instrument_id"])),
                    "chain point order",
                )
                flattened.extend((p, group["expiry_date"], side, p["price"]) for p in points)
    else:
        points = body["points"]
        require(len(points) > 0, "empty Premium Points")
        require(
            points
            == sorted(
                points,
                key=lambda p: (
                    p["expiry_date"],
                    p["option_type"] == "put",
                    p["strike"],
                    p["instrument_id"],
                ),
            ),
            "Premium ordering",
        )
        flattened = [(p, p["expiry_date"], p["option_type"], p["premium"]) for p in points]
        coordinates = [(p["expiry_date"], p["strike"], p["option_type"]) for p in points]
        require(len(coordinates) == len(set(coordinates)), "duplicate Premium coordinates")
    identities = [p["instrument_id"] for p, *_ in flattened]
    require(
        len(identities) == len(set(identities)) and set(identities) == set(by_id),
        "result contract coverage mismatch",
    )
    for point, expiry, side, price in flattened:
        contract = by_id[point["instrument_id"]]
        require(
            contract["maturity_date"] == expiry
            and contract["call_put"] == {"call": "C", "put": "P"}[side],
            "contract context mismatch",
        )
        require(
            contract["exercise_price"] == point["strike"]
            and quotes[point["instrument_id"]].get("close") == price,
            "strike/selected price altered",
        )
    futures_daily = facts["im_futures_daily"]
    require(all(r["trade_date"] == DAY for r in futures_daily), "IM daily observation mismatch")
    require(len({r["ts_code"] for r in futures_daily}) == len(futures_daily), "duplicate IM daily")
    for group in groups:
        matches = [
            r
            for r in facts["im_futures_basic"]
            if r["fut_code"] == "IM"
            and r["exchange"] == "CFFEX"
            and r["list_date"] <= DAY <= r["delist_date"]
            and r["delist_date"] == group["expiry_date"]
        ]
        require(len(matches) <= 1, "ambiguous IM reference")
        if not matches:
            require(group["futures"] is None, "fabricated IM reference")
        else:
            rows = [r for r in futures_daily if r["ts_code"] == matches[0]["ts_code"]]
            require(
                len(rows) == 1
                and group["futures"]
                == {"instrument_id": matches[0]["ts_code"], "price": rows[0]["close"]},
                "IM reference mismatch",
            )
    return {
        "contracts": len(identities),
        "expiries": len(dates),
        "points": len(flattened) if key == "premium" else None,
        "futures_references": sum(g["futures"] is not None for g in groups),
        "futures_absences": sum(g["futures"] is None for g in groups),
        "null_selected_prices": sum(price is None for *_, price in flattened),
        "zero_selected_prices": sum(price == 0 for *_, price in flattened),
    }


class AuditedSource:
    """Delegate every request to the real configured client; retain no credentials."""

    def __init__(self, api):
        self.api = api
        self.calls = []

    def __getattr__(self, endpoint):
        require(
            endpoint in {"index_daily", "opt_basic", "opt_daily", "fut_basic", "fut_daily"},
            "unexpected source endpoint",
        )

        def call(**kwargs):
            record = {"endpoint": endpoint, "query": kwargs, "started_at": now()}
            self.calls.append(record)
            try:
                frame = getattr(self.api, endpoint)(**kwargs)
                record.update(status="PASS", rows=len(frame))
                return frame
            except Exception:
                record["status"] = "FAIL"
                raise
            finally:
                record["finished_at"] = now()

        return call


def retain_r1(root, previous):
    previous = isolation(previous)
    index = read(previous / "evidence-index.json")
    require(index["id"] == "D3-R1-local-20261113", "wrong R1 evidence identity")
    names = ["provider.json", "input_checks.json"] + [
        f"raw/{namespace}/{DAY}/{name}.json"
        for namespace in PRODUCTS.values()
        for name in RAW_NAMES
    ]
    verify_inventory(previous, {name: index["artifacts"][name] for name in names})
    shutil.copyfile(previous / "evidence-index.json", root / "r1-index.json")
    for name in names:
        target = root / "r1" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(previous / name, target)
    return {"identity": index["id"], "index": "r1-index.json", "retained_references": names}


def acquire(root, r1):
    from data_snapshot.sources import tushare

    root = isolation(root)
    require(not root.exists(), "use a new private output directory; no overwrite")
    root.mkdir(mode=0o700, parents=True)
    os.umask(0o077)
    source_revision = git("rev-parse", "HEAD")
    r1_record = retain_r1(root, r1)
    for name in ("private_mo_examples.py", "validate_private_mo.mjs"):
        target = root / "tooling" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / "ui_web/scripts" / name, target)
    manifest = {
        "profile": PROFILE,
        "example_revision": 1,
        "identity": "D3-R2-local-20261113-v1",
        "classification": "real_market",
        "source_revision": source_revision,
        "created_at": now(),
        "publication_rights": "BLOCKED",
        "r1": r1_record,
        "examples": {},
        "tooling": ["tooling/private_mo_examples.py", "tooling/validate_private_mo.mjs"],
        "build_isolation_review": {
            "external_owner_only_root": True,
            "worktree_symlinks_checked": True,
            "credentials_persisted": False,
            "vite_demo_config_sha256": digest(REPO / "ui_web/vite.demo.config.ts"),
            "pages_workflow_sha256": digest(REPO / ".github/workflows/deploy-demo-pages.yml"),
        },
        "input_digest_kind": (
            "Demo SHA-256 artifact binding; not an official Product input fingerprint"
        ),
        "limitations": [
            "Source facts are minimally normalized Capture output, not signed exchange evidence.",
            (
                "No published pure offline Product Service replay boundary; "
                "metrics protected by hashes and schema, not independently recomputed offline."
            ),
            (
                "Full financial replay requires explicit live reacquisition "
                "through canonical Services."
            ),
            "Redistribution rights remain BLOCKED per R1; private local research only.",
        ],
    }
    api = tushare.create_tushare_api(tushare.get_tushare_token())
    for key, namespace in PRODUCTS.items():
        source = AuditedSource(api)
        raw_root = root / key / "raw"
        started = now()
        if key == "chain":
            query = chain.ChainQuery(DAY, chain.OptionProduct.MO, chain.PriceType.CLOSE)
            result = chain.read_chain_with_api(source, query, raw_root)
            dto = to_chain_dto(result.chain) if result.error is None else None
        else:
            query = premium.PremiumPlaneQuery(
                DAY, premium.OptionProduct.MO, premium.PriceType.CLOSE
            )
            result = premium.read_premium_plane_with_api(source, query, raw_root)
            dto = project_plane(result.plane) if result.error is None else None
        write(root / key / "source-calls.json", source.calls)
        if result.error is not None:
            # Provider exception text can contain credentials; preserve category safely.
            write(
                root / key / "failure.json",
                {
                    "kind": result.error.kind,
                    "stage": "canonical_product_service",
                    "finished_at": now(),
                },
            )
            raise RuntimeError(
                f"{key}: classified failure {result.error.kind}; private captures retained"
            )
        # Preserve all nulls and the published yield alias. No financial JSON edits.
        (root / key / "response.json").write_text(dto.model_dump_json(by_alias=True) + "\n")
        coverage = consistency(root, key)
        old_basic = read(root / "r1" / "raw" / namespace / DAY / "mo_option_basic.json")
        current_basic = read(raw_root / namespace / DAY / "mo_option_basic.json")
        old_ids = {r["ts_code"] for r in old_basic}
        current_ids = {r["ts_code"] for r in current_basic}
        comparison = {
            "r1_contracts": len(old_ids),
            "r2_contracts": len(current_ids),
            "added": sorted(current_ids - old_ids),
            "removed": sorted(old_ids - current_ids),
            "raw_byte_equal": {
                name: digest(root / "r1" / "raw" / namespace / DAY / f"{name}.json")
                == digest(raw_root / namespace / DAY / f"{name}.json")
                for name in RAW_NAMES
            },
        }
        write(root / key / "r1-comparison.json", comparison)
        manifest["examples"][key] = {
            "identity": f"{PROFILE}:{key}:revision-1",
            "classification": "real_market",
            "query": {
                "target_trade_date" if key == "chain" else "as_of": DAY,
                "option_product": "MO",
                "price_type": "close",
            },
            "provider": "Tushare",
            "datasets": list(RAW_NAMES),
            "source_endpoints": sorted({c["endpoint"] for c in source.calls}),
            "acquisition_started_at": started,
            "acquisition_finished_at": now(),
            "service": "data_snapshot.products.mo_option_"
            + ("chain" if key == "chain" else "premium")
            + ".service."
            + ("read_chain_with_api" if key == "chain" else "read_premium_plane_with_api"),
            "source_revision": source_revision,
            "projection": "ui_http.products.mo_option_"
            + (
                "chain.endpoint.to_chain_dto"
                if key == "chain"
                else "premium.endpoint.project_plane"
            ),
            "response": f"{key}/response.json",
            "result_sha256": digest(root / key / "response.json"),
            "raw_references": [f"{key}/raw/{namespace}/{DAY}/{name}.json" for name in RAW_NAMES],
            "source_calls": f"{key}/source-calls.json",
            "r1_comparison": f"{key}/r1-comparison.json",
            "coverage": coverage,
            "python_product_execution": "PASS",
            "http_projection": "PASS",
            "source_acquisition": "PASS",
            "contract_validation": "PASS",
            "publication_rights": "BLOCKED",
        }
        print(f"{key}: Product PASS; coverage {coverage}", flush=True)
    manifest["frontend_validation"] = frontend(root)
    write(root / "frontend-validation.json", manifest["frontend_validation"])
    manifest["artifacts"] = inventory(root)
    write(root / "manifest.json", manifest)
    (root / "manifest.sha256").write_text(digest(root / "manifest.json") + "\n")
    verify(root)


def verify(root):
    # Python checks cannot contact a Source, including accidental future imports.
    import socket

    def offline(*args, **kwargs):
        raise RuntimeError("network disabled during offline verification")

    socket.socket.connect = offline
    socket.create_connection = offline
    root = isolation(root)
    require(
        digest(root / "manifest.json") == (root / "manifest.sha256").read_text().strip(),
        "manifest digest mismatch",
    )
    manifest = read(root / "manifest.json")
    require(
        manifest["profile"] == PROFILE and manifest["example_revision"] == 1,
        "unsupported package profile",
    )
    require(
        manifest["identity"] == "D3-R2-local-20261113-v1"
        and manifest["classification"] == "real_market",
        "wrong package identity",
    )
    require(manifest["publication_rights"] == "BLOCKED", "package is private only")
    require(set(manifest["examples"]) == set(PRODUCTS), "missing Product association")
    require(inventory(root) == manifest["artifacts"], "inventory mismatch or unlisted file")
    verify_inventory(root, manifest["artifacts"])
    r1_index = read(root / manifest["r1"]["index"])
    require(
        r1_index["id"] == manifest["r1"]["identity"] == "D3-R1-local-20261113",
        "R1 association mismatch",
    )
    verify_inventory(
        root / "r1",
        {name: r1_index["artifacts"][name] for name in manifest["r1"]["retained_references"]},
    )
    for key, namespace in PRODUCTS.items():
        example = manifest["examples"][key]
        require(example["identity"] == f"{PROFILE}:{key}:revision-1", "example identity mismatch")
        require(
            example["source_revision"] == manifest["source_revision"], "producer revision mismatch"
        )
        require(
            example["query"]
            == {
                "target_trade_date" if key == "chain" else "as_of": DAY,
                "option_product": "MO",
                "price_type": "close",
            },
            "manifest query mismatch",
        )
        require(example["response"] == f"{key}/response.json", "wrong result association")
        require(
            example["raw_references"]
            == [f"{key}/raw/{namespace}/{DAY}/{name}.json" for name in RAW_NAMES],
            "wrong Raw association",
        )
        require(
            example["result_sha256"] == digest(checked_file(root, example["response"])),
            "result digest mismatch",
        )
        calls = read(checked_file(root, example["source_calls"]))
        require(calls and all(c["status"] == "PASS" for c in calls), "failed Source call")
        require(
            set(c["endpoint"] for c in calls)
            == {"index_daily", "opt_basic", "opt_daily", "fut_basic", "fut_daily"},
            "incomplete source endpoints",
        )
        for c in calls:
            require(
                datetime.fromisoformat(c["started_at"]).tzinfo is not None
                and datetime.fromisoformat(c["finished_at"])
                >= datetime.fromisoformat(c["started_at"]),
                "invalid acquisition time",
            )
        require(consistency(root, key) == example["coverage"], "coverage record mismatch")
    require(frontend(root) == manifest["frontend_validation"], "frontend validation changed")
    print(
        json.dumps(
            {
                "verification": "PASS",
                "manifest_sha256": digest(root / "manifest.json"),
                "frontend": manifest["frontend_validation"],
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["acquire", "verify"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--r1", type=Path)
    args = parser.parse_args()
    if args.operation == "acquire":
        require(args.r1 is not None, "acquire requires the located --r1 evidence path")
        acquire(args.output, args.r1)
    else:
        verify(args.output)
