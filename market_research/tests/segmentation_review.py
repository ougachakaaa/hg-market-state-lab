"""Generate an offline review of the retained G4 Price Segmentation evidence."""

import argparse
import csv
import hashlib
import html
import json
import math
import statistics
from datetime import date
from pathlib import Path

from market_research.algorithm.pip import find_pips


def review(evidence: Path, epsilons: list[float]) -> tuple[dict, list[dict]]:
    """Validate retained input identity and recompute each requested segmentation."""
    report = json.loads(evidence.read_text(encoding="utf-8"))
    scenarios = [
        s
        for s in report["scenarios"]
        if s["request"]["index_code"] == "000852.SH"
        and s["request"]["start_date"] == "2024-01-08"
        and s["request"]["end_date"] == "2024-02-29"
        and s["request"]["epsilon"] == 0.01
    ]
    if len(scenarios) != 1:
        raise ValueError("Expected exactly one G4 long-window scenario")
    source = scenarios[0]
    calendar, index = (a["final_export"] for a in source["input_evidence"])
    rows = index["records"]
    dates = [r["trade_date"] for r in rows]
    closes = [float(r["close"]) for r in rows]
    sessions = [r["cal_date"] for r in calendar["records"] if r["is_open"] == 1]
    if (
        len(dates) < 2
        or dates != sessions
        or any(a >= b for a, b in zip(dates, dates[1:], strict=False))
        or any(date.fromisoformat(d).isoformat() != d for d in dates)
        or any(r["index_code"] != source["request"]["index_code"] for r in rows)
        or any(not math.isfinite(c) or c <= 0 for c in closes)
    ):
        raise ValueError("Invalid ordered source facts")
    payload = [
        "price_segmentation_inputs_v1",
        "tushare_index_daily",
        "index_daily",
        1,
        source["request"]["index_code"],
        [[d, c.hex()] for d, c in zip(dates, closes, strict=False)],
    ]
    fingerprint = hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if fingerprint != source["input_fingerprint"]:
        raise ValueError("Input fingerprint mismatch")
    logs = [math.log(c) for c in closes]
    results = []
    # Always independently replay G4 even when its epsilon is not requested for display.
    for epsilon in dict.fromkeys([*epsilons, 0.01]):
        pip = find_pips(logs, epsilon=epsilon)
        indices = pip.indices
        if (
            indices[0] != 0
            or indices[-1] != len(dates) - 1
            or any(a >= b for a, b in zip(indices, indices[1:], strict=False))
        ):
            raise ValueError("Invalid PIP indices")
        spans = list(zip(indices, indices[1:], strict=False))
        maximum = max(
            (
                abs(logs[i] - (logs[a] + (logs[b] - logs[a]) * float(i - a) / float(b - a)))
                for a, b in spans
                for i in range(a + 1, b)
            ),
            default=0.0,
        )
        if maximum != pip.max_reconstruction_error or maximum > epsilon:
            raise ValueError("Invalid reconstruction error")
        durations = [b - a for a, b in spans]
        amplitudes = [closes[b] / closes[a] - 1 for a, b in spans]
        directions = [
            "up" if closes[b] > closes[a] else "down" if closes[b] < closes[a] else "flat"
            for a, b in spans
        ]
        if sum(durations) != len(dates) - 1 or any(
            a[1] != b[0] for a, b in zip(spans, spans[1:], strict=False)
        ):
            raise ValueError("Segments do not cover input")
        diag = {
            "input_point_count": len(dates),
            "important_point_count": len(indices),
            "segment_count": len(spans),
            "algorithm_id": pip.algorithm_id,
            "epsilon": epsilon,
            "max_reconstruction_error": maximum,
        }
        if epsilon == 0.01:
            points = [{"index": i, "date": dates[i], "close": closes[i]} for i in indices]
            if points != source["important_points"] or diag != source["diagnostics"]:
                raise ValueError("G4 replay mismatch")
        if epsilon in epsilons:
            results.append(
                {
                    **diag,
                    "input_fingerprint": fingerprint,
                    "indices": indices,
                    "average_duration": statistics.mean(durations),
                    "median_duration": statistics.median(durations),
                    "minimum_duration": min(durations),
                    "maximum_duration": max(durations),
                    "single_session_ratio": durations.count(1) / len(durations),
                    "average_absolute_amplitude": statistics.mean(map(abs, amplitudes)),
                    "median_absolute_amplitude": statistics.median(map(abs, amplitudes)),
                    "up_count": directions.count("up"),
                    "down_count": directions.count("down"),
                    "flat_count": directions.count("flat"),
                }
            )
    return {
        "dates": dates,
        "closes": closes,
        "fingerprint": fingerprint,
        "request": source["request"],
        "executed_at": report["executed_at_utc"],
        "tested_sha": report["tested_sha"],
    }, results


def chart(facts: dict, result: dict) -> str:
    dates, closes = facts["dates"], facts["closes"]
    low, high = min(closes), max(closes)
    pad = (high - low) * 0.05 or high * 0.05
    low, high = low - pad, high + pad

    def xy(i: int) -> tuple[float, float]:
        return 85 + 850 * i / (len(dates) - 1), 310 - 255 * (closes[i] - low) / (high - low)

    def path(indices: range | tuple) -> str:
        return " ".join(f"{xy(i)[0]:.2f},{xy(i)[1]:.2f}" for i in indices)

    ticks = []
    for i in sorted(
        {0, (len(dates) - 1) // 4, (len(dates) - 1) // 2, 3 * (len(dates) - 1) // 4, len(dates) - 1}
    ):
        x, _ = xy(i)
        ticks.append(f'<text x="{x:.2f}" y="338" text-anchor="middle">{i} {dates[i]}</text>')
    for j in range(5):
        y = 310 - 255 * j / 4
        ticks.append(
            f'<text x="77" y="{y:.2f}" text-anchor="end">{low + (high - low) * j / 4:.2f}</text>'
        )
        ticks.append(f'<line x1="85" x2="935" y1="{y:.2f}" y2="{y:.2f}" stroke="#dbe3eb"/>')
    dots = "".join(
        f'<circle cx="{xy(i)[0]:.2f}" cy="{xy(i)[1]:.2f}" r="1.5" fill="#d35400">'
        f"<title>{dates[i]}: {closes[i]}</title></circle>"
        for i in result["indices"]
    )
    return (
        '<svg viewBox="0 0 1000 370" role="img" aria-label="Close and PIP points">'
        + "".join(ticks)
        + f'<polyline points="{path(range(len(dates)))}" fill="none" '
        + 'stroke="#184a7a" stroke-width="0.7"/>'
        + f'<polyline points="{path(result["indices"])}" fill="none" '
        + 'stroke="#d35400" stroke-width="1.2" stroke-dasharray="6 4"/>'
        + dots
        + '<text x="500" y="365" text-anchor="middle">Trading session index and date</text>'
        + '<text x="14" y="180" transform="rotate(-90 14 180)" text-anchor="middle">'
        + "Close</text></svg>"
    )


def generate(evidence: Path, output: Path, epsilons: list[float]) -> None:
    if not epsilons or len(set(epsilons)) != len(epsilons):
        raise ValueError("Provide distinct positive epsilons")
    facts, results = review(evidence, epsilons)
    output.mkdir(parents=True, exist_ok=True)
    columns = [k for k in results[0] if k != "indices"]
    with (output / "comparison.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    table = (
        "<table><thead><tr>"
        + "".join(f"<th>{html.escape(k)}</th>" for k in columns if k != "input_fingerprint")
        + "</tr></thead><tbody>"
    )
    for r in results:
        table += (
            "<tr>"
            + "".join(
                f"<td>{html.escape(str(r[k]))}</td>" for k in columns if k != "input_fingerprint"
            )
            + "</tr>"
        )
    table += "</tbody></table>"
    panels = "".join(
        f"<section><h2>epsilon = {r['epsilon']} · {r['segment_count']} segments · "
        f"max log error {r['max_reconstruction_error']:.8f}</h2>{chart(facts, r)}</section>"
        for r in results
    )
    explanation = (
        "Blue: original Close; orange dots: original important points; "
        "dashed orange: connections in Close space for visual comparison only. "
        "PIP reconstructs linearly in ln(close), so these straight Close-space "
        "lines are not its fitted function. "
        "Maximum error is measured in natural log price. Epsilon is not a minimum segment return. "
        "Duration is in trading-session intervals; amplitude is the simple Close return. "
        "All segments are retained. These diagnostics are for human review, "
        "not Statistics product output or a new Live E2E pass."
    )
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Price segmentation offline review</title><style>
body{{font:15px system-ui;color:#173047;max-width:1200px;margin:auto;padding:24px}}
section{{margin:32px 0}}
svg{{width:100%;background:#f8fafc}}
svg text{{font:12px sans-serif;fill:#173047}}
table{{border-collapse:collapse;font-size:12px}}
td,th{{border:1px solid #ccd8e2;padding:5px}}
.scroll{{overflow:auto}}</style></head>
<body><h1>Price Segmentation V1 · offline review</h1>
<p>000852.SH · {facts["dates"][0]} to {facts["dates"][-1]} · {len(facts["dates"])} sessions ·
{facts["closes"][0]} to {facts["closes"][-1]} Close</p>
<p>Input SHA-256: {facts["fingerprint"]}</p>
<p>{explanation}</p>
<div class="scroll">{table}</div>{panels}</body></html>"""
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "README.md").write_text(
        f"""# Offline segmentation review

Source: saved G4 public input evidence, {evidence.resolve()}.
Original live run: {facts["executed_at"]}, tested SHA {facts["tested_sha"]}.
Subject 000852.SH; {facts["dates"][0]} to {facts["dates"][-1]};
fingerprint {facts["fingerprint"]}.
Algorithm: pip_vertical_error_bounded_v1. Epsilons: {epsilons}.

Open index.html locally in a browser. Compare the panels and CSV, paying attention to
short segments and changes in duration and amplitude. {explanation}\n""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epsilon", type=float, nargs="+", required=True)
    args = parser.parse_args()
    generate(args.evidence, args.output, args.epsilon)


if __name__ == "__main__":
    main()
