"""Sort personal trip photos by the place they were taken, and set aside portraits of specific people.

Folders in <dest>: one per place (within MAX_KM of the place's pin or parking lot); `_other_iceland/near-<place>` for
GPS inside Iceland that is not near any place (stops en route, sights without a card), grouped by the nearest place;
`_outside_iceland` for GPS elsewhere (airports, a wrong fix); `_no_gps/<source folder>` for photos without a location.

Both steps work on COPIES in a scratch folder; the originals are never touched.

    # 1. Read each photo's GPS and copy it to <dest>/<place>/ (nearest place in the pack, within MAX_KM)
    python tools/media/sort_personal_photos.py sort "C:/path/to/trip photos" C:/scratch/iceland-by-place --pack is

    # 2. Find portraits with local face models (OpenCV YuNet + SFace, ONNX, offline) and move them to <dest>/!deleted/
    python tools/media/sort_personal_photos.py portraits C:/scratch/iceland-by-place           # measure only, shows counts
    python tools/media/sort_personal_photos.py portraits C:/scratch/iceland-by-place --apply   # move the flagged photos
    python tools/media/sort_personal_photos.py restore   C:/scratch/iceland-by-place           # undo: put them all back

What counts as a portrait of specific people (either rule sets the photo aside):
  1. CLOSE-UP: the largest face is at least --threshold (default 0.10) of the photo's shorter side: a selfie or posed shot,
     whoever it is.
  2. KNOWN PEOPLE: a face that belongs to someone who appears in at least --min-photos (default 4) photos of the trip (your
     travel companions, found by face recognition) and is at least --known-size (default 0.04) of the shorter side, so
     "my friend posing in front of the waterfall" goes even when the face is small.
Strangers who appear once (bystanders at a pool, people on a street, a distant group) stay. Nothing is sent anywhere: both
models run locally. `features.json` keeps every measurement, so changing a setting re-sorts without re-detecting.
`people.jpg` shows one face per recurring person so you can check the grouping; `!deleted/review.html` shows what was set
aside, with the reason.

Needs: pillow, opencv-python-headless, and two model files in ~/.finiteplay/models/ from
https://github.com/opencv/opencv_zoo/tree/main/models : face_detection_yunet_2023mar.onnx (face_detection_yunet)
and face_recognition_sface_2021dec.onnx (face_recognition_sface). Videos are skipped.
OneDrive "files on demand" photos are downloaded when read; expect the first run to take a while.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".dng", ".webp"}
MAX_KM = 2.5
ICELAND = (63.1, 66.7, -24.7, -13.2)   # south, north, west, east: GPS outside this box is not Iceland
MODELS = Path.home() / ".finiteplay" / "models"
MODEL = MODELS / "face_detection_yunet_2023mar.onnx"
REC_MODEL = MODELS / "face_recognition_sface_2021dec.onnx"
DEFAULT_THRESHOLD = 0.10
DEFAULT_KNOWN_SIZE = 0.025
DEFAULT_MIN_PHOTOS = 6
MIN_FACE_SCORE = 0.85
DETECT_SIDE = 1280           # longest side the detector sees; small faces matter less than prominent ones
FEATURE_VERSION = 3          # bump when measure() changes, so cached measurements are redone
MIN_PIXELS = 24              # faces smaller than this (in the detector image) are too small to recognise
SAME_PERSON = 0.40           # cosine similarity to join a person (SFace suggests 0.363; stricter avoids merging strangers)


def slug(text: str) -> str:
    text = text.lower().replace("þ", "th").replace("ð", "d").replace("æ", "ae").replace("ö", "o")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def load_places(cc: str) -> list[dict]:
    """Every place with coordinates: the sights (pin and parking lot) and the lagoons listed inside the guides."""
    pack = ROOT / "content" / cc
    places = []
    for item in json.loads((pack / "sights.yaml").read_text(encoding="utf-8"))["items"]:
        anchors = [item["location"]] + ([item["parking"]] if item.get("parking") else [])
        places.append({"slug": slug(item["name"]), "name": item["name"], "points": [(a["latitude"], a["longitude"]) for a in anchors]})
    guides = json.loads((pack / "playbooks.yaml").read_text(encoding="utf-8")).get("playbooks", [])
    have = {p["slug"] for p in places}
    for guide in guides:
        for group in guide.get("whereToSoak", []) or []:
            for entry in group.get("places", []):
                loc = entry.get("location")
                if loc and slug(entry["name"]) not in have:
                    places.append({"slug": slug(entry["name"]), "name": entry["name"], "points": [(loc["latitude"], loc["longitude"])]})
                    have.add(slug(entry["name"]))
    return places


def gps_of(path: Path):
    """(lat, lon, taken) from EXIF, or None. Works for JPEG/PNG/WebP/HEIC with Pillow; DNG when it carries a TIFF GPS block."""
    from PIL import Image

    try:
        with Image.open(path) as im:
            exif = im.getexif()
            gps = exif.get_ifd(0x8825)
            taken = str(exif.get_ifd(0x8769).get(0x9003) or exif.get(0x0132) or "")
    except OSError:
        raise
    except Exception:
        return None
    if not gps or 2 not in gps or 4 not in gps:
        return None

    def deg(v, ref):
        d = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
        return -d if ref in ("S", "W") else d

    try:
        lat, lon = deg(gps[2], gps.get(1, "N")), deg(gps[4], gps.get(3, "E"))
    except Exception:
        return None
    if abs(lat) < 0.001 and abs(lon) < 0.001:
        return None
    return lat, lon, taken


def nearest(places, lat, lon):
    best = min(((km((lat, lon), pt), p) for p in places for pt in p["points"]), key=lambda t: t[0])
    return best[1], best[0]


def read_with_retry(path: Path, tries: int = 4):
    err = None
    for i in range(tries):
        try:
            return gps_of(path), None
        except OSError as e:
            time.sleep(2 * (i + 1))
            err = e
    return None, err


# ---------------------------------------------------------------- sort
def cmd_sort(args) -> int:
    src, dest = Path(args.src), Path(args.dest)
    places = load_places(args.pack)
    files = sorted(p for p in src.rglob("*") if p.is_file() and p.suffix.lower() in PHOTO_EXT)
    skipped = sum(1 for p in src.rglob("*") if p.is_file() and p.suffix.lower() not in PHOTO_EXT)
    print(f"{len(files)} photos to read ({skipped} other files such as videos are skipped); {len(places)} places")

    def work(p: Path):
        gps, err = read_with_retry(p)
        return p, gps, err

    rows, counts = [], {}
    with ThreadPoolExecutor(args.jobs) as pool:
        for i, (p, gps, err) in enumerate(pool.map(work, files), 1):
            if gps:
                lat, lon, taken = gps
                place, d = nearest(places, lat, lon)
                in_country = ICELAND[0] <= lat <= ICELAND[1] and ICELAND[2] <= lon <= ICELAND[3]
                if d <= args.max_km:
                    folder = place["slug"]
                elif in_country:
                    folder = f"_other_iceland/near-{place['slug']}"   # a roadside stop or a sight that has no card
                else:
                    folder = "_outside_iceland"
                note = f"{place['name']} {d * 1000:.0f} m"
            elif err:
                lat = lon = taken = None
                folder, note = "_unreadable", str(err)[:80]
            else:
                lat = lon = taken = None
                folder, note = f"_no_gps/{p.parent.name}", ""
            target_dir = dest / folder
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / p.name
            if target.exists() and target.stat().st_size != p.stat().st_size:
                target = target_dir / f"{p.parent.name}__{p.name}"   # same file name from another folder
            if not target.exists():
                shutil.copy2(p, target)
            counts[folder] = counts.get(folder, 0) + 1
            rows.append([str(p), str(target.relative_to(dest)), lat, lon, taken, folder, note])
            if i % 100 == 0:
                print(f"  {i}/{len(files)}", flush=True)
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "copy", "lat", "lon", "taken", "folder", "nearest place"])
        w.writerows(rows)
    print(f"\ncopied into {dest}  (manifest.csv lists every file)")
    for name, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"{n:5d}  {name}")
    return 0


# ---------------------------------------------------------------- portraits
def measure(path: Path, detector, recognizer) -> dict:
    import cv2
    import numpy as np
    from PIL import Image, ImageOps

    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        W, H = im.size
        scale = min(1.0, DETECT_SIDE / max(W, H))
        small = im.resize((max(1, round(W * scale)), max(1, round(H * scale))))
    bgr = cv2.cvtColor(np.asarray(small), cv2.COLOR_RGB2BGR)
    detector.setInputSize((bgr.shape[1], bgr.shape[0]))
    _, faces = detector.detect(bgr)
    found = []
    for f in (faces if faces is not None else []):
        if f[14] < MIN_FACE_SCORE:
            continue
        size = round(float(f[3]) / bgr.shape[0] * (H / min(W, H)), 4)   # face height / shorter side
        embedding = None
        if f[3] >= MIN_PIXELS:
            vec = recognizer.feature(recognizer.alignCrop(bgr, f)).flatten()
            embedding = [round(float(x), 4) for x in vec / (np.linalg.norm(vec) or 1)]
        box = [round(float(f[0]) / bgr.shape[1], 4), round(float(f[1]) / bgr.shape[0], 4),
               round(float(f[2]) / bgr.shape[1], 4), round(float(f[3]) / bgr.shape[0], 4)]
        found.append({"size": size, "box": box, "embedding": embedding})
    found.sort(key=lambda x: -x["size"])
    return {"version": FEATURE_VERSION, "width": W, "height": H, "faces": len(found), "found": found,
            "largest": found[0]["size"] if found else 0.0}


def cluster_people(cache: dict, min_photos: int):
    """Group faces into people by embedding. Returns (people, owner): people seen in >= min_photos photos, and
    {(photo, face index): person index} for their faces."""
    import numpy as np

    faces = [(rel, i, np.array(f["embedding"], dtype=np.float32), f["size"]) for rel, v in cache.items()
             for i, f in enumerate(v.get("found", [])) if f.get("embedding")]
    faces.sort(key=lambda t: -t[3])          # large, clear faces seed the groups
    centroids, members = [], []
    for rel, i, vec, _ in faces:
        best, score = -1, 0.0
        for c, cen in enumerate(centroids):
            sim = float(vec @ cen)
            if sim > score:
                best, score = c, sim
        if best >= 0 and score >= SAME_PERSON:
            members[best].append((rel, i, vec))
            cen = np.mean([m[2] for m in members[best]], axis=0)
            centroids[best] = cen / (np.linalg.norm(cen) or 1)
        else:
            centroids.append(vec / (np.linalg.norm(vec) or 1))
            members.append([(rel, i, vec)])
    people, owner = [], {}
    for group in sorted(members, key=lambda g: -len({m[0] for m in g})):
        photos = {m[0] for m in group}
        if len(photos) >= min_photos:
            pid = len(people)
            people.append({"photos": len(photos), "sample": group[0][:2]})
            for rel, i, _ in group:
                owner[(rel, i)] = pid
    return people, owner


def flagged(cache: dict, args):
    """({photo: reason}, people) for every measured photo that is a portrait of specific people."""
    people, owner = cluster_people(cache, args.min_photos)
    out = {}
    for rel, v in cache.items():
        if v.get("largest", 0) >= args.threshold:
            out[rel] = f"close-up (face {v['largest']:.2f})"
            continue
        for i, f in enumerate(v.get("found", [])):
            if (rel, i) in owner and f["size"] >= args.known_size:
                out[rel] = f"known person #{owner[(rel, i)] + 1} (face {f['size']:.2f})"
                break
    return out, people


def write_people_sheet(dest: Path, people, cache) -> None:
    from PIL import Image, ImageDraw, ImageOps

    if not people:
        return
    T = 160
    sheet = Image.new("RGB", (min(len(people), 8) * T, ((len(people) + 7) // 8) * (T + 18)), "white")
    d = ImageDraw.Draw(sheet)
    for n, person in enumerate(people):
        rel, i = person["sample"]
        f = cache[rel]["found"][i]
        path = dest / rel if (dest / rel).exists() else dest / "!deleted" / rel   # the sample may already be set aside
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            W, H = im.size
            x, y, w, h = f["box"]
            pad = 0.35
            box = (max(0, int((x - w * pad) * W)), max(0, int((y - h * pad) * H)),
                   min(W, int((x + w * (1 + pad)) * W)), min(H, int((y + h * (1 + pad)) * H)))
            crop = im.crop(box)
            crop.thumbnail((T, T))
        cx, cy = (n % 8) * T, (n // 8) * (T + 18)
        sheet.paste(crop, (cx, cy))
        d.text((cx + 3, cy + T + 2), f"#{n + 1}: {person['photos']} photos", fill="black")
    sheet.save(dest / "people.jpg", quality=85)


def photos_under(dest: Path):
    skip = {"people.jpg"}   # this tool's own output must not be measured as a photo
    return sorted(p for p in dest.rglob("*") if p.is_file() and p.suffix.lower() in PHOTO_EXT and p.name not in skip
                  and "!deleted" not in p.relative_to(dest).parts)


def cmd_portraits(args) -> int:
    import cv2

    dest = Path(args.dest)
    for model in (MODEL, REC_MODEL):
        if not model.exists():
            print(f"missing model {model}; download it from opencv_zoo (see the top of this file)", file=sys.stderr)
            return 2
    cache_path = dest / "features.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    todo = [p for p in photos_under(dest) if cache.get(str(p.relative_to(dest)), {}).get("version") != FEATURE_VERSION]
    print(f"{len(cache)} measured earlier, {len(todo)} to measure")
    detector = cv2.FaceDetectorYN.create(str(MODEL), "", (320, 320), 0.8, 0.3, 5000)
    recognizer = cv2.FaceRecognizerSF.create(str(REC_MODEL), "")
    for i, p in enumerate(todo, 1):
        key = str(p.relative_to(dest))
        try:
            cache[key] = measure(p, detector, recognizer)
        except Exception as e:
            cache[key] = {"version": FEATURE_VERSION, "error": str(e)[:100], "faces": 0, "largest": 0.0, "found": []}
        if i % 100 == 0:
            cache_path.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  {i}/{len(todo)}", flush=True)
    cache_path.write_text(json.dumps(cache), encoding="utf-8")

    cache.pop("people.jpg", None)
    live = {k: v for k, v in cache.items() if (dest / k).exists()}
    # Identity is learned from every photo measured, including ones already set aside; only photos still in place are flagged.
    reasons, people = flagged(cache, args)
    reasons = {k: v for k, v in reasons.items() if k in live}
    write_people_sheet(dest, people, cache)
    print(f"\nphotos still in place: {len(live)}; with a detected face: {sum(1 for v in live.values() if v['faces'])}")
    print(f"recurring people (seen in >= {args.min_photos} photos): {len(people)}  ->  {dest / 'people.jpg'}")
    for n, person in enumerate(people[:12], 1):
        print(f"  person #{n}: {person['photos']} photos")
    close = sum(1 for r in reasons.values() if r.startswith("close-up"))
    print(f"\nwould be set aside: {len(reasons)}  (close-ups {close}, known people {len(reasons) - close})")
    print(f"settings: --threshold {args.threshold}  --known-size {args.known_size}  --min-photos {args.min_photos}")
    if not args.apply:
        print("nothing moved (use --apply)")
        return 0
    deleted = dest / "!deleted"
    for rel in reasons:
        target = deleted / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dest / rel), str(target))
    write_review(deleted, reasons)
    print(f"\nmoved {len(reasons)} photos to {deleted}  (review.html shows them with the reason; `restore` puts them back)")
    return 0


def write_review(deleted: Path, reasons: dict) -> None:
    rows = []
    for rel, why in sorted(reasons.items()):
        rows.append(f'<figure><img loading="lazy" src="{rel.replace(chr(92), "/")}" alt=""><figcaption>{rel}<br><b>{why}</b></figcaption></figure>')
    (deleted / "review.html").write_text(
        "<!doctype html><meta charset=utf-8><title>Set aside as portraits</title>"
        "<style>body{font:14px system-ui;margin:16px;background:#f3f0e8}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}"
        "img{width:100%;height:160px;object-fit:cover;border-radius:6px}figure{margin:0}figcaption{font-size:11px;color:#555;word-break:break-all}</style>"
        f"<h1>Set aside as portraits ({len(rows)})</h1><p>Move any photo back to its place folder to keep it, or run <code>restore</code>.</p>"
        "<main>" + "".join(rows) + "</main>", encoding="utf-8")


def cmd_restore(args) -> int:
    dest = Path(args.dest)
    deleted = dest / "!deleted"
    n = 0
    for p in sorted(deleted.rglob("*")) if deleted.exists() else []:
        if p.is_file() and p.suffix.lower() in PHOTO_EXT:
            target = dest / p.relative_to(deleted)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(target))
            n += 1
    print(f"restored {n} photos")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sort")
    s.add_argument("src")
    s.add_argument("dest")
    s.add_argument("--pack", default="is")
    s.add_argument("--max-km", type=float, default=MAX_KM)
    s.add_argument("--jobs", type=int, default=8)
    s.set_defaults(fn=cmd_sort)
    p = sub.add_parser("portraits")
    p.add_argument("dest")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="close-up rule: largest face / shorter side")
    p.add_argument("--known-size", type=float, default=DEFAULT_KNOWN_SIZE, help="smallest face of a recurring person to count")
    p.add_argument("--min-photos", type=int, default=DEFAULT_MIN_PHOTOS, help="photos a person must appear in to count as recurring")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=cmd_portraits)
    r = sub.add_parser("restore")
    r.add_argument("dest")
    r.set_defaults(fn=cmd_restore)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
