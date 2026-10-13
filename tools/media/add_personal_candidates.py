"""Add the author's own trip photos to the selection page as candidates, next to the Commons and Flickr ones.

    python tools/media/add_personal_candidates.py is C:/scratch/iceland-photos-by-place      # the folder made by sort_personal_photos.py

Reads <folder>/index.csv (run `sort_personal_photos.py refresh <folder>` first if photos were moved by hand), keeps only
photos with status "kept" that sit in a place folder matching a sight, and for each one that is landscape (ratio 1.33-2.2)
and at least MIN_WIDTH wide adds a candidate with id `<sight id>-p001`, `-p002`, ... to
`content/<cc>/media-candidates/candidates.json`, makes a thumbnail in `thumbs/` (git-ignored) and rewrites `review.html`.
Candidate ids stay the same when you run it again, so earlier picks in selection.json keep working. Candidates from
Commons and Flickr are untouched and keep their place at the top of each place's list; own photos follow them.

The photos stay on your machine: candidates.json holds only the place folder and file name (`personal`), never your
folder path. `apply_selection.py` finds the files through the folder recorded in ~/.finiteplay/personal-photos-root.txt
(written here) or the MFV_PERSONAL_PHOTOS variable. Credit and license are "FinitePlay" and "Own work".
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shortlist_photos import MAX_RATIO, MIN_RATIO, write_review  # noqa: E402
from sort_personal_photos import slug  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MIN_WIDTH = 1600
TOLERANCE = 0.015   # a phone's 4:3 frame is 4080x3072 = 1.328, a hair under the 1.33 rule
THUMB = 960
SOURCE = "Own photo (author)"


def main() -> int:
    from PIL import Image, ImageOps

    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("folder", help="the folder made by sort_personal_photos.py (has index.csv)")
    ap.add_argument("--author", default="FinitePlay", help="credit shown with the photo")
    args = ap.parse_args()
    folder = Path(args.folder)
    index = folder / "index.csv"
    if not index.exists():
        print(f"{index} not found; run sort_personal_photos.py sort and refresh first", file=sys.stderr)
        return 2

    pack = ROOT / "content" / args.country
    sights = json.loads((pack / "sights.yaml").read_text(encoding="utf-8"))["items"]
    by_slug = {slug(s["name"]): s for s in sights}
    out_dir = pack / "media-candidates"
    thumbs = out_dir / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    doc = json.loads((out_dir / "candidates.json").read_text(encoding="utf-8"))
    attractions = doc["attractions"]

    rows = [r for r in csv.DictReader(index.open(encoding="utf-8", newline="")) if r["status"] == "kept"]
    unmatched: dict[str, int] = {}
    per_place: dict[str, list[dict]] = {}
    for r in rows:
        place = by_slug.get(r["folder"])
        if not place:
            unmatched[r["folder"]] = unmatched.get(r["folder"], 0) + 1
            continue
        per_place.setdefault(place["id"], []).append(r)

    # earlier personal candidates keep their ids (matched by file name)
    old_ids = {}
    for sid, a in attractions.items():
        for c in a["candidates"]:
            if c.get("personal"):
                old_ids[(sid, c["personal"]["file"])] = c["id"]

    added, rejected = {}, {}
    for sid, a in attractions.items():
        a["candidates"] = [c for c in a["candidates"] if not c.get("personal")]   # rebuilt below
    for sid, items in per_place.items():
        taken_sorted = sorted(items, key=lambda r: (r["taken"], r["file"]))
        used = {int(i.rsplit("-p", 1)[1]) for (s, _), i in old_ids.items() if s == sid}
        counter = max(used, default=0)
        reject = rejected.setdefault(sid, {})
        for r in taken_sorted:
            name = Path(r["file"]).name
            path = folder / r["file"]
            try:
                with Image.open(path) as im:
                    im = ImageOps.exif_transpose(im).convert("RGB")
                    w, h = im.size
                    ratio = w / h
                    if ratio < MIN_RATIO - TOLERANCE or ratio > MAX_RATIO:
                        why = "portrait or square" if ratio < MIN_RATIO - TOLERANCE else "too wide"
                        reject[why] = reject.get(why, 0) + 1
                        continue
                    if w < MIN_WIDTH:
                        reject["too small"] = reject.get("too small", 0) + 1
                        continue
                    cid = old_ids.get((sid, name))
                    if not cid:
                        counter += 1
                        cid = f"{sid}-p{counter:03d}"
                    thumb = im.copy()
                    thumb.thumbnail((THUMB, THUMB))
                    thumb.save(thumbs / f"{cid}.jpg", quality=82)
            except Exception as e:
                reject["unreadable"] = reject.get("unreadable", 0) + 1
                print(f"  {path}: {e}", file=sys.stderr)
                continue
            attractions[sid]["candidates"].append({
                "source": SOURCE, "title": name, "sourceUrl": "", "fileUrl": "", "thumbUrl": "",
                "mime": "image/jpeg", "width": w, "height": h, "ratio": round(ratio, 2),
                "author": args.author, "license": "Own work", "licenseUrl": "",
                "description": f"Own trip photo, {r['taken'][:10].replace(':', '-')}" if r["taken"] else "Own trip photo",
                "restrictions": "", "id": cid, "thumb": f"thumbs/{cid}.jpg",
                "personal": {"folder": r["folder"], "file": name},
            })
            added[sid] = added.get(sid, 0) + 1
        attractions[sid]["rejectedCounts"] = {**{k: v for k, v in attractions[sid].get("rejectedCounts", {}).items()
                                                 if not k.startswith("own photos")},
                                              **{f"own photos: {k}": v for k, v in reject.items()}}
        attractions[sid]["shortfall"] = None if len(attractions[sid]["candidates"]) >= 10 else attractions[sid].get("shortfall")

    doc["generatedAt"] = time.strftime("%Y-%m-%d")
    if SOURCE not in doc["sources"]:
        doc["sources"].append(SOURCE)
    (out_dir / "candidates.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    write_review(out_dir, doc)
    (Path.home() / ".finiteplay" / "personal-photos-root.txt").write_text(str(folder.resolve()), encoding="utf-8")

    total = sum(added.values())
    print(f"added {total} own photos as candidates for {len(added)} places  ->  {out_dir / 'review.html'}")
    for sid, n in sorted(added.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {n:4d}  {sid}")
    skipped = {sid: sum(v.values()) for sid, v in rejected.items() if v}
    print(f"left out: {sum(skipped.values())} (portrait or square shots, too wide, or too small), e.g. "
          + ", ".join(f"{k} {v}" for k, v in list(sorted(skipped.items(), key=lambda kv: -kv[1]))[:4]))
    if unmatched:
        print("folders that match no sight (not added):", ", ".join(f"{k} ({v})" for k, v in sorted(unmatched.items(), key=lambda kv: -kv[1])[:10]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
