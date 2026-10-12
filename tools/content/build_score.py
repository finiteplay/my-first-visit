"""Compute each place's own "traveler score" from public rating aggregates.

Why: the site must not republish any other site's rating, review count, rank or link (their terms forbid it). It
publishes one number that we compute: a confidence-weighted blend of the ratings travelers gave a place on several large
sites. The raw per-site inputs stay OUTSIDE the repository, in ~/.finiteplay/score-inputs/<cc>.json (override with
MFV_SCORE_INPUTS); only the blended result is written to content/<cc>/sights.yaml as `score`.

    python tools/content/build_score.py is                      # recompute scores from the inputs file
    python tools/content/build_score.py is --import-tripadvisor # one-off: move old `tripadvisor` fields out of sights.yaml

Inputs file: {"asOf": "2026-10", "places": {"<place id>": {"tripadvisor": {"rating": 4.6, "reviews": 1187},
                                                              "google":      {"rating": 4.7, "reviews": 9021}}}}

Method (v1), per place:
  1. Shrink each source's rating toward that source's mean over all places, by how few reviews it has:
         adjusted = (n * rating + M * source_mean) / (n + M)        with M = 50
  2. Blend the sources, weighting each by log10(1 + n), so a source with many reviews counts for more.
  3. Publish blended * 2, rounded to one decimal, as a score out of 10 (stored with two decimals for sorting).
`score.sources` is how many sources fed it. A place with no usable input gets no score and sorts after scored places.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHRINK = 50
METHOD = "v1"


def inputs_path(cc: str) -> Path:
    return Path(os.environ.get("MFV_SCORE_INPUTS", str(Path.home() / ".finiteplay" / "score-inputs" / f"{cc}.json")))


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_sights(path: Path, data: dict) -> None:
    # sights.yaml is JSON with CRLF line endings in the working tree; keep that style so diffs stay small.
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\r\n"), encoding="utf-8", newline="")


def blend(places: dict[str, dict]) -> dict[str, dict]:
    sources = sorted({s for p in places.values() for s in p})
    mean = {}
    for s in sources:
        ratings = [p[s]["rating"] for p in places.values() if p.get(s, {}).get("rating") is not None]
        mean[s] = sum(ratings) / len(ratings)
    out = {}
    for pid, p in places.items():
        total = weight = 0.0
        used = 0
        for s in sources:
            entry = p.get(s) or {}
            r, n = entry.get("rating"), entry.get("reviews")
            if r is None or not n:
                continue
            adjusted = (n * r + SHRINK * mean[s]) / (n + SHRINK)
            w = math.log10(1 + n)
            total += w * adjusted
            weight += w
            used += 1
        if used:
            out[pid] = {"value": round(total / weight * 2, 2), "sources": used}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("--import-tripadvisor", action="store_true",
                    help="move legacy `tripadvisor` fields out of sights.yaml into the inputs file (one-off)")
    args = ap.parse_args()
    sights_path = ROOT / "content" / args.country / "sights.yaml"
    sights = read(sights_path)
    path = inputs_path(args.country)
    inputs = read(path) if path.exists() else {"asOf": "", "places": {}}

    if args.import_tripadvisor:
        moved = 0
        for item in sights["items"]:
            ta = item.pop("tripadvisor", None)
            if ta and ta.get("rating") is not None and ta.get("reviews"):
                inputs["places"].setdefault(item["id"], {})["tripadvisor"] = {"rating": ta["rating"], "reviews": ta["reviews"]}
                moved += 1
        inputs["asOf"] = inputs.get("asOf") or "2026-10"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(inputs, indent=1), encoding="utf-8")
        print(f"moved {moved} Tripadvisor inputs to {path} and removed the field from sights.yaml")

    scores = blend({pid: p for pid, p in inputs["places"].items() if p})
    asof = inputs.get("asOf", "")
    missing = []
    for item in sights["items"]:
        score = scores.get(item["id"])
        if score:
            item["score"] = {"value": score["value"], "sources": score["sources"], "method": METHOD, "asOf": asof}
        else:
            item.pop("score", None)
            missing.append(item["id"])
    write_sights(sights_path, sights)
    vals = sorted(s["value"] for s in scores.values())
    print(f"scored {len(scores)} of {len(sights['items'])} places"
          + (f"; range {vals[0]}-{vals[-1]}, median {vals[len(vals) // 2]}" if vals else "")
          + (f"; unscored: {', '.join(missing[:6])}{'...' if len(missing) > 6 else ''}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
