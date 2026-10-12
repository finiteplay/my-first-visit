#!/usr/bin/env python3
"""Validate research-backed reader content independently of the legacy language schema."""
import argparse
import csv
import json
import sys
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


# Completeness standard, docs/CONTENT.md "Completeness standard". The bar is the
# pack-for-exposure and rental-counter-before-counter Iceland playbooks.
MIN_PARAGRAPHS, MIN_WORDS, MIN_SOURCES = 4, 300, 8


def _paragraphs(value):
    return [value] if isinstance(value, str) else list(value or [])


def _role_gaps(source_ids, roles):
    have = {roles.get(sid, "") for sid in source_ids}
    gaps = []
    if "traveler" not in have:
        gaps.append("needs at least one traveler source")
    if not have & {"official", "provider"}:
        gaps.append("needs at least one official or provider source")
    return gaps


def playbook_depth(item, roles):
    gaps = []
    if not (item.get("cardImage") or {}).get("alt"):
        gaps.append("cardImage with alt text is required")
    if not str(item.get("hook", "")).strip():
        gaps.append("hook is required")
    body = _paragraphs(item.get("body"))
    words = sum(len(p.split()) for p in body)
    if len(body) < MIN_PARAGRAPHS or words < MIN_WORDS:
        gaps.append(f"body needs {MIN_PARAGRAPHS}+ paragraphs and {MIN_WORDS}+ words "
                    f"(has {len(body)}, {words})")
    decision = item.get("decision") or {}
    options = [o for o in item.get("options", []) if o.get("bestFor") and o.get("tradeoff")]
    if len([v for v in decision.values() if str(v).strip()]) < 3 and len(options) < 3:
        gaps.append("needs a three-path decision or 3+ options with bestFor and tradeoff")
    if len(item.get("checklist", [])) < 5 and len(item.get("avoid", [])) < 3:
        gaps.append("needs a checklist of 5+ steps or 3+ avoid items")
    if len(item.get("liveChecks", [])) < 3:
        gaps.append("needs 3+ liveChecks")
    source_ids = item.get("sourceIds", [])
    if len(source_ids) < MIN_SOURCES:
        gaps.append(f"needs {MIN_SOURCES}+ source IDs (has {len(source_ids)})")
    gaps += _role_gaps(source_ids, roles)
    if str(item.get("evidenceLabel", "")).lower() == "experiences vary":
        if len(item.get("travelerStories", [])) < 2:
            gaps.append("'Experiences vary' needs 2+ contrasting travelerStories")
        if not str(item.get("limits", "")).strip():
            gaps.append("'Experiences vary' needs a limits statement")
    return gaps


def _nights(duration):
    import re
    numbers = [int(n) for n in re.findall(r"\d+", str(duration))]
    return max(numbers) if numbers else 0


def route_depth(item, roles):
    gaps = []
    if not str(item.get("whoFor", "")).strip():
        gaps.append("whoFor is required")
    days = item.get("days", [])
    nights = _nights(item.get("duration"))
    if len(days) < max(1, nights):
        gaps.append(f"days needs one entry per day (has {len(days)}, duration suggests {nights} nights)")
    for index, day in enumerate(days, 1):
        missing = [k for k in ("base", "travel", "highlights") if not day.get(k)]
        if missing:
            gaps.append(f"day {index} missing {', '.join(missing)}")
    if nights >= 4 and not any(d.get("flexible") or d.get("weatherSwap") for d in days):
        gaps.append("routes of 4+ nights need a flexible or weatherSwap day")
    if not str(item.get("seasonNotes", "")).strip():
        gaps.append("seasonNotes is required")
    if not (item.get("tradeoff") or item.get("skipIf")):
        gaps.append("tradeoff or skipIf is required")
    if len(item.get("liveChecks", [])) < 2:
        gaps.append("needs 2+ liveChecks")
    source_ids = item.get("sourceIds", [])
    if len(source_ids) < 5:
        gaps.append(f"needs 5+ source IDs (has {len(source_ids)})")
    gaps += _role_gaps(source_ids, roles)
    return gaps


def score_errors(item):
    """Third-party ratings, review counts, ranks and links must not be published (their terms forbid it); only our own
    blended `score` (tools/content/build_score.py) is allowed on a place."""
    errors = []
    for banned in ("tripadvisor", "google", "yelp", "reviews", "rating"):
        if banned in item:
            errors.append(f"sights.yaml {item.get('id')}: `{banned}` must not be in the content; publish only the blended `score`.")
    score = item.get("score")
    if score is not None:
        stars = score.get("stars")
        if not isinstance(stars, (int, float)) or isinstance(stars, bool) or not (1 <= stars <= 5):
            errors.append(f"sights.yaml {item.get('id')}: score.stars must be a number from 1 to 5.")
        rank = score.get("rank")
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            errors.append(f"sights.yaml {item.get('id')}: score.rank must be a whole number from 1.")
        if not score.get("method") or not score.get("asOf"):
            errors.append(f"sights.yaml {item.get('id')}: score needs method and asOf.")
    return errors


def basics_audit(basics, evidence_ids, root_dir=Path('.'), media_items=None):
    """The 'Iceland at a glance' section: pronounced names, sourced and iconned numbers."""
    errors = []
    names = basics.get("names", [])
    if len(names) < 2:
        errors.append("basics.yaml: needs the country name and the capital (2+ names).")
    for name in names:
        label = name.get("local", "<missing>")
        for field in ("english", "local", "respelling", "meaning"):
            if not str(name.get(field, "")).strip():
                errors.append(f"basics.yaml name {label}: {field} is required.")
    image = (basics.get("volcano") or {}).get("image")
    if basics.get("volcano") and not image:
        errors.append("basics.yaml volcano: an image is required.")
    if image:
        for field in ("file", "alt", "author", "license", "sourceUrl", "downloadedAt", "status"):
            if not str(image.get(field, "")).strip():
                errors.append(f"basics.yaml volcano image: {field} is required (author, license and source must be recorded).")
        if "nc" in str(image.get("license", "")).lower().split() or "nd" in str(image.get("license", "")).lower().split():
            errors.append("basics.yaml volcano image: NC/ND licenses are not allowed.")
        logical = str(image.get("file", ""))
        if logical not in (media_items or {}) and not (root_dir / logical).exists():
            errors.append("basics.yaml volcano image: file is in neither media-manifest.json nor local-site.")
    checks = basics.get("dailyChecks")
    if checks:
        if len(checks.get("links", [])) < 2:
            errors.append("basics.yaml dailyChecks: needs 2+ links (weather and roads).")
        for link in checks.get("links", []):
            if not str(link.get("url", "")).startswith("https://"):
                errors.append(f"basics.yaml dailyChecks {link.get('label')}: url must use https.")
        if set(checks.get("sourceIds", [])) - evidence_ids:
            errors.append("basics.yaml dailyChecks: unknown source IDs.")
    best = basics.get("bestTime")
    if best:
        seasons = best.get("seasons", [])
        if len(seasons) < 4:
            errors.append("basics.yaml bestTime: needs all four seasons.")
        for season in seasons:
            for field in ("months", "daylight", "goodFor", "watchFor"):
                if not season.get(field):
                    errors.append(f"basics.yaml bestTime {season.get('id')}: {field} is required.")
            unknown = set(season.get("sourceIds", [])) - evidence_ids
            if unknown or not season.get("sourceIds"):
                errors.append(f"basics.yaml bestTime {season.get('id')}: needs sources that exist in the corpus {sorted(unknown)}.")
        if not str(best.get("takeaway", "")).strip():
            errors.append("basics.yaml bestTime: a takeaway is required.")
    if len(basics.get("numbers", [])) < 4:
        errors.append("basics.yaml: needs 4+ numbers.")
    for number in basics.get("numbers", []):
        if not str(number.get("icon", "")).strip():
            errors.append(f"basics.yaml number {number.get('label')}: an icon is required.")
    groups = [("name", names), ("number", basics.get("numbers", []))]
    for kind, items in groups:
        for item in items:
            title = item.get("title") or item.get("label") or item.get("local") or "<item>"
            if not item.get("sourceIds"):
                errors.append(f"basics.yaml {kind} {title}: sourceIds are required.")
            unknown = set(item.get("sourceIds", [])) - evidence_ids
            if unknown:
                errors.append(f"basics.yaml {kind} {title}: unknown source IDs {sorted(unknown)}.")
    return errors


def vocabulary_audit(vocab, evidence_ids):
    """The 'Say it in Icelandic' section: courtesy and emergency groups plus pronounced extra words."""
    errors = []
    groups = {group.get("id"): group for group in vocab.get("groups", [])}
    for required in ("courtesy", "emergency"):
        if required not in groups:
            errors.append(f"vocabulary.yaml: a {required} group is required.")
        elif not groups[required].get("alwaysShow"):
            errors.append(f"vocabulary.yaml: the {required} group must always be shown, with or without audio.")
    for word in vocab.get("extraWords", []) + vocab.get("placeWords", []):
        label = word.get("local", "<missing>")
        for field in ("local", "respelling", "meaning"):
            if not str(word.get(field, "")).strip():
                errors.append(f"vocabulary.yaml word {label}: {field} is required.")
        limit = vocab.get("rules", {}).get("maxWords")
        if limit and len(str(word.get("local", "")).split()) > limit:
            errors.append(f"vocabulary.yaml word {label}: more than {limit} words; keep the word page simple.")
        if not word.get("sourceIds"):
            errors.append(f"vocabulary.yaml word {label}: sourceIds are required.")
        unknown = set(word.get("sourceIds", [])) - evidence_ids
        if unknown:
            errors.append(f"vocabulary.yaml word {label}: unknown source IDs {sorted(unknown)}.")
    return errors


def map_audit(map_data, evidence_ids):
    """The small country map: an outline, route lines and points that all fall on the outline."""
    errors = []
    outline = map_data.get("outline", [])
    if len(outline) < 50:
        errors.append("map.yaml: the outline needs 50+ points (the map would look like a blob).")
        return errors
    lons, lats = [p[0] for p in outline], [p[1] for p in outline]
    box = (min(lons), max(lons), min(lats), max(lats))

    def inside(lon, lat):
        return box[0] <= lon <= box[1] and box[2] <= lat <= box[3]

    kinds = {"town", "gc", "glacier", "glacier-lagoon", "volcano"}
    for point in map_data.get("points", []):
        if point.get("kind") not in kinds:
            errors.append(f"map.yaml point {point.get('id')}: unknown kind {point.get('kind')!r}.")
        if not inside(point.get("lon", 999), point.get("lat", 999)):
            errors.append(f"map.yaml point {point.get('id')}: outside the country's bounding box.")
    for line in map_data.get("lines", []):
        for lon, lat in line.get("points", []):
            if not inside(lon, lat):
                errors.append(f"map.yaml line {line.get('id')}: a waypoint is outside the bounding box.")
                break
    for region in map_data.get("regions", []):
        west, south, east, north = region.get("bbox", [0, 0, 0, 0])
        if not region.get("land") or not str(region.get("credit", "")).strip():
            errors.append(f"map.yaml region {region.get('id')}: land rings and a data credit are required.")
        if not (west < region.get("center", [999, 999])[0] < east and south < region.get("center", [999, 999])[1] < north):
            errors.append(f"map.yaml region {region.get('id')}: center is outside its bbox.")
    unknown = set(map_data.get("sourceIds", [])) - evidence_ids
    if unknown:
        errors.append(f"map.yaml: unknown source IDs {sorted(unknown)}.")
    if not str(map_data.get("credit", "")).strip():
        errors.append("map.yaml: a data credit is required (outline source and license).")
    return errors


def route_place_errors(route, sight_ids, soak_slugs):
    """Every place a trip day links to must exist: a place card, or a soak entry written as soak:<slug>."""
    errors = []
    for number, day in enumerate(route.get("days", []), 1):
        for place_id in day.get("placeIds", []):
            known = (place_id[5:] in soak_slugs) if place_id.startswith("soak:") else (place_id in sight_ids)
            if not known:
                errors.append(f"routes.yaml {route.get('id')} day {number}: unknown place {place_id!r}.")
    return errors


def _slug(name):
    import re
    import unicodedata
    folded = "".join(c for c in unicodedata.normalize("NFD", name) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")


def layout_errors(item, kind, place_ids):
    """Article layout fields: key points, section breaks and figures must be well formed."""
    errors = []
    points = item.get("keyPoints")
    if points is not None and not 2 <= len(points) <= 4:
        errors.append(f"{kind} {item.get('id')}: keyPoints needs 2 to 4 short points.")
    breaks = item.get("sectionBreaks")
    if breaks:
        starts = [b.get("at") for b in breaks]
        if starts[0] != 0 or starts != sorted(set(starts)) or starts[-1] >= len(item.get("body", [])):
            errors.append(f"{kind} {item.get('id')}: sectionBreaks must start at 0, ascend and stay inside the body.")
        if any(not str(b.get("title", "")).strip() for b in breaks):
            errors.append(f"{kind} {item.get('id')}: every section break needs a title.")
    limit = len(breaks) if breaks else len(item.get("sections", [])) or 1
    for figure in item.get("figures", []):
        if figure.get("placeId") not in place_ids:
            errors.append(f"{kind} {item.get('id')}: figure place {figure.get('placeId')!r} does not exist.")
        if not str(figure.get("caption", "")).strip():
            errors.append(f"{kind} {item.get('id')}: every figure needs a caption.")
        if not 0 <= figure.get("after", -1) < limit:
            errors.append(f"{kind} {item.get('id')}: figure 'after' must point at an existing section.")
    return errors


def audit(root):
    errors = []
    research = root / "research"
    with (research / "corpus.csv").open(encoding="utf-8-sig", newline="") as stream:
        roles = {row["id"]: row.get("source_role", "") for row in csv.DictReader(stream)}
    evidence_ids = set(roles)
    sources_path = root / "sources.yaml"
    if sources_path.exists():
        evidence_ids |= {item["id"] for item in read_json(sources_path).get("sources", [])}

    sights_path = root / "sights.yaml"
    if sights_path.exists():
        sights = read_json(sights_path)
        for item in sights.get("items", []):
            fi = item.get("featureImage")
            if fi is not None:
                for field in ("url", "pageUrl", "status", "checkedAt"):
                    if not str(fi.get(field, "")).strip():
                        errors.append(f"sights.yaml {item.get('id')}: featureImage.{field} is required.")
                if not str(fi.get("url", "")).startswith("https://"):
                    errors.append(f"sights.yaml {item.get('id')}: featureImage.url must use https.")
                if not (1.33 <= float(fi.get("width", 1)) / float(fi.get("height", 1)) <= 2.2):
                    errors.append(f"sights.yaml {item.get('id')}: featureImage must be landscape between 4:3 and 2.2:1.")
            errors += score_errors(item)
        areas = sights.get("areas")
        if areas:
            owner = {}
            for area in areas:
                for region in area.get("regions", []):
                    owner.setdefault(region, []).append(area.get("id"))
            for item in sights.get("items", []):
                found = owner.get(item.get("region"), [])
                if len(found) != 1:
                    errors.append(f"sights.yaml {item.get('id')}: region {item.get('region')!r} must belong to exactly one area (has {found}).")

    sight_ids = set()
    if sights_path.exists():
        sight_ids = {item.get("id") for item in read_json(sights_path).get("items", [])}
    soak_slugs = set()
    playbooks_path = root / "playbooks.yaml"
    if playbooks_path.exists():
        for guide in read_json(playbooks_path).get("playbooks", []):
            for group in guide.get("whereToSoak", []):
                soak_slugs |= {_slug(place["name"]) for place in group.get("places", [])}

    specs = [
        ("briefings.yaml", "briefings", 1),
        ("playbooks.yaml", "playbooks", 5),
        ("routes.yaml", "routes", 3),
    ]
    all_ids = []
    for filename, collection, minimum in specs:
        path = root / filename
        if not path.exists():
            errors.append(f"Missing {filename}.")
            continue
        data = read_json(path)
        items = data.get(collection)
        if data.get("schemaVersion") != 1:
            errors.append(f"{filename}: schemaVersion must be 1.")
        if not isinstance(items, list) or len(items) < minimum:
            errors.append(f"{filename}: {collection} needs at least {minimum} item(s).")
            continue
        for item in items:
            item_id = item.get("id", "<missing-id>")
            all_ids.append(item_id)
            for field in ("id", "title"):
                if not str(item.get(field, "")).strip():
                    errors.append(f"{filename} {item_id}: {field} is required.")
            source_ids = item.get("sourceIds", [])
            if filename == "briefings.yaml":
                sections = item.get("sections", [])
                if not item.get("hook") or len(sections) < 3:
                    errors.append(f"{filename} {item_id}: hook and at least 3 sections required.")
                source_ids = source_ids + [sid for section in sections for sid in section.get("sourceIds", [])]
            if not source_ids:
                errors.append(f"{filename} {item_id}: sourceIds are required.")
            unknown = set(source_ids) - evidence_ids
            if unknown:
                errors.append(f"{filename} {item_id}: unknown source IDs {sorted(unknown)}.")
            if filename == "playbooks.yaml":
                errors += [f"{filename} {item_id}: depth: {e}" for e in playbook_depth(item, roles)]
            if filename == "routes.yaml":
                errors += [f"{filename} {item_id}: depth: {e}" for e in route_depth(item, roles)]
                errors += route_place_errors(item, sight_ids, soak_slugs)
            if filename in ("playbooks.yaml", "briefings.yaml"):
                errors += layout_errors(item, filename, sight_ids)
    map_path = root / "map.yaml"
    if map_path.exists():
        errors += map_audit(read_json(map_path), evidence_ids)
    vocabulary_path = root / "vocabulary.yaml"
    if vocabulary_path.exists():
        errors += vocabulary_audit(read_json(vocabulary_path), evidence_ids)
    basics_path = root / "basics.yaml"
    if basics_path.exists():
        manifest_path = root / "media-manifest.json"
        media_items = read_json(manifest_path).get("items", {}) if manifest_path.exists() else {}
        errors += basics_audit(read_json(basics_path), evidence_ids, root.parent.parent / "local-site", media_items)
    if len(all_ids) != len(set(all_ids)):
        errors.append("Reader-content IDs must be unique across briefing, playbook and route files.")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("country_dir", type=Path)
    args = parser.parse_args()
    try:
        errors = audit(args.country_dir)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print("FAIL: malformed or missing guide source:", exc, file=sys.stderr)
        return 1
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    if errors:
        return 1
    print("PASS: research-backed guide structure and evidence references.")
    print("Structural gate only; editorial, traveler, destination and release reviews remain required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
