# Country content authoring

MyFirstVisit country packs are experience-led travel briefings backed by a versioned
research dossier. Language, sights and optional practice support the briefing; they do not
define its table of contents.

The [Iceland pack](is/README.md) is the first research-backed editorial example and also retains
the earlier language-first text shape. Its [preview](is/PREVIEW.md) covers phrases,
pronunciation, signs, basic tips and media planning; its dossier, briefing, playbooks, routes
and review report demonstrate [EDITORIAL.md](../docs/EDITORIAL.md).

## Build or substantially revise a country

Use `.agents/skills/author-country-pack/SKILL.md`. In summary:

1. Declare destination, audience origin, season range, scope and research date. Run a broad
   travel-mode discovery pass, then record evidence-backed primary, supporting and excluded
   modes; do not begin from a car-versus-tour template.
2. Discover the consequential questions through recent trip reports, forums, travel programs,
   blogs and guides. Research positive experiences and ordinary successful trips as well as
   mistakes, costs and surprises.
3. Build `research/corpus.csv` from independently attributable sources. Preserve publication
   and trip dates, traveler context, source role, topics, URL and a paraphrased observation.
4. Build `research/dossier.yaml`: topic signals, decision-useful anecdotes, counterexamples,
   source links, official/provider checks, limitations, live handoffs and editorial takes.
5. Research in meaningfully different batches until core topics reach corpus saturation under
   the stopping rule in `docs/EDITORIAL.md`. Source volume alone is not completion.
6. Write a short destination briefing, then practical playbooks and routes as semantic HTML
   around the decisions and experiences the research found. Use original wording, an explicit
   audience lens and figures or callouts only where they improve the reading experience.
7. Attach phrases, signs, likely replies, pronunciation and Show a local cards to the situations
   where they help. Preserve complete grammatical forms and native review requirements.
8. Add an optional practice inventory only where recall or listening practice is genuinely
   useful. Do not force quizzes between information cards or create trivial distractors.
9. Acquire authentic, licensed media after the text and shot brief are approved. Keep rights,
   credits and hashes separate from mere public visibility.
10. Run the research, content, media and traveler-task gates; revise and rerun. A structural
    pass is not editorial or release approval.

## Research dossier

The planned layout for a research-backed pack is:

```text
content/<cc>/
  research/
    corpus.csv          one independent account or authoritative source per row
    dossier.yaml        topic synthesis, anecdotes, disagreement and limitations
    REVIEW.md           copy of REVIEW_TEMPLATE.md with gate results and rerun evidence
  articles/
    start-here.html     destination orientation and audience-specific framing
    <playbook-id>.html  practical decisions and recurring situations
    <route-id>.html     realistic ways to combine experiences
  phrases.csv           stable language-toolkit slots
  completions.yaml      complete questions, orders and safety-reviewed cards
  primer.yaml           reading rules and sign words
  sights.yaml           place facts, practical fit, media and map references
  scenarios.yaml        likely local replies; optional practice may use them
  sources.yaml          authoritative/editorial source registry used by runtime content
  media.yaml            intended audio/photo inventory
  pack.yaml             identity, versions, audience lenses and feature availability
```

The research files are authoring evidence and do not need to ship in full. Compiled reader
content retains evidence labels, freshness and source links needed for trust and updates.
The existing Iceland briefing/playbook/route YAML files predate the HTML decision and remain
temporary migration inputs; do not create new country guide prose in that format.

## Source conventions

- CSV and HTML are UTF-8. The remaining `.yaml` files use JSON syntax, a valid YAML subset,
  until a general parser is introduced.
- Guide HTML uses only the element, class and attribute allowlist in `docs/CONTENT.md`. It has
  no scripts, forms, iframes, event handlers, remote resources or article-specific styling.
- Use stable `data-source-id` and `data-media-id` references. Do not paste source prose,
  licences or binary image data into an article.
- IDs remain stable when copy changes. A changed meaning or decision requires an explicit
  migration decision because saved items and optional practice may key progress by ID.
- A thread may contain several independent traveler accounts; record each account separately
  but do not count reposts or quoted stories as new evidence.
- Forum recurrence is not an incident rate. Quantifiers in reader copy must match the evidence.
- `traveler`, `editorial`, `official`, `provider` and `reviewer` sources have different roles;
  do not use one as a substitute for another.
- Publicly accessible media or prose is not automatically licensed for reuse. Paraphrase facts
  and retain the source trail; acquire media rights separately.
- Fast-changing facts carry an accessed date and a live/provider-specific handoff.
- `PREVIEW.md` is generated from source. Never treat generated Markdown as canonical.

## Quality loop

Run the deterministic research audit for a full dossier:

```text
python tools/content/audit_research.py content/<cc>/research --strict
```

Then follow `.agents/skills/verify-country-pack/SKILL.md` for evidence review, the editorial
rubric and 90-second traveler-task tests. Every failure becomes a research, synthesis, writing,
native-review or product task and is rerun after revision. Start the report from
[REVIEW_TEMPLATE.md](REVIEW_TEMPLATE.md); keep failed and superseded rounds rather than
rewriting history.

Iceland's existing language-source check remains:

```text
python tools/content/validate.py --pack content/is --preview
python tools/content/validate.py --pack content/is --release
```

The first is a legacy text-shape check; the second must fail until its named approvals and
media gates pass. Run the strict research and guide audits separately; even all three structural
passes do not replace independent editorial, traveler, destination, safety or rights review.
