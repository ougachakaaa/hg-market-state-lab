"""Explicit authenticated HTTP capture. Run from the repository Poetry environment."""

from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx

from lab_config import auth_settings

WEB = Path(__file__).resolve().parents[2]
ACTIVE = WEB / "demo/bundles"
WORK = WEB / ".build/demo-collection"


class CollectionError(Exception):
    """Safe diagnostic suitable for terminal output."""


class Bridge:
    def __enter__(self):
        self.process = subprocess.Popen(
            ["node", str(WEB / "scripts/demo_collect_bridge.mjs")],
            cwd=WEB,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        return self

    def call(self, op, **arguments):
        try:
            self.process.stdin.write(json.dumps({"op": op, **arguments}) + "\n")
            self.process.stdin.flush()
            response = json.loads(self.process.stdout.readline())
        except (OSError, ValueError):
            raise CollectionError("bridge tooling_failed") from None
        if not response["ok"]:
            location = (
                " field=" + json.dumps(response["fieldPath"], ensure_ascii=True)
                if "fieldPath" in response
                else ""
            )
            raise CollectionError("bridge " + response["reason"] + location)
        return response["data"]

    def __exit__(self, *_):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stdout.close()


def preflight(directory):
    result = subprocess.run(
        ["node", str(WEB / "scripts/demo_check.mjs"), "--dir", str(directory)],
        cwd=WEB,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode:
        # Preflight deliberately emits safe fixed diagnostics.
        diagnostic = next(
            (line for line in result.stderr.splitlines() if line.startswith("FAIL ")),
            "FAIL dataset preflight failed",
        )
        raise CollectionError(diagnostic)


def reject_links(path):
    for item in (path, *path.parents):
        if item.is_symlink() or item.is_junction():
            raise CollectionError("transaction linked_path")


@contextmanager
def dataset_lock(work):
    reject_links(work)
    work.mkdir(parents=True, exist_ok=True)
    path = work / "dataset.lock"
    reject_links(path)
    with path.open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise CollectionError("dataset busy") from None
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def durable_write(path, data):
    reject_links(path)
    with path.open("wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finish_transaction(active, work, registry):
    marker = work / "pending.json"
    reject_links(marker)
    if not marker.exists():
        return
    try:
        journal = json.loads(marker.read_bytes())
        name = journal["candidate"]
        if (
            not isinstance(name, str)
            or Path(name).name != name
            or not name.startswith("candidate-")
        ):
            raise ValueError
        candidate = work / name
        reject_links(candidate)
        replacements = journal["replacements"]
        allowed = {item["path"] for item in registry}
        if (
            not isinstance(replacements, list)
            or not replacements
            or len(set(replacements)) != len(replacements)
            or any(item not in allowed for item in replacements)
        ):
            raise ValueError
        expected = journal["hashes"]
        if not isinstance(expected, dict) or set(expected) != allowed | {"manifest.json"}:
            raise ValueError
        for filename, sha in expected.items():
            reject_links(candidate / filename)
            if digest(candidate / filename) != sha:
                raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise CollectionError("transaction corrupt_pending_requires_repair") from None
    preflight(candidate)
    reject_links(active)
    active.mkdir(parents=True, exist_ok=True)
    # Unselected files must still belong to the validated candidate.
    for filename in allowed - set(replacements):
        reject_links(active / filename)
        if not (active / filename).is_file() or digest(active / filename) != expected[filename]:
            raise CollectionError("transaction unchanged_file_mismatch")
    for filename in [*replacements, "manifest.json"]:
        target = active / filename
        reject_links(target)
        temporary = work / "replacement.tmp"
        durable_write(temporary, (candidate / filename).read_bytes())
        os.replace(temporary, target)
    preflight(active)
    marker.unlink()
    shutil.rmtree(candidate)


def commit_candidate(candidate, active, work, selected, registry):
    files = [item["path"] for item in registry] + ["manifest.json"]
    for filename in files:
        with (candidate / filename).open("r+b") as handle:
            os.fsync(handle.fileno())
    journal = {
        "candidate": candidate.name,
        "replacements": selected,
        "hashes": {name: digest(candidate / name) for name in files},
    }
    temporary = work / "journal.tmp"
    durable_write(temporary, json.dumps(journal).encode("utf-8"))
    os.replace(temporary, work / "pending.json")
    finish_transaction(active, work, registry)


def reference(response, field=None):
    result = {"$ref": response["ref"]}
    if field:
        result["field"] = field
    return result


class Collector:
    def __init__(self, bridge, client, origin, poll_interval, timeout, request_timeout):
        self.bridge, self.client, self.origin = bridge, client, origin
        self.poll_interval, self.timeout, self.request_timeout = (
            poll_interval,
            timeout,
            request_timeout,
        )

    def request(
        self,
        method,
        route,
        *,
        parameters=None,
        body=None,
        ids=(),
        expected_run=None,
        expected_request=None,
        expected_result_status=None,
        timeout=None,
    ):
        path = route
        for key, value in ids:
            path = path.replace("{" + key + "}", quote(value, safe=""))
        try:
            response = self.client.request(
                method,
                path,
                params=parameters,
                json=body,
                headers={"Origin": self.origin} if method == "post" else {},
                timeout=timeout or self.request_timeout,
            )
        except httpx.HTTPError:
            reason = (
                "submit_outcome_unknown"
                if method == "post" and route.endswith("/runs")
                else "connection_failed"
            )
            raise CollectionError("http " + reason) from None
        expected_status = 202 if method == "post" and route.endswith("/runs") else 200
        if response.status_code != expected_status:
            raise CollectionError(f"http status_{response.status_code}")
        return self.bridge.call(
            "response",
            route=route,
            method=method,
            status=response.status_code,
            bytes=base64.b64encode(response.content).decode("ascii"),
            expectedRun=expected_run,
            expectedRequest=expected_request,
            expectedResultStatus=expected_result_status,
        )

    def login(self, username, password):
        identity = self.request(
            "post", "/auth/login", body={"username": username, "password": password}
        )
        if not self.client.cookies:
            raise CollectionError("auth missing_cookie")
        current = self.request("get", "/auth/me")
        if current["id"] != identity["id"]:
            raise CollectionError("auth identity_mismatch")

    def run(self, root, preset):
        accepted = self.request("post", root, body=preset)
        request = accepted["request"]
        if any(request.get(key) != value for key, value in preset.items()):
            raise CollectionError("run preset_mismatch")
        run_id = accepted["run_id"]
        ids = (("run_id", run_id),)
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CollectionError("run poll_timeout")
            state = self.request(
                "get",
                root + "/{run_id}",
                ids=ids,
                expected_run=run_id,
                expected_request=request,
                timeout=min(remaining, self.request_timeout),
            )
            if time.monotonic() >= deadline:
                raise CollectionError("run poll_timeout")
            if state["status"] == "COMPLETED":
                break
            if state["status"] not in ("PENDING", "RUNNING"):
                raise CollectionError("run terminal_failure")
            time.sleep(min(self.poll_interval, max(0, deadline - time.monotonic())))
        suffix = "/report" if root.startswith("/research/") else "/result"
        result = self.request(
            "get",
            root + "/{run_id}" + suffix,
            ids=ids,
            expected_run=run_id,
            expected_request=request,
            expected_result_status=state.get("result_status"),
        )
        return reference(result, "request"), reference(result, "data")

    def capture(self, entry, preset):
        validator = entry["validator"]
        if validator in ("validateEmbeddedReport", "validateEmbeddedBacktestResult"):
            root = (
                "/research/futures-basis/runs"
                if validator == "validateEmbeddedReport"
                else "/backtesting/futures-roll/runs"
            )
            return self.run(root, preset)
        if validator in ("validateOptionChain", "validatePremiumPlane"):
            route = (
                "/mo-option-chain"
                if validator == "validateOptionChain"
                else "/mo-option-premium-plane"
            )
            return preset, reference(self.request("get", route, parameters=preset))
        if validator == "validateEmbeddedCatalog":
            listing = self.request("get", "/research/capabilities")
            identities = listing["capabilities"]
            if len(set(identities)) != len(identities):
                raise CollectionError("catalog duplicate_identity")
            details = [
                reference(self.request("get", "/research/capabilities/{id}", ids=(("id", item),)))
                for item in identities
            ]
            return preset, {"list": reference(listing), "details": details}
        pages, manifests, analyses, views = [], [], [], []
        cursors, publications = set(), set()
        cursor = None
        while True:
            query = dict(preset)
            if cursor is not None:
                query["after"] = cursor
            page = self.request("get", "/research/publications", parameters=query)
            pages.append(reference(page))
            for publication in page["publications"]:
                if publication in publications:
                    raise CollectionError("publications duplicate_identity")
                publications.add(publication)
                ids = (("publication_id", publication),)
                manifest = self.request("get", "/research/publications/{publication_id}", ids=ids)
                manifests.append(reference(manifest, "data"))
                for analysis in manifest["analyses"]:
                    detail = self.request(
                        "get",
                        "/research/publications/{publication_id}/analyses/{analysis_id}",
                        ids=(*ids, ("analysis_id", analysis["id"])),
                    )
                    analyses.append(reference(detail, "data"))
                    for view in analysis["views"]:
                        detail = self.request(
                            "get",
                            "/research/publications/{publication_id}/views/{view_id}",
                            ids=(*ids, ("view_id", view)),
                        )
                        views.append(
                            {
                                "publication_id": publication,
                                "view_id": view,
                                "view": reference(detail, "data"),
                            }
                        )
            cursor = page["next_cursor"]
            if cursor is None:
                break
            if cursor in cursors:
                raise CollectionError("publications repeated_cursor")
            cursors.add(cursor)
        return preset, {
            "pages": pages,
            "manifests": manifests,
            "analyses": analyses,
            "views": views,
        }


def generate(bridge, collector, only=None, active=ACTIVE, work=WORK, authenticate=None):
    configuration = bridge.call("config")
    registry, presets = configuration["registry"], configuration["presets"]
    if only and only not in {item["bundle_id"] for item in registry}:
        raise CollectionError("arguments unknown_bundle")
    with dataset_lock(work):
        finish_transaction(active, work, registry)
        if only:
            preflight(active)
        reject_links(active)
        if active.exists() and any(
            item.name not in {row["path"] for row in registry} | {"manifest.json"}
            for item in active.iterdir()
        ):
            raise CollectionError("dataset unexpected_files")
        if authenticate:
            authenticate()
        candidate = Path(tempfile.mkdtemp(prefix="candidate-", dir=work))
        selected = []
        try:
            for entry in registry:
                if only and entry["bundle_id"] != only:
                    shutil.copyfile(active / entry["path"], candidate / entry["path"])
                    continue
                try:
                    request, result = collector.capture(
                        entry, presets[entry["preset_id"]]["request"]
                    )
                except CollectionError as error:
                    raise CollectionError(entry["bundle_id"] + " " + str(error)) from None
                bridge.call(
                    "bundle",
                    id=entry["bundle_id"],
                    directory=str(candidate),
                    request=request,
                    result=result,
                )
                selected.append(entry["path"])
            bridge.call("manifest", directory=str(candidate))
            preflight(candidate)
            commit_candidate(candidate, active, work, selected, registry)
        finally:
            if candidate.exists() and not (work / "pending.json").exists():
                shutil.rmtree(candidate)


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--all", action="store_true")
    selection.add_argument("--only")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--username")
    parser.add_argument("--poll-interval", type=positive, default=2)
    parser.add_argument("--timeout", type=positive, default=1800)
    parser.add_argument("--request-timeout", type=positive, default=60)
    args = parser.parse_args()
    try:
        address = urlsplit(args.base_url)
        if (
            address.scheme not in ("http", "https")
            or not address.hostname
            or address.username
            or address.password
            or address.query
            or address.fragment
            or address.path not in ("", "/")
        ):
            raise CollectionError("arguments invalid_base_url")
        origin = auth_settings().lab_auth_origin
        if not origin:
            raise CollectionError("auth missing_origin")
        username = args.username or input("Username: ")
        password = getpass.getpass("Password: ")
        with (
            Bridge() as bridge,
            httpx.Client(base_url=args.base_url, follow_redirects=False, trust_env=False) as client,
        ):
            collector = Collector(
                bridge, client, origin, args.poll_interval, args.timeout, args.request_timeout
            )
            generate(
                bridge,
                collector,
                args.only,
                authenticate=lambda: collector.login(username, password),
            )
        print("PASS HTTP capture and seven-Bundle admission")
        return 0
    except (CollectionError, OSError, ValueError, EOFError):
        import sys

        error = sys.exception()
        print(
            "FAIL "
            + (str(error) if isinstance(error, CollectionError) else "collector operation_failed")
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
