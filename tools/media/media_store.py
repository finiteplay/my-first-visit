"""Content-addressed media store for a country pack: photos, pronunciation audio and the basics image.

Why: images and sound do not belong in git (they do not scale and cannot be removed from history later). Git keeps only
`content/<cc>/media-manifest.json`; the bytes live in a store whose layout is also the layout of the public bucket
(Cloudflare R2). Every file is stored under its content hash, so a changed file gets a new key, old releases keep working
and the files can be cached forever.

    python tools/media/media_store.py ingest is      # hash the pack's media, make card sizes, fill the store, write the manifest
    python tools/media/media_store.py verify is      # every manifest key exists in the store with the right hash
    python tools/media/media_store.py sync-local is  # copy the store into local-site/media/ for the local preview (git-ignored)
    python tools/media/media_store.py upload is      # dry run: what the bucket is missing
    python tools/media/media_store.py upload is --apply   # upload it (needs the R2_* variables below and boto3)

Store location: MFV_MEDIA_STORE (default ~/.finiteplay/media-store). Bucket upload variables: R2_ACCOUNT_ID,
R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET. The site reads media from MFV_MEDIA_BASE (default "media/").
Photos get a 640 px WebP "card" copy beside the full file; the grid uses the small one.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import mimetypes
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "local-site"
CARD_WIDTH = 640
CACHE = "public, max-age=31536000, immutable"


def store_dir() -> Path:
    return Path(os.environ.get("MFV_MEDIA_STORE", str(Path.home() / ".finiteplay" / "media-store")))


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def put(store: Path, key: str, data: bytes) -> None:
    dest = store / key
    if dest.exists() and dest.stat().st_size == len(data):
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)


def logical_files(pack: Path) -> list[tuple[str, str]]:
    """(kind, path relative to local-site) for every media file the pack uses."""
    found: list[tuple[str, str]] = []
    photos = pack / "photos.json"
    if photos.exists():
        for items in read_json(photos).get("attractions", {}).values():
            found += [("photos", p["file"]) for p in items]
    audio = pack / "place-audio.json"
    if audio.exists():
        for entry in read_json(audio).get("items", {}).values():
            found += [("audio", f["file"]) for f in entry.get("files", {}).values()]
    basics = pack / "basics.yaml"
    if basics.exists():
        image = (read_json(basics).get("volcano") or {}).get("image")
        if image and image.get("file"):
            found.append(("images", image["file"]))
    seen, out = set(), []
    for kind, path in found:
        if path not in seen:
            seen.add(path)
            out.append((kind, path))
    return out


def ingest(cc: str) -> int:
    from PIL import Image  # tooling only

    pack = ROOT / "content" / cc
    store = store_dir()
    manifest_path = pack / "media-manifest.json"
    old = read_json(manifest_path)["items"] if manifest_path.exists() else {}
    items: dict[str, dict] = {}
    missing = []
    for kind, logical in logical_files(pack):
        source = SITE / logical
        if not source.exists():
            if logical in old and (store / old[logical]["key"]).exists():
                items[logical] = old[logical]  # already ingested; the working copy was removed on purpose
                continue
            missing.append(logical)
            continue
        data = source.read_bytes()
        h = digest(data)
        ext = source.suffix.lower()
        key = f"{cc}/{kind}/{h[:16]}{ext}"
        put(store, key, data)
        entry = {"key": key, "sha256": h, "bytes": len(data), "type": mimetypes.guess_type(source.name)[0] or "application/octet-stream"}
        if kind == "photos":
            im = Image.open(io.BytesIO(data))
            entry["width"], entry["height"] = im.size
            card = im.convert("RGB")
            card.thumbnail((CARD_WIDTH, CARD_WIDTH * 2))
            buf = io.BytesIO()
            card.save(buf, "WEBP", quality=78, method=6)
            cdata = buf.getvalue()
            ckey = f"{cc}/photos/{h[:16]}-{CARD_WIDTH}.webp"
            put(store, ckey, cdata)
            entry["card"] = {"key": ckey, "sha256": digest(cdata), "bytes": len(cdata), "type": "image/webp",
                             "width": card.width, "height": card.height}
        items[logical] = entry
    if missing:
        print(f"{len(missing)} referenced files are missing from local-site and from the store, e.g. {missing[:3]}", file=sys.stderr)
        return 1
    manifest = {"schemaVersion": 1, "country": cc, "cache": CACHE, "items": dict(sorted(items.items()))}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    total = sum(e["bytes"] + e.get("card", {}).get("bytes", 0) for e in items.values())
    print(f"{len(items)} files, {total / 1e6:.1f} MB in the store at {store}; wrote {manifest_path.relative_to(ROOT)}")
    return 0


def all_keys(manifest: dict) -> list[tuple[str, dict]]:
    keys = []
    for entry in manifest["items"].values():
        keys.append((entry["key"], entry))
        if "card" in entry:
            keys.append((entry["card"]["key"], entry["card"]))
    return keys


def verify(cc: str) -> int:
    manifest = read_json(ROOT / "content" / cc / "media-manifest.json")
    store = store_dir()
    bad = []
    for key, entry in all_keys(manifest):
        path = store / key
        if not path.exists() or digest(path.read_bytes()) != entry["sha256"]:
            bad.append(key)
    print(f"{len(all_keys(manifest))} keys checked; {len(bad)} missing or wrong" + (f": {bad[:5]}" if bad else ""))
    return 1 if bad else 0


def sync_local(cc: str) -> int:
    manifest = read_json(ROOT / "content" / cc / "media-manifest.json")
    store, target = store_dir(), SITE / "media"
    copied = 0
    for key, _ in all_keys(manifest):
        dest = target / key
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(store / key, dest)
        copied += 1
    print(f"copied {copied} files into {target.relative_to(ROOT)}")
    return 0


def upload(cc: str, apply: bool) -> int:
    manifest = read_json(ROOT / "content" / cc / "media-manifest.json")
    store = store_dir()
    keys = all_keys(manifest)
    need = {k: os.environ.get(k) for k in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")}
    if not all(need.values()):
        print(f"{len(keys)} keys in the manifest. Set {', '.join(k for k, v in need.items() if not v)} to check or upload.")
        return 0 if not apply else 1
    import boto3  # tooling only

    s3 = boto3.client("s3", endpoint_url=f"https://{need['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                      aws_access_key_id=need["R2_ACCESS_KEY_ID"], aws_secret_access_key=need["R2_SECRET_ACCESS_KEY"], region_name="auto")
    todo = []
    for key, entry in keys:
        try:
            s3.head_object(Bucket=need["R2_BUCKET"], Key=f"myfirstvisit/{key}")
        except Exception:
            todo.append((key, entry))
    print(f"{len(todo)} of {len(keys)} keys are not in the bucket yet")
    if apply:
        for key, entry in todo:
            s3.put_object(Bucket=need["R2_BUCKET"], Key=f"myfirstvisit/{key}", Body=(store / key).read_bytes(),
                          ContentType=entry["type"], CacheControl=CACHE)
        print(f"uploaded {len(todo)} files")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["ingest", "verify", "sync-local", "upload"])
    ap.add_argument("country")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.command == "ingest":
        return ingest(args.country)
    if args.command == "verify":
        return verify(args.country)
    if args.command == "sync-local":
        return sync_local(args.country)
    return upload(args.country, args.apply)


if __name__ == "__main__":
    sys.exit(main())
