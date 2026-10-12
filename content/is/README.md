# Iceland country pack

The first research-backed country example for **First Day Away**.
Status: **research-backed editorial draft, not publishable**. The destination briefing,
playbooks and routes now lead the package; the earlier language toolkit remains supporting
material. Open [PREVIEW.md](PREVIEW.md) for the legacy language/media review copy and read the
new canonical guide sources directly until the production renderer supports them.

The research dossier passes its deterministic strict gate. That proves evidence shape and
minimum breadth—not source truth, traveler representativeness, native review, safety approval,
media rights or release readiness.

The canonical content is in the CSV/YAML files; PREVIEW.md is generated. The .yaml files
currently use the JSON subset of YAML, so the authoring validator needs only Python's
standard library. Preserve this subset until the production YAML parser is implemented.

## Files

- `pack.yaml`: identity, replacement slots, review state, legacy optional-practice topic groups
  and a seven-card optional-practice example.
- `briefings.yaml`: the first-day destination orientation.
- `playbooks.yaml`: decision support for driving, rental coverage, pools, aurora, clothing,
  spending and Reykjavík.
- `routes.yaml`: realistic short, no-car, South Coast and Ring Road shapes.
- `phrases.csv`: all 50 slots, including usage and approximate US respellings.
- `completions.yaml`: complete questions and orders plus six separate allergy cards.
- `primer.yaml`: reading rules and sign words.
- `tips.yaml`: short customs/safety cards. The current cards include three-choice exercises
  from the earlier model; future briefings must not force them on the reader.
- `sights.yaml`: regional destination cards, draft map pins and photo assignments.
- `scenarios.yaml`: local lines with response choices and explanations.
- `sources.yaml`: source scopes and review limits; checked on 2026-10-09.
- `media.yaml`, [RECORDING_BRIEF.md](RECORDING_BRIEF.md): exact recording script and photo
  inventory. Assets have not been acquired.
- `CREDITS.csv`: acquired media only; currently header-only.
- `research/corpus.csv`: recent traveler accounts plus official and provider checks.
- `research/dossier.yaml`: topic synthesis, contrasting anecdotes, limitations and live checks.
- `research/REVIEW.md`: deterministic, editorial and traveler-task results plus remaining gates.

## Review this example

Language claims are not native-approved. In particular, have a reviewer check the requests
using takk, declined noun forms, gender-neutral lost phrase, counting forms, formal/casual
choices, the allergy categories, and every respelling. Do not teach a template as permission
to concatenate arbitrary nouns. Personal names and hotel addresses stay user supplied.

The response lines and usage advice are original drafts informed by the sources, not
quotations from a source or claims that the university endorses them. Lexical entries,
natural pronunciation, allergies and scenario usage still need direct review. Native audio,
licensed photos, entrance-pin checks and timed traveler testing are also outstanding.

## Local authoring checks

From the app root:

```text
python tools/content/validate.py
python tools/content/validate.py --preview
python tools/content/validate.py --release
python tools/content/audit_research.py content/is/research --strict
python tools/content/audit_guide.py content/is
```

The first checks the legacy text structure, counts, limits, IDs, links, optional-practice
coverage and media inventory.
The second regenerates PREVIEW.md from the canonical sources. The third is expected to fail
until review and media are complete; it is a preliminary publication-readiness guard,
  not the planned Kotlin `verifyPacks` compiler. It does not measure loudness, image dimensions,
  practice-session duration or compiled archive size.

## Pattern status

See the shared [country authoring guide](../README.md) and
[editorial standard](../../docs/EDITORIAL.md). Iceland now demonstrates the research dossier,
decision synthesis, briefing, playbook, route and review-report layers as well as the older
language/media conventions. A new country begins with traveler questions, not these Icelandic
topics or a fixed slot inventory.

Keep the 50 stable phrase slots as a compatible language toolkit and justify local
replacements. Write complete useful interactions, retain native review and media provenance,
and expose exercises only through optional practice. The current validator is Iceland-specific;
adapt its script and romanization assumptions, but do not mistake it for the research-quality
gate.

## Practical editorial decisions

- Use everyday hæ as the first greeting; keep góðan daginn for daytime service encounters.
- Treat please as a request pattern; keep water, coffee and beer as complete example orders.
- Keep peanut and tree-nut cards separate. The gluten allergy card is not a celiac card.
- Avoid gendered lost adjectives by expressing that the traveler cannot find their way.
- Include cultural interactions, a museum and a harbor landmark alongside landscape sights.
- Do not freeze current beach access, volcanic alerts, timetables or road status into a pack.
- Do not include unverified horses/ponies etiquette as a scored faux pas.
- Treat the current sights as ingredients. The new routes demonstrate realistic trip shapes;
  place-level route ordering still needs map-pin and timed field review.
- The research-backed playbooks cover insurance, wind, gravel, cost, pools, aurora, clothing,
  Reykjavík and itinerary trade-offs. Parking and connectivity remain supporting observations,
  not mature core playbooks.
