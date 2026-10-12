"""Write each place's own rating (aggregate stars) and place in our ranking into content/<cc>/sights.yaml.

Why: the site must not republish any other site's rating, review count, rank or link (their terms forbid it). It shows
two things we own: "aggregate stars" (our rating, edited by us, informed by what travelers say on several large sites)
and our own place in the ranking, a plain 1..N order for this website only. Both are decided in the HTML editor
(tools/content/edit_ratings.py) and kept in ~/.finiteplay/score-inputs/<cc>.json (override: MFV_SCORE_INPUTS), which
also holds the raw per-site numbers used for suggestions and is NEVER committed. Only the result goes into sights.yaml:

    "score": {"stars": 4.6, "rank": 3, "method": "aggregate-v2", "asOf": "2026-10"}

    python tools/content/build_score.py is         # inputs file -> sights.yaml `score` for every place that has stars

Inputs file (schemaVersion 2):
    {"schemaVersion": 2, "asOf": "2026-10", "order": ["sight-a", "sight-b", ...],
     "places": {"sight-a": {"stars": 4.6, "placeholder": true, "note": "...",
                            "sources": {"tripadvisor": {"rating": 4.6, "reviews": 1187, "rank": 5, "of": "..."},
                                        "google": {"rating": 4.7, "reviews": 9021}}}}}
`placeholder: true` means the stars are still a copy of a source number that has not been reviewed; editing clears it.

Suggestion (shown in the editor, never applied silently): each source's rating is shrunk toward that source's mean by how
few reviews it has, (n*rating + 50*mean)/(n + 50), and the sources are blended weighted by log10(1 + n).
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
METHOD = "aggregate-v2"


def inputs_path(cc: str) -> Path:
    return Path(os.environ.get("MFV_SCORE_INPUTS", str(Path.home() / ".finiteplay" / "score-inputs" / f"{cc}.json")))


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_sights(path: Path, data: dict) -> None:
    # sights.yaml is JSON with CRLF line endings in the working tree; keep that style so diffs stay small.
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2).replace("\n", "\r\n"), encoding="utf-8", newline="")


def suggest(places: dict[str, dict]) -> dict[str, float]:
    """Blend each place's per-source ratings into one suggested star value (see module docstring)."""
    sources = sorted({s for p in places.values() for s in p.get("sources", {})})
    mean = {}
    for s in sources:
        ratings = [p["sources"][s]["rating"] for p in places.values() if p.get("sources", {}).get(s, {}).get("rating") is not None]
        mean[s] = sum(ratings) / len(ratings)
    out = {}
    for pid, p in places.items():
        total = weight = 0.0
        for s in sources:
            entry = p.get("sources", {}).get(s) or {}
            r, n = entry.get("rating"), entry.get("reviews")
            if r is None or not n:
                continue
            total += math.log10(1 + n) * (n * r + SHRINK * mean[s]) / (n + SHRINK)
            weight += math.log10(1 + n)
        if weight:
            out[pid] = round(total / weight, 2)
    return out


def load_inputs(path: Path, item_ids: list[str]) -> dict:
    """Read the inputs file, upgrading the old per-source layout (schemaVersion 1) and filling in a starting order."""
    raw = read(path) if path.exists() else {"places": {}}
    places = raw.get("places", {})
    if raw.get("schemaVersion") != 2:
        upgraded = {}
        for pid, p in places.items():
            sources = {s: v for s, v in p.items() if isinstance(v, dict)}
            entry = {"sources": sources}
            ta = sources.get("tripadvisor", {})
            if ta.get("rating") is not None:  # TripAdvisor values are the placeholders until the author edits them
                entry["stars"], entry["placeholder"] = ta["rating"], True
            if ta.get("note"):
                entry["note"] = ta["note"]
            upgraded[pid] = entry
        places = upgraded
    for pid in item_ids:
        places.setdefault(pid, {"sources": {}})
    guess = suggest(places)
    order = [pid for pid in raw.get("order", []) if pid in places]
    rest = [pid for pid in item_ids if pid not in order]
    rest.sort(key=lambda pid: (-(guess.get(pid) or places[pid].get("stars") or 0), item_ids.index(pid)))
    return {"schemaVersion": 2, "asOf": raw.get("asOf") or "2026-10", "order": order + rest, "places": places}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    args = ap.parse_args()
    sights_path = ROOT / "content" / args.country / "sights.yaml"
    sights = read(sights_path)
    ids = [item["id"] for item in sights["items"]]
    path = inputs_path(args.country)
    inputs = load_inputs(path, ids)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(inputs, indent=1, ensure_ascii=False), encoding="utf-8")

    rank = {pid: i + 1 for i, pid in enumerate(inputs["order"])}
    scored, missing = 0, []
    for item in sights["items"]:
        stars = inputs["places"][item["id"]].get("stars")
        if stars is None:
            item.pop("score", None)
            missing.append(item["id"])
            continue
        item["score"] = {"stars": round(float(stars), 1), "rank": rank[item["id"]], "method": METHOD, "asOf": inputs["asOf"]}
        scored += 1
    write_sights(sights_path, sights)
    placeholders = sum(1 for p in inputs["places"].values() if p.get("placeholder"))
    print(f"scored {scored} of {len(ids)} places; {placeholders} still use a placeholder (source number not yet reviewed)"
          + (f"; no stars: {', '.join(missing[:6])}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
