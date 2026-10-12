"""Propose parking coordinates for places whose map pin is not a place you can drive to.

    python tools/content/find_parking.py is                  # write a report, change nothing
    python tools/content/find_parking.py is --apply          # write `parking` into sights.yaml for the chosen places

Why: a pin on a waterfall, a lava field or a river is where the sight is, not where a car can stop. The place page's Google
Maps link should open the parking lot instead. Candidates come from OpenStreetMap via Nominatim (ODbL; credit
"© OpenStreetMap contributors"), one request per second, so the coordinates may be stored. Nothing comes from Google Places,
whose terms do not allow keeping its coordinates.

For each place the tool searches "parking" in a box around the pin, drops lots tagged private or no-access, and prefers one
whose name contains a word of the place's name; otherwise the nearest. Only places in a walk-in category (WALK_IN: Nature)
are considered. A place gets `parking` when the best lot is at least MIN_M metres from the pin and no more than MAX_M away;
closer means the pin already is at the lot. Edit
`content/<cc>/parking-overrides.json` ({"<place id>": {"latitude":..., "longitude":..., "label":...} or null to skip}) to
correct a result; overrides always win and are reapplied.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_score import ROOT, read, write_sights  # noqa: E402

MIN_M, MAX_M = 80, 2500
WALK_IN = {"Nature"}   # categories whose pin is usually the sight itself, not somewhere a car can stop
BOX_LAT, BOX_LON = 0.024, 0.06   # degrees either side of the pin (about 2.7 km north-south, 3.2 km east-west at 64 N)
UA = "MyFirstVisit-research/1.0 (https://finiteplay.org)"


def metres(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c)).replace("ð", "d").replace("þ", "th").replace("æ", "ae")


def tokens(item: dict) -> set[str]:
    words = fold(item["local"] + " " + item["name"]).replace("-", " ").split()
    return {w for w in words if len(w) >= 5 and w not in {"waterfall", "national", "museum", "iceland", "icelandic", "hot", "springs", "coast", "area", "park", "lagoon", "river", "crater", "beach", "and"}}


def search(lat: float, lon: float) -> list[dict]:
    params = {"q": "parking", "format": "jsonv2", "bounded": 1, "limit": 30, "extratags": 1,
              "viewbox": f"{lon - BOX_LON},{lat + BOX_LAT},{lon + BOX_LON},{lat - BOX_LAT}"}
    req = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def best(item: dict, results: list[dict]) -> dict | None:
    here = (item["location"]["latitude"], item["location"]["longitude"])
    want = tokens(item)
    cands = []
    for e in results:
        if e.get("category") != "amenity" or e.get("type") != "parking":
            continue
        tags = e.get("extratags") or {}
        if tags.get("access") in ("private", "no", "permit", "customers", "delivery"):
            continue
        pos = (float(e["lat"]), float(e["lon"]))
        d = metres(here, pos)
        named = bool(want & set(fold(e.get("name") or "").split()))
        cands.append({"latitude": round(pos[0], 6), "longitude": round(pos[1], 6), "name": e.get("name") or "", "distance": round(d),
                      "fee": tags.get("fee"), "named": named, "osm": f"{e.get('osm_type')}/{e.get('osm_id')}"})
    if not cands:
        return None
    named = [c for c in cands if c["named"] and c["distance"] <= MAX_M]
    return min(named or cands, key=lambda c: c["distance"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    pack = ROOT / "content" / args.country
    sights = read(pack / "sights.yaml")
    overrides_path = pack / "parking-overrides.json"
    overrides = read(overrides_path) if overrides_path.exists() else {}
    cache_path = Path.home() / ".finiteplay" / "parking-cache" / f"{args.country}.json"
    cache = read(cache_path) if cache_path.exists() else {}
    report, applied = [], 0
    for item in sights["items"]:
        pid = item["id"]
        pick = None
        if pid in overrides:
            o = overrides[pid]
            pick = None if o is None else {**o, "distance": round(metres((item["location"]["latitude"], item["location"]["longitude"]),
                                                                       (o["latitude"], o["longitude"]))), "name": o.get("label", ""), "osm": "override"}
        else:
            if pid not in cache:
                cache[pid] = search(item["location"]["latitude"], item["location"]["longitude"])
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
                time.sleep(1.1)   # Nominatim usage policy: at most one request per second
            pick = best(item, cache[pid])
        eligible = item.get("category") in WALK_IN or pid in overrides
        use = bool(pick) and eligible and (pid in overrides or MIN_M <= pick["distance"] <= MAX_M)
        report.append((pid, item["name"], pick, use))
        item.pop("parking", None)
        if use and args.apply:
            item["parking"] = {"latitude": pick["latitude"], "longitude": pick["longitude"],
                               "label": pick.get("name") or f"Parking for {item['name']}",
                               "source": "OpenStreetMap contributors (ODbL)" if pick["osm"] != "override" else "author",
                               "distanceMeters": pick["distance"]}
            applied += 1
    for pid, name, pick, use in report:
        if pick is None:
            print(f"{'-':>5} {name[:34]:34} no parking found nearby")
        else:
            print(f"{'USE' if use else 'skip':>5} {name[:34]:34} {pick['distance']:>5} m  {pick['name'][:30]:30} {'named' if pick.get('named') else ''} {('fee=' + pick['fee']) if pick.get('fee') else ''}")
    if args.apply:
        write_sights(pack / "sights.yaml", sights)
        print(f"applied parking to {applied} places")
    else:
        print("dry run: nothing written (use --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
