"""Compile the current Iceland draft into browser-local website data."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "content" / "is"
OUTPUT = Path(__file__).resolve().parent / "content.js"


def read_json(name: str):
    return json.loads((PACK / name).read_text(encoding="utf-8"))


def is_simple(local, group, config):
    """Word page rule: single words and two-word expressions; no blanks. Place names are exempt."""
    rules = config.get("rules", {})
    if group["from"].get("kind") in rules.get("exemptKinds", []):
        return True
    if "…" in local or "..." in local:
        return False
    return len(local.replace("?", "").split()) <= rules.get("maxWords", 99)


def build_vocabulary():
    """Courtesy and emergency words always; every other word only if it has approved audio."""
    import csv
    if not (PACK / "vocabulary.yaml").exists():
        return {}
    config = read_json("vocabulary.yaml")
    audio = {}
    if (PACK / "place-audio.json").exists():
        manifest = read_json("place-audio.json")
        audio = {e["local"]: e for e in manifest["items"].values() if e.get("showInApp")}
    with (PACK / "phrases.csv").open(encoding="utf-8-sig", newline="") as stream:
        phrases = list(csv.DictReader(stream))
    signs = read_json("primer.yaml").get("signs", [])
    seen, groups = set(), []
    for group in config["groups"]:
        source, candidates = group["from"], []
        if "phraseCategory" in source:
            candidates += [{"local": r["local"], "respelling": r["respelling"], "meaning": r["meaning"], "when": r["when"]}
                           for r in phrases if r["category"] == source["phraseCategory"]]
        if source.get("extraWords"):
            candidates += [{"local": w["local"], "respelling": w["respelling"], "meaning": w["meaning"], "when": w.get("when", "")}
                           for w in config.get("extraWords", [])]
        if source.get("kind") == "sign":
            candidates += [{"local": x["local"], "respelling": x["respelling"], "meaning": x["meaning"], "when": ""} for x in signs]
        if source.get("kind") == "place":
            candidates += [{"local": e["local"], "respelling": e["respelling"], "meaning": e["meaning"], "when": ""}
                           for e in audio.values() if e.get("kind") == "place"]
        if source.get("placeWords"):
            candidates = [{"local": w["local"], "respelling": w["respelling"], "meaning": w["meaning"],
                           "when": w.get("when", ""), "force": w.get("alwaysShow", False)}
                          for w in config.get("placeWords", [])] + candidates
        items = []
        for item in candidates:
            if item["local"] in seen:
                continue
            if not is_simple(item["local"], group, config):
                continue
            clip = audio.get(item["local"])
            if not clip and not group.get("alwaysShow") and not item.get("force"):
                continue
            seen.add(item["local"])
            item.pop("force", None)
            items.append({**item, "hasAudio": bool(clip)})
        if items:
            groups.append({"id": group["id"], "title": group["title"], "intro": group["intro"],
                           "callout": group.get("callout"), "items": items})
    return {"title": config["title"], "intro": config["intro"], "note": config["note"], "groups": groups}


content = {
    "pack": read_json("pack.yaml"),
    "briefings": read_json("briefings.yaml")["briefings"],
    "playbooks": read_json("playbooks.yaml")["playbooks"],
    "routes": read_json("routes.yaml")["routes"],
    "places": read_json("sights.yaml")["items"],
    "placeAreas": read_json("sights.yaml").get("areas", []),
    "basics": read_json("basics.yaml"),
    "vocabulary": build_vocabulary(),
    "map": read_json("map.yaml") if (PACK / "map.yaml").exists() else {},
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



# Cache busting: tag each script and stylesheet reference with a short hash of its content, so a browser that has an old
# copy (for example an old content.js without the newest photos) fetches the new one after every build.
import hashlib
import re

SITE = OUTPUT.parent
for page in ("index.html", "words.html"):
    path = SITE / page
    if not path.exists():
        continue
    html = path.read_text(encoding="utf-8")
    for asset in ("content.js", "app.js", "words.js", "styles.css"):
        file = SITE / asset
        if not file.exists():
            continue
        digest = hashlib.sha1(file.read_bytes()).hexdigest()[:8]
        html = re.sub(rf'((?:src|href)="{re.escape(asset)})(?:\?v=[^"]*)?"', rf'\1?v={digest}"', html)
    path.write_text(html, encoding="utf-8")
print("Tagged asset references with content hashes")
