"""Apply the content author's photo selection from review.html.

Reads `content/<cc>/media-candidates/selection.json` (downloaded from review.html) and
`candidates.json`, accepts 1-5 picks per attraction (fewer than 3 is a "partial" gallery that can be extended
later), refuses anything not in the verified shortlist,
downloads 1440px copies into `local-site/assets/places/`, and writes the selected-photo
manifest `content/<cc>/photos.json` with full attribution and per-image framing.

    python tools/media/apply_selection.py is [path/to/selection.json]
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "MyFirstVisit-shortlist/1.0 (FinitePlay LLC; content research)"
WIDTH = 1440
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def fetch(url: str, dest: Path) -> None:
    if dest.exists():
        return
    if "staticflickr.com" in url:
        # Flickr's CDN rate-limits Python's HTTP client but serves curl normally.
        tmp = dest.with_suffix(".part")
        subprocess.run(["curl", "-sSfL", "-m", "90", "-A", BROWSER_UA, "-o", str(tmp), url], check=True)
        tmp.replace(dest)
        return
    for attempt in range(6):
        try:
            time.sleep(1.0)
            ua = BROWSER_UA if "staticflickr.com" in url else UA  # Flickr's CDN 429s custom agents
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=90) as r:
                dest.write_bytes(r.read())
            return
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            time.sleep(20 * (attempt + 1))


def flickr_display_url(c: dict) -> str:
    """Ask Flickr for a ~1440px+ size; the original file is large and rate-limited."""
    import os
    key = os.environ.get("FLICKR_API_KEY")
    kf = Path.home() / ".finiteplay" / "flickr.key"
    if not key and kf.exists():
        key = kf.read_text(encoding="utf-8").strip()
    photo_id = c["sourceUrl"].rstrip("/").rsplit("/", 1)[-1]
    q = urllib.parse.urlencode({"method": "flickr.photos.getSizes", "api_key": key,
                                "photo_id": photo_id, "format": "json", "nojsoncallback": 1})
    req = urllib.request.Request("https://api.flickr.com/services/rest/?" + q, headers={"User-Agent": UA})
    sizes = json.load(urllib.request.urlopen(req, timeout=40))["sizes"]["size"]
    big = max(sizes, key=lambda x: int(x["width"]))
    return min((x for x in sizes if int(x["width"]) >= WIDTH), key=lambda x: int(x["width"]),
               default=big)["source"]


def display_url(c: dict) -> str:
    if c["source"] == "Wikimedia Commons":
        name = c["title"].removeprefix("File:")
        return ("https://commons.wikimedia.org/wiki/Special:FilePath/"
                + urllib.parse.quote(name) + f"?width={WIDTH}")
    return flickr_display_url(c)


def main() -> int:
    cc = sys.argv[1]
    pack = ROOT / "content" / cc
    cand_dir = pack / "media-candidates"
    sel_path = Path(sys.argv[2]) if len(sys.argv) > 2 else cand_dir / "selection.json"
    selection = json.loads(sel_path.read_text(encoding="utf-8"))
    candidates = json.loads((cand_dir / "candidates.json").read_text(encoding="utf-8"))["attractions"]
    assets = ROOT / "local-site" / "assets" / "places"
    assets.mkdir(parents=True, exist_ok=True)

    out = pack / "photos.json"
    # Merge into the existing manifest so galleries can be extended in later rounds.
    manifest = json.loads(out.read_text(encoding="utf-8"))["attractions"] if out.exists() else {}
    errors = []
    for sid, picks in selection["selections"].items():
        pool = {c["id"]: c for c in candidates.get(sid, {}).get("candidates", [])}
        if not 1 <= len(picks) <= 5:
            errors.append(f"{sid}: {len(picks)} picks (need 1-5); skipped")
            continue
        photos = []
        for pick in picks:
            c = pool.get(pick["id"])
            if not c:
                errors.append(f"{sid}: {pick['id']} is not in the verified shortlist")
                continue
            dest = assets / f"{pick['id']}.jpg"
            fetch(display_url(c), dest)
            photos.append({
                "id": pick["id"],
                "file": f"assets/places/{dest.name}",
                "source": c["source"],
                "sourceUrl": c["sourceUrl"],
                "title": c["title"],
                "author": c["author"],
                "license": c["license"],
                "licenseUrl": c["licenseUrl"],
                "width": c["width"], "height": c["height"],
                "objectPosition": pick.get("objectPosition", "center"),
                "downloadedAt": time.strftime("%Y-%m-%d"),
                "selectedBy": "content author",
                "selectedAt": selection.get("selectedAt"),
                "releaseStatus": "author-selected; alt text, people/property and final rights review pending",
            })
        if photos:
            manifest[sid] = photos
        status = "complete" if len(photos) >= 3 else "partial (add more later)"
        print(f"{sid}: {len(photos)} photos, {status}")

    out.write_text(json.dumps({"schemaVersion": 1, "attractions": manifest,
                               "partial": sorted(k for k, v in manifest.items() if len(v) < 3)},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {out}")
    for e in errors:
        print("WARN", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
