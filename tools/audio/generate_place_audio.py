"""Generate DRAFT synthetic pronunciation audio for Icelandic place names (normal and 0.5x slow).

Voices: Piper Icelandic voices trained on Talrómur 1 (Reykjavík University and SÍM),
CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ . Credit is required.

This is a draft aid only. AGENTS.md: published packs use human, native-speaker recordings;
synthetic speech is allowed only in `draft` packs and must be labeled. Every output is marked
`status: draft-synthetic` in `content/<cc>/place-audio.json`. Each clip is also transcribed
back with the Icelandic Whisper model as a sanity check (not a pronunciation review).

    ~/.finiteplay/venv/Scripts/python tools/audio/generate_place_audio.py is --voice ugla
    ~/.finiteplay/venv/Scripts/python tools/audio/generate_place_audio.py is --only "Þingvellir" --voice bui --no-check

Slow take: `length_scale=2.0`, i.e. phonemes stretched to twice the duration (0.5x speed)
while keeping the pitch natural, which sounds better than resampling.
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
SLOW_SCALE = 2.0  # 0.5x speed
# English-language brand names are not Icelandic names, so no Icelandic voice is offered.
ENGLISH_BRANDS = {"Aurora Reykjavík", "FlyOver Iceland", "Mink Viking Portrait"}
SHOW_THRESHOLD = 0.75  # Whisper match on the normal take; below this a native listener must decide


def slug(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.replace("Þ", "Th").replace("þ", "th")
                                   .replace("Ð", "D").replace("ð", "d").replace("Æ", "Ae").replace("æ", "ae"))
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")


def collect_names(pack: Path) -> dict[str, str]:
    """Map local Icelandic name -> respelling (draft) from sights and playbook place entries."""
    names: dict[str, str] = {}
    for item in json.loads((pack / "sights.yaml").read_text(encoding="utf-8"))["items"]:
        names.setdefault(item["local"], item.get("respelling", ""))
    for playbook in json.loads((pack / "playbooks.yaml").read_text(encoding="utf-8"))["playbooks"]:
        for group in playbook.get("whereToSoak", []):
            for place in group["places"]:
                if place.get("local"):
                    names.setdefault(place["local"], place.get("respelling", ""))
    return names


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
    for local, respelling in names.items():
        key = slug(local)
        entry = {"local": local, "respelling": respelling, "voice": f"piper is_IS-{args.voice}-medium",
                 "generated": time.strftime("%Y-%m-%d"), "status": "draft-synthetic", "files": {}}
        for take, scale in (("normal", 1.0), ("slow", SLOW_SCALE)):
            path = out_dir / f"{key}_{take}.wav"
            seconds = synth(voice, local, path, scale)
            entry["files"][take] = {"file": f"assets/audio/{path.name}", "seconds": round(seconds, 2)}
        if checker:
            cr, model_w = checker
            heard = cr.transcribe(model_w, out_dir / f"{key}_normal.wav")
            entry["whisperHeard"] = heard
            entry["whisperMatch"] = round(cr.similarity(heard, local), 2)
        entry["showInApp"] = bool(checker) and entry.get("whisperMatch", 0) >= SHOW_THRESHOLD             and local not in ENGLISH_BRANDS
        manifest["items"][key] = entry
        extra = f" heard {entry.get('whisperHeard')!r} ({entry.get('whisperMatch')})" if checker else ""
        print(f"{local}: normal {entry['files']['normal']['seconds']}s, slow {entry['files']['slow']['seconds']}s{extra}")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
