#!/usr/bin/env python3
"""Validate the text draft. Media measurements and compilation are separate future gates."""
import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOUND = re.compile(r"(?:eye|ah|aw|ay|ee|eh|ai|ih|oh|oo|ow|oy|uh|ur|uu|a|[bcdfghklmnpqrstvwxyz])+", re.I)


def load(pack_dir):
    data = {n: json.loads((pack_dir / (n + ".yaml")).read_text(encoding="utf-8-sig"))
            for n in ["pack", "completions", "primer", "tips", "sights", "scenarios", "sources", "media"]}
    with (pack_dir / "phrases.csv").open(encoding="utf-8-sig", newline="") as stream:
        data["phrases"] = list(csv.DictReader(stream))
    return data


def validate(data, pack_dir, release):
    errors = []
    def check(ok, message):
        if not ok:
            errors.append(message)
    phrases, pack, primer, media = (data[k] for k in ["phrases", "pack", "primer", "media"])
    check(len(phrases) == 50 and sorted(int(p["slot"]) for p in phrases) == list(range(1, 51)),
          "Require exactly 50 unique slots, 1–50.")
    for p in phrases:
        slot = int(p["slot"])
        check(p["id"] == f"p{slot:02d}", "ID/slot mismatch: " + p["id"])
        check(len(p["when"]) <= 90, p["id"] + ": when exceeds 90 characters.")
        check(p["formality"] in {"neutral", "polite", "casual"}, p["id"] + ": invalid formality.")
        check(not p["romanization"], p["id"] + ": no romanization needed for Icelandic.")
        category = ("courtesy" if slot <= 14 else "getting-around" if slot <= 23 else
                    "food-and-drink" if slot <= 33 else "money-and-numbers" if slot <= 45 else "help")
        check(p["category"] == category, p["id"] + ": wrong category.")
    sets = [phrases, data["completions"]["items"], primer["rules"], primer["signs"],
            data["tips"]["items"], data["sights"]["items"], data["scenarios"]["items"]]
    items = [x for group in sets for x in group]
    ids = [x["id"] for x in items]
    check(len(ids) == len(set(ids)), "Duplicate stable item IDs.")
    by_id = {x["id"]: x for x in items}
    source_ids = {s["id"] for s in data["sources"]["sources"]}
    check(len(source_ids) == len(data["sources"]["sources"]), "Duplicate source ID.")
    for source in data["sources"]["sources"]:
        check(source["url"].startswith("https://") and source["scope"] and source["accessed"],
              source["id"] + ": incomplete source evidence.")
    for name, sequence, lo, hi in [
        ("primer rules", primer["rules"], 6, 12), ("signs", primer["signs"], 6, 12),
        ("tips", data["tips"]["items"], 12, 20), ("sights", data["sights"]["items"], 10, 15),
        ("scenarios", data["scenarios"]["items"], 8, 15)
    ]:
        check(lo <= len(sequence) <= hi, f"{name}: require {lo}–{hi} items.")
    for x in items:
        for field, maximum in {"title": 40, "body": 280, "why": 200, "whyGo": 120, "tip": 200}.items():
            if field in x:
                check(len(x[field]) <= maximum, f"{x['id']}: {field} exceeds {maximum}.")
        spoken = x.get("example", x)
        if "local" in spoken:
            check(spoken.get("local") and spoken.get("respelling") and
                  (spoken.get("meaning") or spoken.get("name")),
                  x["id"] + ": missing language fields.")
            spelling = spoken["respelling"].replace(x.get("personalName") or "\0", "")
            for syllable in re.split(r"[\s\-…]+", spelling):
                if syllable:
                    check(bool(SOUND.fullmatch(syllable)), x["id"] + ": invalid respelling " + syllable)
        if "linkedItem" in x:
            check(x["linkedItem"] in by_id, x["id"] + ": missing linked item.")
        for source in x.get("sourceIds", []):
            check(source in source_ids, x["id"] + ": unknown source.")
        q = x.get("question", x if "options" in x else None)
        if q:
            options = [o["id"] for o in q["options"]]
            check(len(options) == 3 and len(set(options)) == 3 and q["answerId"] in options,
                  x["id"] + ": invalid quiz choices/answer.")
            check(bool(q["feedback"]), x["id"] + ": feedback required.")
    check(any(t["category"] == "Phrases in context" for t in data["tips"]["items"]),
          "Phrases-in-context tip required.")
    completions = data["completions"]["items"]
    check({c["id"].removeprefix("allergy-") for c in completions if c["id"].startswith("allergy-")}
          == {"peanuts", "tree-nuts", "shellfish", "gluten", "milk", "eggs"},
          "Six separate allergy categories required.")
    for c in completions:
        check(c["phraseId"] in {p["id"] for p in phrases}, c["id"] + ": missing phrase stem.")
    for stem in ["p14", "p15", "p29", "p30"]:
        check(any(c["phraseId"] == stem for c in completions), stem + ": complete example required.")
    replacements = pack["replacements"]
    check(len(replacements) <= 5 and len({r["slot"] for r in replacements}) == len(replacements),
          "Invalid replacement count or duplicate slot.")
    for r in replacements:
        check(1 <= r["slot"] <= 50 and bool(r["reason"]), "Replacement needs slot and reason.")
    legs = pack["plan"]["legs"]
    check([leg["id"] for leg in legs] == [f"L{i}" for i in range(10)], "Require legs L0–L9.")
    assigned, group_ids = set(), []
    for leg in legs:
        check(leg["targetMinutes"] > 0 and 2 <= len(leg["lessonGroups"]) <= 4,
              leg["id"] + ": invalid target/groups.")
        for group in leg["lessonGroups"]:
            group_ids.append(group["id"])
            assigned.update(group["items"])
            check(set(group["items"]) <= by_id.keys(), group["id"] + ": unknown items.")
    check(len(group_ids) == len(set(group_ids)), "Duplicate topic-group IDs.")
    required = set(by_id) - {c["id"] for c in completions}
    check(required <= assigned, "Missing path coverage: " + ", ".join(sorted(required - assigned)))
    for name in ["essentials", "full"]:
        check(set(pack["plan"]["plans"][name]) <= {leg["id"] for leg in legs}, "Unknown plan leg.")
    cards = pack["exampleLesson"]["cards"]
    check(5 <= len(cards) <= 8 and len({c["id"] for c in cards}) == len(cards),
          "Example requires 5–8 unique cards.")
    for card in cards:
        check(card["item"] in by_id, card["id"] + ": unknown item.")
        if "options" in card:
            check(card["answerId"] in {o["id"] for o in card["options"]}, card["id"] + ": invalid answer.")
            check(all(o["item"] in by_id for o in card["options"]), card["id"] + ": unknown option.")
    for sight in data["sights"]["items"]:
        check(sight["tier"] in {"must-see", "worth-it", "if-you-have-time"}, sight["id"] + ": invalid tier.")
        loc = sight["location"]
        check(-90 <= loc["latitude"] <= 90 and -180 <= loc["longitude"] <= 180,
              sight["id"] + ": invalid coordinates.")
    expected_audio = {p["id"] for p in phrases} | {
        c["id"] for c in completions if not c.get("personalName")
    } | {x["id"] for x in primer["rules"] + primer["signs"] +
         data["sights"]["items"] + data["scenarios"]["items"]}
    check(len(media["audio"]) == len(expected_audio) and
          {a["id"] for a in media["audio"]} == expected_audio, "Incomplete/duplicate audio inventory.")
    check(len(media["photos"]) == len(data["sights"]["items"]) and
          {p["sightId"] for p in media["photos"]} == {s["id"] for s in data["sights"]["items"]},
          "Incomplete/duplicate photo inventory.")
    paths = []
    for audio in media["audio"]:
        check(audio["takes"] == ["normal", "slow"], audio["id"] + ": two takes required.")
        item = by_id[audio["id"]]
        check(audio["local"] == item.get("example", item)["local"], audio["id"] + ": script mismatch.")
        check(audio["voice"] == ("scenario" if audio["id"].startswith("scenario-") else "main"),
              audio["id"] + ": wrong voice.")
        for take in audio["takes"]:
            path = audio["files"][take]
            check(path == f"audio/{audio['id']}_{take}.ogg", audio["id"] + ": inconsistent filename.")
            paths.append(path)
    paths += [p["sourceFile"] for p in media["photos"]]
    check(len(paths) == len(set(paths)), "Duplicate media filenames.")
    for path in paths:
        check((pack_dir / path).resolve().is_relative_to(pack_dir.resolve()), "Asset path escapes pack.")
    if release:
        check(pack["status"] == "release", "Pack remains a draft.")
        for field in ["nativeReviewedBy", "safetyReviewedBy", "allergyReviewedBy"]:
            check(bool(pack["editorial"].get(field)), "Missing approval: " + field)
        check(pack["editorial"]["mapPinsStatus"] == "verified", "Map pins are unverified.")
        for item in primer["rules"] + primer["signs"] + completions + data["scenarios"]["items"]:
            check(item.get("review") == "approved", item["id"] + ": native review pending.")
        for item in data["tips"]["items"] + data["sights"]["items"]:
            check(bool(item.get("reviewedBy")), item["id"] + ": editorial review pending.")
        check(all(a["status"] == "recorded-native" for a in media["audio"]), "Native audio incomplete.")
        check(all(p["status"] == "acquired" for p in media["photos"]), "Licensed photos incomplete.")
        with (pack_dir / "CREDITS.csv").open(encoding="utf-8-sig", newline="") as stream:
            credits = list(csv.DictReader(stream))
        by_asset = {c["asset"]: c for c in credits}
        check(len(credits) == len(by_asset), "Duplicate credits.")
        missing = []
        for path in paths:
            target = pack_dir / path
            if not target.is_file():
                missing.append(path)
                continue
            credit = by_asset.get(path)
            check(bool(credit), path + ": missing provenance.")
            if credit:
                check(all(credit.get(k) for k in ["author", "license", "source", "date", "sha256"]),
                      path + ": incomplete provenance.")
                check(credit["license"] in {"owned", "CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0"},
                      path + ": license needs review.")
                check(credit["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest(),
                      path + ": hash mismatch.")
        check(not missing, f"{len(missing)} source media files missing.")
    return errors


def table(headers, rows):
    def cell(text):
        return str(text).replace("|", r"\|").replace("\n", " ")
    return "\n".join("| " + " | ".join(map(cell, row)) + " |"
                     for row in [headers, ["---"] * len(headers), *rows])


def render(data):
    pack, primer = data["pack"], data["primer"]
    lines = ["# Iceland — First Day Away", "",
             "Status: generated preview of the supporting language/media layer.",
             "Generated from the canonical sources by tools/content/validate.py --preview.", "",
             "This preview does not render the research-backed briefing, playbooks or routes; see",
             "briefings.yaml, playbooks.yaml, routes.yaml and research/REVIEW.md. Native review,",
             "media and independent traveler-task review remain pending.", "",
             "> " + pack["welcome"], "", pack["languageNote"], "",
             "## Your first few hours", "",
             "Keep your hotel address and offline map handy. Rest before a long drive after an",
             "overnight flight. Start with a greeting and switch to English when it helps.",
             "Learn the shower and changing-room rules before a pool visit.", "",
             "Check current official conditions and closures before setting out. This pack has",
             "no live conditions, prices or opening hours.", "",
             "## The 50 useful phrases", "",
             "Respellings are approximate; native recordings and a US-reader listening test are",
             "required. Capitals show stress; function words may be unstressed in a sentence.", "",
             table(["ID", "Icelandic", "Say it approximately", "Meaning", "When"],
                   [[p[k] for k in ["id", "local", "respelling", "meaning", "when"]]
                    for p in data["phrases"]]), "",
             "## Complete examples and allergy cards", "",
             "Use complete saved lines: noun forms can change. Alex is an example; say your name",
             "normally. The gluten allergy card does not describe celiac disease. Allergy drafts",
             "need independent review before use as medical communication aids.", "",
             table(["ID", "Icelandic", "Say it approximately", "Meaning", "Note"],
                   [[c[k] for k in ["id", "local", "respelling", "meaning", "note"]]
                    for c in data["completions"]["items"]]), "",
             "## Recognize the signs", "",
             table(["Sign", "Say it approximately", "Meaning"],
                   [[s[k] for k in ["local", "respelling", "meaning"]] for s in primer["signs"]]),
             "", "## A small reading guide", "", primer["intro"], ""]
    for rule in primer["rules"]:
        ex = rule["example"]
        lines += ["### " + rule["pattern"], "", rule["soundsLike"],
                  f"Example: **{ex['local']}** — {ex['respelling']}, {ex['meaning']}.",
                  "", rule["trap"], ""]
    lines += ["## Supporting local know-how", "",
              "Read these cards directly. The questions are optional-practice examples, not gates", 
              "between information cards.", ""]
    for tip in data["tips"]["items"]:
        q = tip["question"]
        lines += ["### " + tip["title"], "", tip["body"], "", "Why: " + tip["why"],
                  "", "Optional practice: " + q["prompt"], ""]
        lines += [f"{i}. {o['text']}" for i, o in enumerate(q["options"], 1)]
        answer = next(i for i, o in enumerate(q["options"], 1) if o["id"] == q["answerId"])
        lines += ["", f"Answer: {answer}. {q['feedback']}", "",
                  "[Source](sources.yaml): " + ", ".join(tip["sourceIds"]) +
                  ". Native/resident review pending.", ""]
    lines += ["## Things to see", "",
              "Tiers are editorial choices, not ratings. This is not a one-day route around Iceland.",
              "Durations are rough on-site estimates, excluding driving, queues and tours.",
              "Map pins are draft orientation points awaiting entrance/accessibility verification.", ""]
    for s in data["sights"]["items"]:
        lines += ["### " + s["name"], "", s["local"] + " — " + s["respelling"], "",
                  " · ".join(s[k] for k in ["tier", "region", "nearestCity", "category"]), "",
                  s["whyGo"], "", f"Allow {s['timeNeeded']}. Best fit: {s['bestTime']}", "",
                  s["tip"], "", "[Source](sources.yaml): " + ", ".join(s["sourceIds"]) +
                  ". Photo and map-pin review pending.", ""]
    lines += ["## What someone may say to you", ""]
    for s in data["scenarios"]["items"]:
        lines += ["### " + s["setting"], "", f"**{s['local']}** — {s['respelling']}",
                  "", "Meaning: " + s["meaning"], ""]
        lines += [f"{i}. {o['text']}" for i, o in enumerate(s["options"], 1)]
        answer = next(i for i, o in enumerate(s["options"], 1) if o["id"] == s["answerId"])
        lines += ["", f"Answer: {answer}. {s['feedback']}", ""]
    lesson = pack["exampleLesson"]
    lines += ["## Optional practice sample: " + lesson["title"], "",
              "Quiet mode works without forced audio or speech.", "",
              table(["Card", "Type", "Item", "Prompt"],
                    [[c["id"], c["type"], c["item"], c.get("prompt", "Learn the phrase and its usage.")]
                     for c in lesson["cards"]]), "", lesson["note"], "",
              "## Legacy optional-practice grouping", "",
              "Earlier topic groups for a possible practice generator; not the primary guide,",
              "not required, and not measured practice-session durations.", "",
              table(["Group", "Topic", "Design target", "Contents"],
                    [[leg["id"], leg["title"], str(leg["targetMinutes"]) + " min",
                      "; ".join(g["title"] for g in leg["lessonGroups"])]
                     for leg in pack["plan"]["legs"]]), "",
              "## Editorial sources", "",
              "Sources support the stated scopes. They do not certify our original translations,",
              "respellings or practice items; individual dictionary lookups remain pending.", "",
              table(["ID", "Source", "Scope"],
                    [[s["id"], f"[{s['title']}]({s['url']})", s["scope"]]
                     for s in data["sources"]["sources"]]), ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=ROOT / "content" / "is")
    parser.add_argument("--release", action="store_true", help="Require reviews and source media.")
    parser.add_argument("--preview", action="store_true", help="Regenerate the Markdown review copy.")
    args = parser.parse_args()
    try:
        data = load(args.pack)
        errors = validate(data, args.pack, args.release)
        if errors:
            for error in errors:
                print("FAIL:", error, file=sys.stderr)
            return 1
        if args.preview:
            (args.pack / "PREVIEW.md").write_text(render(data), encoding="utf-8", newline="\n")
            print("Regenerated PREVIEW.md.")
        print(f"PASS: {len(data['phrases'])} phrases; "
              f"{len(data['completions']['items'])} completions; "
              f"{len(data['primer']['rules'])} primer rules; {len(data['primer']['signs'])} signs; "
              f"{len(data['tips']['items'])} tips; {len(data['sights']['items'])} sights; "
              f"{len(data['scenarios']['items'])} scenarios.")
        print("Legacy language/media checks only; research and guide audits are separate, and native review, media measurements and pack compilation are not evaluated here.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        print("FAIL: malformed/missing source:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
