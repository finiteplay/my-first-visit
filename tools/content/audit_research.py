#!/usr/bin/env python3
"""Audit a First Day Away traveler-research dossier.

This deterministic gate checks evidence shape and minimum support. It cannot judge whether a
source is truthful, prose is engaging, or the researched corpus represents all travelers.
"""
import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

CORPUS_FIELDS = [
    "id", "url", "platform", "source_role", "published_at", "trip_date",
    "traveler_origin", "trip_style", "season", "firsthand", "topics", "notes",
]
SOURCE_ROLES = {"traveler", "editorial", "official", "provider", "reviewer"}
IMPORTANCE = {"core", "supporting"}
SIGNALS = {"repeated", "split", "emerging", "single-anecdote"}
SENSITIVE = {"safety", "health", "legal", "emergency", "insurance"}
VERIFYING_ROLES = {"official", "provider", "reviewer"}
MODE_STATUSES = {"primary", "supporting", "excluded"}


def parse_day(value, field, errors):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        errors.append(f"{field}: require YYYY-MM-DD, got {value!r}.")
        return None


def month_floor(day, months):
    year = day.year
    month = day.month - months
    while month <= 0:
        year -= 1
        month += 12
    return date(year, month, 1)


def load(root):
    with (root / "corpus.csv").open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        corpus = list(reader)
    dossier = json.loads((root / "dossier.yaml").read_text(encoding="utf-8-sig"))
    return fields, corpus, dossier


def audit(root, strict=False):
    errors = []
    warnings = []

    def check(ok, message):
        if not ok:
            errors.append(message)

    fields, corpus, dossier = load(root)
    check(fields == CORPUS_FIELDS,
          "corpus.csv columns must exactly match the documented schema and order.")
    check(dossier.get("schemaVersion") == 1, "dossier.yaml schemaVersion must be 1.")
    check(bool(dossier.get("country")), "Dossier country is required.")
    check(bool(dossier.get("audience")), "Dossier audience lens is required.")
    as_of = parse_day(dossier.get("asOf"), "dossier asOf", errors)
    window = dossier.get("researchWindowMonths")
    check(isinstance(window, int) and 1 <= window <= 60,
          "researchWindowMonths must be an integer from 1 to 60.")
    check(dossier.get("status") in {"draft", "review-ready"},
          "Dossier status must be draft or review-ready.")
    if strict:
        check(dossier.get("status") == "review-ready",
              "Strict audit requires status review-ready.")

    ids = [row.get("id", "") for row in corpus]
    check(all(ids), "Every corpus row needs an id.")
    check(len(ids) == len(set(ids)), "Corpus source IDs must be unique.")
    by_id = {row.get("id"): row for row in corpus if row.get("id")}

    for row in corpus:
        sid = row.get("id") or "<missing-id>"
        check(row.get("url", "").startswith("https://"), f"{sid}: URL must use HTTPS.")
        check(bool(row.get("platform")), f"{sid}: platform is required.")
        check(row.get("source_role") in SOURCE_ROLES, f"{sid}: invalid source_role.")
        parse_day(row.get("published_at"), f"{sid} published_at", errors)
        trip_date = row.get("trip_date", "")
        check(trip_date == "unknown" or (
            len(trip_date) in {4, 7, 10} and
            all(part.isdigit() for part in trip_date.split("-"))
        ), f"{sid}: trip_date must be YYYY, YYYY-MM, YYYY-MM-DD or unknown.")
        for name in ["traveler_origin", "trip_style", "season", "topics", "notes"]:
            check(bool(row.get(name, "").strip()), f"{sid}: {name} is required.")
        check(row.get("firsthand") in {"true", "false"},
              f"{sid}: firsthand must be true or false.")
        if row.get("source_role") != "traveler":
            check(row.get("firsthand") == "false",
                  f"{sid}: only traveler accounts may be counted as firsthand.")

    travel_modes = dossier.get("travelModes")
    check(isinstance(travel_modes, list) and travel_modes,
          "At least one evidence-backed travel mode is required.")
    mode_ids = [m.get("id") for m in travel_modes if isinstance(m, dict)] \
        if isinstance(travel_modes, list) else []
    check(len(mode_ids) == len(set(mode_ids)) and all(mode_ids),
          "Travel mode IDs must be present and unique.")
    for mode in travel_modes or []:
        if not isinstance(mode, dict):
            errors.append("Every travel mode must be an object.")
            continue
        mid = mode.get("id") or "<missing-mode-id>"
        status = mode.get("status")
        check(status in MODE_STATUSES, f"{mid}: invalid travel mode status.")
        source_ids = mode.get("sourceIds")
        check(isinstance(source_ids, list) and source_ids,
              f"{mid}: travel mode sourceIds must be non-empty.")
        if isinstance(source_ids, list):
            check(set(source_ids) <= by_id.keys(), f"{mid}: unknown travel mode source ID.")
        if status in {"primary", "supporting"}:
            for name in ["travelerFit", "seasonality"]:
                check(bool(str(mode.get(name, "")).strip()), f"{mid}: {name} is required.")
            for name in ["advantages", "frictions", "coverage"]:
                value = mode.get(name)
                check(isinstance(value, list) and value, f"{mid}: {name} must be non-empty.")
        if status == "excluded":
            check(bool(str(mode.get("reason", "")).strip()),
                  f"{mid}: excluded travel mode needs a reason.")

    firsthand = [r for r in corpus
                 if r.get("source_role") == "traveler" and r.get("firsthand") == "true"]
    if strict:
        check(len(firsthand) >= 30,
              f"Strict audit requires at least 30 firsthand accounts; found {len(firsthand)}.")
        platforms = Counter(r["platform"] for r in firsthand)
        check(len(platforms) >= 3,
              f"Strict audit requires at least 3 traveler communities; found {len(platforms)}.")
        if firsthand and platforms:
            dominant = platforms.most_common(1)[0]
            check(dominant[1] / len(firsthand) <= 0.60,
                  f"One traveler platform supplies more than 60% of accounts: {dominant[0]}.")
        if as_of and isinstance(window, int):
            cutoff = month_floor(as_of, window)
            dated = []
            for row in firsthand:
                try:
                    dated.append(date.fromisoformat(row["published_at"]))
                except ValueError:
                    pass
            recent = sum(day >= cutoff for day in dated)
            check(bool(dated) and recent / len(firsthand) >= 0.70,
                  "At least 70% of firsthand accounts must be inside the research window.")
        contextual = sum(
            all(r[field] != "unknown" for field in ["traveler_origin", "trip_style", "season"])
            for r in firsthand
        )
        check(bool(firsthand) and contextual / len(firsthand) >= 0.60,
              "At least 60% of firsthand accounts need origin, trip style and season context.")

    batches = dossier.get("batches")
    check(isinstance(batches, list) and batches, "At least one research batch is required.")
    if isinstance(batches, list):
        batch_ids = [b.get("id") for b in batches if isinstance(b, dict)]
        check(len(batch_ids) == len(set(batch_ids)) and all(batch_ids),
              "Research batch IDs must be present and unique.")
        for batch in batches:
            if not isinstance(batch, dict):
                errors.append("Every research batch must be an object.")
                continue
            bid = batch.get("id") or "<missing-batch-id>"
            check(bool(batch.get("scope")), f"{bid}: batch scope is required.")
            source_ids = batch.get("sourceIds")
            check(isinstance(source_ids, list) and source_ids,
                  f"{bid}: batch sourceIds must be non-empty.")
            if isinstance(source_ids, list):
                check(set(source_ids) <= by_id.keys(), f"{bid}: unknown source ID.")
            for name in ["newHighImpactTopics", "newDecisionFactors"]:
                check(isinstance(batch.get(name), list), f"{bid}: {name} must be a list.")
        if strict:
            check(len(batches) >= 3, "Strict audit requires at least 3 research batches.")
            if len(batches) >= 2:
                for batch in batches[-2:]:
                    check(not batch.get("newHighImpactTopics") and
                          not batch.get("newDecisionFactors"),
                          "The last two batches must record no new high-impact topic or decision factor.")

    topics = dossier.get("topics")
    check(isinstance(topics, list) and topics, "At least one synthesized topic is required.")
    topic_ids = [t.get("id") for t in topics if isinstance(t, dict)] if isinstance(topics, list) else []
    check(len(topic_ids) == len(set(topic_ids)) and all(topic_ids),
          "Topic IDs must be present and unique.")

    for topic in topics or []:
        if not isinstance(topic, dict):
            errors.append("Every topic must be an object.")
            continue
        tid = topic.get("id") or "<missing-topic-id>"
        check(bool(topic.get("title")), f"{tid}: title is required.")
        check(topic.get("importance") in IMPORTANCE, f"{tid}: invalid importance.")
        check(topic.get("signal") in SIGNALS, f"{tid}: invalid signal.")
        source_ids = topic.get("sourceIds")
        check(isinstance(source_ids, list) and source_ids, f"{tid}: sourceIds are required.")
        if not isinstance(source_ids, list):
            source_ids = []
        check(set(source_ids) <= by_id.keys(), f"{tid}: unknown source ID.")
        evidence = [by_id[s] for s in source_ids if s in by_id]
        travel = [r for r in evidence
                  if r.get("source_role") == "traveler" and r.get("firsthand") == "true"]
        communities = {r.get("platform") for r in travel}
        needed = 6 if topic.get("importance") == "core" else 3
        if strict:
            check(len(travel) >= needed,
                  f"{tid}: {topic.get('importance')} topic needs {needed} firsthand accounts; found {len(travel)}.")
            check(len(communities) >= 2,
                  f"{tid}: topic needs firsthand evidence from at least 2 communities.")
        if topic.get("signal") == "repeated":
            check(len(travel) >= 6 and len(communities) >= 2,
                  f"{tid}: repeated signal needs 6 firsthand accounts across 2 communities.")

        risk = topic.get("risk", [])
        check(isinstance(risk, list) and set(risk) <= SENSITIVE,
              f"{tid}: invalid risk list.")
        if set(risk) & SENSITIVE:
            check(any(r.get("source_role") in VERIFYING_ROLES for r in evidence),
                  f"{tid}: sensitive topic needs official, provider or reviewer evidence.")

        anecdotes = topic.get("anecdotes")
        check(isinstance(anecdotes, list), f"{tid}: anecdotes must be a list.")
        anecdotes = anecdotes if isinstance(anecdotes, list) else []
        if strict and topic.get("importance") == "core":
            check(len(anecdotes) >= 2, f"{tid}: core topic needs at least 2 anecdotes.")
        stances = set()
        for index, anecdote in enumerate(anecdotes, 1):
            label = f"{tid} anecdote {index}"
            check(isinstance(anecdote, dict), f"{label}: must be an object.")
            if not isinstance(anecdote, dict):
                continue
            check(anecdote.get("sourceId") in source_ids,
                  f"{label}: sourceId must belong to the topic.")
            for name in ["stance", "context", "event", "action", "outcome"]:
                check(bool(str(anecdote.get(name, "")).strip()), f"{label}: {name} is required.")
            stances.add(anecdote.get("stance"))
            quote = str(anecdote.get("quote", "")).split()
            check(len(quote) <= 25, f"{label}: quotation exceeds 25 words; paraphrase it.")
        if topic.get("signal") == "split":
            check(len(stances - {None, ""}) >= 2,
                  f"{tid}: split signal needs anecdotes from at least 2 stances.")

        synthesis = topic.get("synthesis")
        check(isinstance(synthesis, dict), f"{tid}: synthesis is required.")
        if isinstance(synthesis, dict):
            for name in ["travelerPattern", "decisionHelp", "verify", "limits"]:
                check(bool(str(synthesis.get(name, "")).strip()),
                      f"{tid}: synthesis.{name} is required.")
            if topic.get("signal") == "split":
                check(bool(str(synthesis.get("counterPattern", "")).strip()),
                      f"{tid}: split topic requires synthesis.counterPattern.")

    if not strict:
        if len(firsthand) < 30:
            warnings.append(
                f"Draft has {len(firsthand)} firsthand accounts; full strict gate starts at 30."
            )
        if dossier.get("status") != "review-ready":
            warnings.append("Dossier remains draft; strict review-ready checks were not run.")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_dir", type=Path,
                        help="Directory containing corpus.csv and dossier.yaml")
    parser.add_argument("--strict", action="store_true",
                        help="Require the full research-ready thresholds and saturation record")
    args = parser.parse_args()
    try:
        errors, warnings = audit(args.research_dir, args.strict)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print("FAIL: malformed or missing research dossier:", exc, file=sys.stderr)
        return 1
    for warning in warnings:
        print("WARN:", warning)
    for error in errors:
        print("FAIL:", error, file=sys.stderr)
    if errors:
        return 1
    mode = "strict" if args.strict else "draft"
    print(f"PASS: {mode} research dossier audit.")
    print("Structural evidence gate only; editorial and traveler-task review remain required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
