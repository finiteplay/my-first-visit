"""Fetch Google Maps rating aggregates for the place list, as inputs for tools/content/build_score.py.

    GOOGLE_PLACES_API_KEY=... python tools/content/fetch_google_ratings.py is [--only sight-perlan] [--dry-run]

Uses the official Places API (New) Text Search with the place's coordinates as a location bias, so it needs a key from a
Google Cloud project with billing and the "Places API (New)" enabled (about 60 requests per country; one-off).
Results go to the inputs file OUTSIDE the repository (~/.finiteplay/score-inputs/<cc>.json, or MFV_SCORE_INPUTS) next to
the other sources; nothing from Google is written into the repo. Each result is checked against our coordinates and a
mismatch (more than 3 km, or a different-looking name) is listed for review instead of being used.
Then reopen the editor (edit_ratings.py) to see the new suggestions, and run build_score.py after editing.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_score import ROOT, inputs_path, load_inputs, read  # noqa: E402

ENDPOINT = "https://places.googleapis.com/v1/places:searchText"
FIELDS = "places.id,places.displayName,places.rating,places.userRatingCount,places.location"
MAX_KM = 3.0


def km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def search(key: str, item: dict) -> dict | None:
    loc = item["location"]
    body = {"textQuery": f"{item['local']} {item.get('nearestCity', '')} Iceland".strip(), "maxResultCount": 3,
            "locationBias": {"circle": {"center": {"latitude": loc["latitude"], "longitude": loc["longitude"]}, "radius": 2000.0}}}
    req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELDS})
    with urllib.request.urlopen(req, timeout=30) as r:
        places = json.load(r).get("places", [])
    here = (loc["latitude"], loc["longitude"])
    near = [p for p in places if "location" in p and km(here, (p["location"]["latitude"], p["location"]["longitude"])) <= MAX_KM]
    rated = [p for p in near if p.get("rating") is not None and p.get("userRatingCount")]
    return max(rated, key=lambda p: p["userRatingCount"]) if rated else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not key and not args.dry_run:
        print("Set GOOGLE_PLACES_API_KEY (Places API (New) enabled).", file=sys.stderr)
        return 2
    all_items = read(ROOT / "content" / args.country / "sights.yaml")["items"]
    items = [i for i in all_items if i.get("location") and (not args.only or i["id"] in args.only)]
    path = inputs_path(args.country)
    inputs = load_inputs(path, [i["id"] for i in all_items])
    review, found = [], 0
    for item in items:
        if args.dry_run:
            print(f"would search: {item['local']} {item.get('nearestCity', '')}")
            continue
        try:
            hit = search(key, item)
        except Exception as e:  # network or quota problems: report and continue
            review.append((item["id"], f"error {e}"))
            continue
        if not hit:
            review.append((item["id"], "no rated place within 3 km"))
            continue
        inputs["places"].setdefault(item["id"], {"sources": {}}).setdefault("sources", {})["google"] = {
            "rating": hit["rating"], "reviews": hit["userRatingCount"],
            "name": hit.get("displayName", {}).get("text", ""), "placeId": hit["id"]}
        found += 1
    if not args.dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(inputs, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{found} of {len(items)} places got a Google rating -> {path}")
        for pid, why in review:
            print("  review:", pid, why)
        print("Check the matched names in the inputs file, then run tools/content/build_score.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
