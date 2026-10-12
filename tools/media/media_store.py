"""Content-addressed media store for a country pack: photos, pronunciation audio and the basics image.

Why: images and sound do not belong in git (they do not scale and cannot be removed from history later). Git keeps only
`content/<cc>/media-manifest.json`; the bytes live in a store whose layout is also the layout of the public bucket
(Cloudflare R2). Every served file is stored under the hash of its bytes, so a changed file gets a new key, old releases
keep working and the files can be cached forever.

    python tools/media/media_store.py ingest is      # encode the pack's media, fill the store, write the manifest
    python tools/media/media_store.py verify is      # every manifest key exists in the store with the right hash
    python tools/media/media_store.py sync-local is  # mirror the store into local-site/media/ for the local preview (git-ignored)
    python tools/media/media_store.py upload is      # dry run: what the bucket is missing
    python tools/media/media_store.py upload is --apply   # upload it (needs the R2_* variables below and boto3)

Store location: MFV_MEDIA_STORE (default ~/.finiteplay/media-store). Bucket upload variables: R2_ACCOUNT_ID,
R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET. The site reads media from MFV_MEDIA_BASE (default "media/").

Encoding. Served files are always re-encoded from the originals; originals stay in the store under `<cc>/originals/`
(never uploaded, never in the manifest keys) so the settings can change later without hunting for sources.
  photos  1440 px long edge, WebP q80, converted to sRGB, EXIF/GPS stripped; plus a 640 px WebP card copy for the grid
  audio   leading silence trimmed to 60 ms and tail to 150 ms, peak normalised to -1.5 dBFS, AAC-LC mono 48 kbit/s (.m4a)
  images  like photos, without the card copy
Needs Pillow; audio needs ffmpeg on PATH or `pip install imageio-ffmpeg`.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "local-site"
CARD_WIDTH = 640
FULL_WIDTH = 1440
WEBP_QUALITY = 80
CARD_QUALITY = 78
AUDIO_KBPS = 48
LEAD_MS, TAIL_MS, PEAK_DBFS = 60, 150, -1.5
ENCODER = f"photo=webp{FULL_WIDTH}q{WEBP_QUALITY}+card{CARD_WIDTH}q{CARD_QUALITY};audio=aac{AUDIO_KBPS}k-mono-trim{LEAD_MS}/{TAIL_MS}-peak{PEAK_DBFS};v2"
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


def originals_path(store: Path, cc: str, h: str, ext: str) -> Path:
    return store / cc / "originals" / f"{h[:16]}{ext}"


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


def to_srgb(im):
    """Convert to sRGB using the embedded profile; wide-gamut photos would look dull once the profile is dropped."""
    from PIL import ImageCms

    icc = im.info.get("icc_profile")
    if not icc:
        return im.convert("RGB")
    try:
        source = ImageCms.getOpenProfile(io.BytesIO(icc))
        return ImageCms.profileToProfile(im.convert("RGB") if im.mode not in ("RGB", "CMYK") else im,
                                         source, ImageCms.createProfile("sRGB"), outputMode="RGB")
    except Exception:
        return im.convert("RGB")


def webp(im, width: int, quality: int) -> bytes:
    im = im.copy()
    im.thumbnail((width, width))  # long edge limit, landscape and portrait alike; never upscales
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    return buf.getvalue()


def encode_photo(data: bytes, card: bool):
    from PIL import Image, ImageOps

    im = to_srgb(ImageOps.exif_transpose(Image.open(io.BytesIO(data))))
    full = webp(im, FULL_WIDTH, WEBP_QUALITY)
    full_size = Image.open(io.BytesIO(full)).size
    if not card:
        return full, full_size, None, None
    small = webp(im, CARD_WIDTH, CARD_QUALITY)
    return full, full_size, small, Image.open(io.BytesIO(small)).size


def ffmpeg_exe() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    import imageio_ffmpeg  # tooling only

    return imageio_ffmpeg.get_ffmpeg_exe()


def encode_audio(wav_bytes: bytes) -> bytes:
    """Trim silence, normalise the peak, encode AAC-LC mono. Source is 16-bit mono PCM WAV."""
    import array

    with wave.open(io.BytesIO(wav_bytes)) as w:
        rate, width, channels = w.getframerate(), w.getsampwidth(), w.getnchannels()
        pcm = array.array("h", w.readframes(w.getnframes()))
    if width != 2 or channels != 1:
        raise ValueError(f"expected 16-bit mono WAV, got {width * 8}-bit x{channels}")
    peak = max((abs(x) for x in pcm), default=0) or 1
    gate = peak * 0.02
    first = next((i for i, x in enumerate(pcm) if abs(x) > gate), 0)
    last = len(pcm) - next((i for i, x in enumerate(reversed(pcm)) if abs(x) > gate), 0)
    start = max(0, first - rate * LEAD_MS // 1000)
    end = min(len(pcm), last + rate * TAIL_MS // 1000)
    gain = 10 ** (PEAK_DBFS / 20) * 32767 / peak
    trimmed = array.array("h", (max(-32768, min(32767, round(x * gain))) for x in pcm[start:end]))
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "in.wav", Path(tmp) / "out.m4a"
        with wave.open(str(src), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(trimmed.tobytes())
        subprocess.run([ffmpeg_exe(), "-v", "error", "-y", "-i", str(src), "-c:a", "aac", "-b:a", f"{AUDIO_KBPS}k",
                        "-ac", "1", "-map_metadata", "-1", "-movflags", "+faststart", str(dst)], check=True)
        return dst.read_bytes()


def entry_for(cc: str, kind: str, logical: str, data: bytes, store: Path, old: dict | None) -> dict:
    """Encode one original and return its manifest entry; reuses the old entry when source and encoder are unchanged."""
    h = digest(data)
    if old and old.get("source", {}).get("sha256") == h and old.get("encoder") == ENCODER:
        keys = [old["key"]] + ([old["card"]["key"]] if "card" in old else [])
        if all((store / k).exists() for k in keys):
            return old
    orig = originals_path(store, cc, h, Path(logical).suffix.lower())
    if not orig.exists():
        orig.parent.mkdir(parents=True, exist_ok=True)
        orig.write_bytes(data)
    source = {"sha256": h, "bytes": len(data)}
    if kind == "audio":
        blob = encode_audio(data)
        key = f"{cc}/audio/{digest(blob)[:16]}.m4a"
        put(store, key, blob)
        return {"key": key, "sha256": digest(blob), "bytes": len(blob), "type": "audio/mp4", "source": source, "encoder": ENCODER}
    full, size, small, small_size = encode_photo(data, card=(kind == "photos"))
    key = f"{cc}/{kind}/{digest(full)[:16]}.webp"
    put(store, key, full)
    entry = {"key": key, "sha256": digest(full), "bytes": len(full), "type": "image/webp", "width": size[0], "height": size[1],
             "source": source, "encoder": ENCODER}
    if small:
        ckey = f"{cc}/photos/{digest(small)[:16]}-{CARD_WIDTH}.webp"
        put(store, ckey, small)
        entry["card"] = {"key": ckey, "sha256": digest(small), "bytes": len(small), "type": "image/webp",
                         "width": small_size[0], "height": small_size[1]}
    return entry


def original_bytes(store: Path, cc: str, logical: str, prior: dict | None) -> bytes | None:
    working = SITE / logical
    if working.exists():
        return working.read_bytes()
    if prior and "source" in prior:
        path = originals_path(store, cc, prior["source"]["sha256"], Path(logical).suffix.lower())
        return path.read_bytes() if path.exists() else None
    if prior and (store / prior["key"]).exists():
        return (store / prior["key"]).read_bytes()  # first-generation manifest: the stored file is the original
    return None


def ingest(cc: str) -> int:
    pack = ROOT / "content" / cc
    store = store_dir()
    manifest_path = pack / "media-manifest.json"
    old = read_json(manifest_path)["items"] if manifest_path.exists() else {}
    items: dict[str, dict] = {}
    missing = []
    for kind, logical in logical_files(pack):
        data = original_bytes(store, cc, logical, old.get(logical))
        if data is None:
            missing.append(logical)
            continue
        items[logical] = entry_for(cc, kind, logical, data, store, old.get(logical))
    if missing:
        print(f"{len(missing)} referenced files are missing from local-site and from the store, e.g. {missing[:3]}", file=sys.stderr)
        return 1
    manifest = {"schemaVersion": 2, "country": cc, "cache": CACHE, "encoder": ENCODER, "items": dict(sorted(items.items()))}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    served = sum(e["bytes"] + e.get("card", {}).get("bytes", 0) for e in items.values())
    original = sum(e["source"]["bytes"] for e in items.values())
    print(f"{len(items)} files: {original / 1e6:.1f} MB originals -> {served / 1e6:.1f} MB served; wrote {manifest_path.relative_to(ROOT)}")
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
    wanted = {key for key, _ in all_keys(manifest)}
    removed = 0
    if target.exists():
        for stale in [p for p in target.rglob("*") if p.is_file() and p.relative_to(target).as_posix() not in wanted]:
            stale.unlink()
            removed += 1
    copied = 0
    for key in sorted(wanted):
        dest = target / key
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(store / key, dest)
        copied += 1
    print(f"copied {copied} files into {target.relative_to(ROOT)}, removed {removed} stale")
    return 0


def prune_store(cc: str, apply: bool) -> int:
    """Delete served-file keys in the store that no manifest entry points to (originals are kept)."""
    manifest = read_json(ROOT / "content" / cc / "media-manifest.json")
    wanted = {key for key, _ in all_keys(manifest)}
    base = store_dir() / cc
    stale = [p for p in base.rglob("*") if p.is_file() and "originals" not in p.relative_to(base).parts
             and f"{cc}/{p.relative_to(base).as_posix()}" not in wanted]
    print(f"{len(stale)} unreferenced served files, {sum(p.stat().st_size for p in stale) / 1e6:.1f} MB" + ("" if apply else " (dry run; use --apply)"))
    if apply:
        for p in stale:
            p.unlink()
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
    ap.add_argument("command", choices=["ingest", "verify", "sync-local", "prune-store", "upload"])
    ap.add_argument("country")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.command == "ingest":
        return ingest(args.country)
    if args.command == "verify":
        return verify(args.country)
    if args.command == "sync-local":
        return sync_local(args.country)
    if args.command == "prune-store":
        return prune_store(args.country, args.apply)
    return upload(args.country, args.apply)


if __name__ == "__main__":
    sys.exit(main())
