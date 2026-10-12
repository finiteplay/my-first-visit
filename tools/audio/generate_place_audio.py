"""Generate DRAFT synthetic pronunciation audio for Icelandic place names and words.

Voices: Piper Icelandic voices trained on Talrómur 1 (Reykjavík University and SÍM),
CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Credit is required.

This is a draft aid only. AGENTS.md: published packs use human, native-speaker recordings;
synthetic speech is allowed only in `draft` packs and must be labeled. Every output is marked
`status: draft-synthetic` in `content/<cc>/place-audio.json`. Each clip is also transcribed
back with the Icelandic Whisper model as a sanity check (not a pronunciation review).

    ~/.finiteplay/venv/Scripts/python tools/audio/generate_place_audio.py is --voice ugla
    ~/.finiteplay/venv/Scripts/python tools/audio/generate_place_audio.py is --only "Þingvellir" --voice bui --no-check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS = Path.home() / ".finiteplay" / "models" / "piper-is"
CREDIT = ("Synthetic voice: Piper Icelandic voice trained on Talrómur 1, "
          "Reykjavík University and SÍM, CC BY 4.0")
# English-language brand names are not Icelandic names, so no Icelandic voice is offered.
ENGLISH_BRANDS = {"Aurora Reykjavík", "FlyOver Iceland", "Mink Viking Portrait", "Magic Ice Reykjavík", "Lava Show", "Sky Lagoon"}
ATTEMPTS = 8  # takes tried per clip (variants alternate)
GOOD_ENOUGH = 0.95
SHOW_THRESHOLD = 0.75  # Whisper match on the normal take; below this a native listener must decide


def slug(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.replace("Þ", "Th").replace("þ", "th")
                                   .replace("Ð", "D").replace("ð", "d").replace("Æ", "Ae").replace("æ", "ae"))
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")


def collect_names(pack: Path) -> dict[str, dict]:
    """Map local Icelandic text -> {respelling, kind, meaning} for everything that gets audio:
    place names, the country and capital, courtesy/emergency/other phrases, signs and the extra
    vocabulary words. The first source to mention a text wins."""
    import csv
    items: dict[str, dict] = {}

    def add(local, respelling, kind, meaning):
        if local and local not in items:
            items[local] = {"respelling": respelling, "kind": kind, "meaning": meaning}

    for item in json.loads((pack / "sights.yaml").read_text(encoding="utf-8"))["items"]:
        add(item["local"], item.get("respelling", ""), "place", item["name"])
    basics = pack / "basics.yaml"
    if basics.exists():
        for name in json.loads(basics.read_text(encoding="utf-8")).get("names", []):
            add(name["local"], name.get("respelling", ""), "place", name["english"])
    for playbook in json.loads((pack / "playbooks.yaml").read_text(encoding="utf-8"))["playbooks"]:
        for group in playbook.get("whereToSoak", []):
            for place in group["places"]:
                add(place.get("local"), place.get("respelling", ""), "place", place["name"])
    phrases = pack / "phrases.csv"
    if phrases.exists():
        with phrases.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                add(row["local"], row["respelling"], "phrase", row["meaning"])
    primer = pack / "primer.yaml"
    if primer.exists():
        for sign in json.loads(primer.read_text(encoding="utf-8")).get("signs", []):
            add(sign["local"], sign["respelling"], "sign", sign["meaning"])
    vocab = pack / "vocabulary.yaml"
    if vocab.exists():
        config = json.loads(vocab.read_text(encoding="utf-8"))
        for word in config.get("extraWords", []):
            add(word["local"], word["respelling"], "word", word["meaning"])
        for word in config.get("placeWords", []):
            add(word["local"], word["respelling"], "place", word["meaning"])
    return items


def speak_text(local: str) -> str:
    """What the voice should say: fill-in-the-blank phrases lose their ellipsis."""
    text = re.sub(r"\s*[…]+\s*", " ", local).replace("...", " ")
    return re.sub(r"\s+([?!.,])", r"\1", text).strip()


def synth(voice, text: str, path: Path, length_scale: float) -> float:
    from piper import SynthesisConfig
    with wave.open(str(path), "wb") as wav:
        voice.synthesize_wav(text, wav, syn_config=SynthesisConfig(length_scale=length_scale))
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / wav.getframerate()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("--voice", default="ugla", choices=["ugla", "bui", "salka", "steinn"])
    ap.add_argument("--only", action="append")
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--missing-only", action="store_true", help="skip texts that already have audio in the manifest")
    args = ap.parse_args()

    from piper import PiperVoice
    model = MODELS / f"is_IS-{args.voice}-medium.onnx"
    if not model.exists():
        sys.exit(f"Missing voice model {model}")
    voice = PiperVoice.load(str(model), use_cuda=False)

    pack = ROOT / "content" / args.country
    out_dir = Path(args.out) if args.out else ROOT / "local-site" / "assets" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    names = collect_names(pack)
    if args.only:
        names = {k: v for k, v in names.items() if k in args.only}

    checker = None
    if not args.no_check:
        sys.path.insert(0, str(Path(__file__).parent))
        import check_recording as cr
        checker = (cr, cr.load_model())

    manifest_path = pack / "place-audio.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"schemaVersion": 1, "items": {}}
    manifest["credit"] = CREDIT
    manifest["status"] = "draft-synthetic; replace with native-speaker recordings before release"
    for local, info in names.items():
        key = slug(local)
        if args.missing_only and key in manifest["items"] and manifest["items"][key].get("files"):
            continue
        said = speak_text(local)
        entry = {"local": local, "respelling": info["respelling"], "kind": info["kind"], "meaning": info["meaning"],
                 "voice": f"piper is_IS-{args.voice}-medium",
                 "generated": time.strftime("%Y-%m-%d"), "status": "draft-synthetic", "files": {}}
        path = out_dir / f"{key}_normal.wav"
        best = None  # Piper sampling is random: keep the take Whisper hears best
        # Very short words are said more reliably with a closing period: alternate the variants.
        variants = [(said, 1.0)] if said[-1:] in "?!.," else [(said, 1.0), (said + ".", 1.0)]
        if len(said) <= 6 and said[-1:] not in "?!.,":
            variants += [(said + ".", 0.9), (said + "!", 1.0)]  # a lone short word is the hardest to get right
        for attempt in range(ATTEMPTS if checker else 1):
            text, scale = variants[attempt % len(variants)]
            seconds = synth(voice, text, path, scale)
            if not checker:
                best = (0.0, path.read_bytes(), seconds, "")
                break
            cr, model_w = checker
            heard = cr.transcribe(model_w, path)
            score = cr.similarity(heard, said)
            if best is None or score > best[0]:
                best = (score, path.read_bytes(), seconds, heard)
            if score >= GOOD_ENOUGH:
                break
        path.write_bytes(best[1])
        entry["files"]["normal"] = {"file": f"assets/audio/{path.name}", "seconds": round(best[2], 2)}
        if checker:
            entry["whisperHeard"] = best[3]
            entry["whisperMatch"] = round(best[0], 2)
        entry["showInApp"] = bool(checker) and entry.get("whisperMatch", 0) >= SHOW_THRESHOLD \
            and local not in ENGLISH_BRANDS
        manifest["items"][key] = entry
        extra = f" heard {entry.get('whisperHeard')!r} ({entry.get('whisperMatch')})" if checker else ""
        print(f"{local}: {entry['files']['normal']['seconds']}s{extra}  (then: python tools/media/media_store.py ingest is)")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
