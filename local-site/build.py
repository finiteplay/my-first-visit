"""Compile the current Iceland draft into browser-local website data."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "content" / "is"
OUTPUT = Path(__file__).resolve().parent / "content.js"


def read_json(name: str):
    return json.loads((PACK / name).read_text(encoding="utf-8"))


content = {
    "pack": read_json("pack.yaml"),
    "briefings": read_json("briefings.yaml")["briefings"],
    "playbooks": read_json("playbooks.yaml")["playbooks"],
    "routes": read_json("routes.yaml")["routes"],
    "places": read_json("sights.yaml")["items"],
    # Author-selected photos only (tools/media/apply_selection.py); others stay pending.
    "photos": read_json("photos.json")["attractions"] if (PACK / "photos.json").exists() else {},
    # Draft synthetic pronunciation (tools/audio/generate_place_audio.py); only clips approved
    # for preview are shown. Replace with native-speaker recordings before release.
    "placeAudio": read_json("place-audio.json") if (PACK / "place-audio.json").exists() else {},
}

OUTPUT.write_text(
    "window.ICELAND_CONTENT = "
    + json.dumps(content, ensure_ascii=False, separators=(",", ":"))
    + ";\n",
    encoding="utf-8",
)
print(f"Built {OUTPUT.relative_to(ROOT)}")

