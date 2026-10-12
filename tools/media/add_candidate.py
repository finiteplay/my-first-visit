"""Add one Flickr photo to an attraction's shortlist by URL (and optionally select it).

Applies the same checks as the automatic shortlist: license must allow commercial use with
attribution (CC0, PDM, CC BY, CC BY-SA), no ND/NC, landscape, minimum width. Manual
candidates get ids like `<sight>-m01` and survive re-runs of shortlist_photos.py.

    python tools/media/add_candidate.py is sight-perlan https://www.flickr.com/photos/x/123/ [--select]
Needs FLICKR_API_KEY or ~/.finiteplay/flickr.key.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shortlist_photos as sp  # noqa: E402

LIC = {"4": ("CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/"),
       "5": ("CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/"),
       "9": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
       "10": ("Public Domain Mark", "https://creativecommons.org/publicdomain/mark/1.0/"),
       "11": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"),
       "12": ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/")}


def call(key: str, method: str, **kw) -> dict:
    return sp.get_json("https://api.flickr.com/services/rest/",
                       {"method": method, "api_key": key, "format": "json", "nojsoncallback": 1, **kw})


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cc, sid, url = args
    key = os.environ.get("FLICKR_API_KEY")
    kf = Path.home() / ".finiteplay" / "flickr.key"
    if not key and kf.exists():
        key = kf.read_text(encoding="utf-8").strip()
    if not key:
        sys.exit("No Flickr key (FLICKR_API_KEY or ~/.finiteplay/flickr.key)")
    pid = re.search(r"flickr\.com/photos/([^/]+)/(\d+)", url)
    owner_path, photo_id = pid.group(1), pid.group(2)
    info = call(key, "flickr.photos.getInfo", photo_id=photo_id)["photo"]
    lic = LIC.get(str(info["license"]))
    if not lic:
        sys.exit(f"Rejected: license id {info['license']} does not allow commercial use with attribution")
    sizes = call(key, "flickr.photos.getSizes", photo_id=photo_id)["sizes"]["size"]
    big = max(sizes, key=lambda s: int(s["width"]))
    mid = min((s for s in sizes if int(s["width"]) >= sp.THUMB_WIDTH), key=lambda s: int(s["width"]), default=big)
    w, h = int(big["width"]), int(big["height"])
    # Download a ~1600px copy, not the multi-megapixel original.
    disp = min((s for s in sizes if int(s["width"]) >= 1440), key=lambda s: int(s["width"]), default=big)
    c = {
        "source": "Flickr", "title": info["title"]["_content"] or photo_id,
        "sourceUrl": f"https://www.flickr.com/photos/{owner_path}/{photo_id}/",
        "fileUrl": disp["source"], "thumbUrl": mid["source"], "mime": "image/jpeg",
        "width": w, "height": h,
        "author": info["owner"]["realname"] if re.search(r"\w", info["owner"].get("realname", "")) else info["owner"]["username"],
        "license": lic[0], "licenseUrl": lic[1],
        "description": sp.strip_html(info["description"]["_content"])[:300],
        "restrictions": "", "note": "Added manually by URL. Confirm the uploader's own work.",
        "ratio": round(w / h, 2),
    }
    why = sp.reject_reason(c)
    if why:
        sys.exit(f"Rejected: {why}")

    pack = sp.ROOT / "content" / cc / "media-candidates"
    path = pack / "candidates.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    entry = doc["attractions"][sid]
    old = next((x for x in entry["candidates"] if x["sourceUrl"] == c["sourceUrl"]), None)
    if old:
        c["id"] = old["id"]
    else:
        n = sum(1 for x in entry["candidates"] if "-m" in x["id"]) + 1
        c["id"] = f"{sid}-m{n:02d}"
        entry["candidates"].append(c)
        entry["shortfall"] = None if len(entry["candidates"]) >= 10 else entry.get("shortfall")
    thumb = pack / "thumbs" / f"{c['id']}.jpg"
    if not sp.download(c["thumbUrl"], thumb):
        sys.exit("thumbnail download failed")
    (old or c)["thumb"] = f"thumbs/{thumb.name}"
    if old:
        old["fileUrl"] = c["fileUrl"]
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    sp.write_review(pack, doc)
    print(f"Added {c['id']}: {c['license']} · {c['author']} · {w}x{h}")

    if "--select" in sys.argv:
        sel_path = pack / "selection.json"
        sel = json.loads(sel_path.read_text(encoding="utf-8"))
        picks = sel["selections"].setdefault(sid, [])
        if len(picks) >= 5:
            sys.exit("Already 5 picks")
        if not any(p["id"] == c["id"] for p in picks):
            picks.append({"id": c["id"], "objectPosition": "center"})
        sel_path.write_text(json.dumps(sel, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Selected for {sid} ({len(picks)} picks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
