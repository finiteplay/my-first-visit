---
name: author-country-pack
description: Research and write an experience-led MyFirstVisit country pack from recent traveler accounts, travel media, official sources and an explicit audience lens. Use for new destination briefings, playbooks, routes, or substantial country-content revisions; do not use for a small copyedit or translation-only change.
---

# Authoring a country pack

Read `docs/EDITORIAL.md` first. It is the editorial contract. Read `docs/CONTENT.md` and the
target country README for the current source format, but do not let their older language-first
shape turn quizzes into the primary product.

## Establish the assignment

Write down the destination, audience origin, season coverage, trip modes, scope and `as of`
date. State whether this is a full-country dossier, a focused topic expansion, or a revision.
Do not silently treat one travel style—especially self-driving—as universal.

Before declaring the trip modes, run the travel-mode discovery pass in the research method.
Record the resulting primary, supporting and excluded modes in the dossier. Separate modes
that change the traveler's lodging, route, chores, booking, safety, cost, accessibility or
legal obligations; do not collapse campervans into rental cars or rail passes into generic
public transport when those differences create consequential decisions.

For a new or substantially revised destination, read
[references/research-method.md](references/research-method.md) and build the research dossier
before writing polished briefing prose. For a focused revision, update the affected dossier
topics and rerun their gates.

## Work from traveler questions

Discover questions through recent trip reports, forum discussions and traveler media. Give
priority to decisions travelers must otherwise make while tired, under time pressure, or at a
counter: transport, insurance, reservations, money, connectivity, clothing, timing, access,
etiquette and realistic itineraries.

Research vivid positive experiences as deliberately as problems. A useful pack helps the user
choose what to repeat, not merely avoid mistakes.

Treat shows, blogs and guidebooks as topic-discovery and engagement sources. When a fact appears
across several of them, investigate the fact; do not copy their wording, narrative sequence,
signature comparisons, images, video or graphics.

## Synthesize before writing

For each topic, record:

- the user decision or desired experience;
- recurring traveler observations and meaningful counterexamples;
- two or more decision-useful anecdotes when the evidence supports them;
- contextual differences that may explain the outcomes;
- official guidance or provider terms required by the topic;
- what is stable offline and what must be checked live;
- the evidence limitation and the editorial take for this audience.

For each included travel mode, also record who it suits, why travelers choose it, ordinary
frictions, seasonality, authoritative checks and where the reader receives useful guidance.

When season changes the experience materially, create a season-fit synthesis. Define `best`,
`bad` and `worst` against a named traveler goal instead of declaring a universal month. Cover
access, daylight, demand, signature experiences and disruption risk, then translate the result
into concrete clothing changes by season on top of the destination's all-season baseline.

For consequential clothing or equipment, research whether travelers should bring, rent or buy
locally. Explain the value, logistics and expected reuse of each path. Verify rental inventory
with a current provider, distinguish local design from local manufacture when authenticity
matters, and avoid claiming that every destination-branded product shares one quality level.

Forum counts establish recurrence in the corpus, not real-world incidence. Never invent a
missing anecdote, outcome, consensus or statistic.

## Write the reader experience

Use scenes, consequences, choices and short checklists. Make the result enjoyable to consume,
but ensure each section makes a decision easier or an experience more vivid. Label disagreement
and opinion naturally. `Choose for yourself` must follow useful considerations, not substitute
for them.

Author new or migrated briefing, playbook and route prose as semantic HTML under
`content/<cc>/articles/`, following the allowlist and evidence/media references in
`docs/CONTENT.md`. Review it in a browser as well as source form. Keep research synthesis,
rights metadata and pack metadata in their sidecar files; do not turn HTML into an unstructured
substitute for those records.

## Attraction photos (author in the loop)

Follow the image rules in `AGENTS.md`. For each attraction:

1. Search the approved sources only: Wikimedia Commons and Flickr.
2. Keep only landscape files with an aspect ratio of at least 4:3 that show the exact place.
   Each file's own page must state a commercial-use-with-attribution license: CC0, public
   domain, CC BY or CC BY-SA. Reject NC, ND, all-rights-reserved and unclear licenses.
3. Preview each candidate's render at every card size (list card, carousel, popup) and drop
   any that cannot be framed without hiding the attraction.
4. Present 10–20 verified candidates to the content author, with a thumbnail, source link,
   author, license and dimensions for each. Stop and wait for the author's choice.
5. Record the author's 3–5 picks in the media manifest, with full attribution, the license
   URL, the download date and a per-image `object-position` or `contain` setting. Never fill
   a shortfall with an unrelated or stock image. One or two author picks make a `partial`
   gallery; list it for a later round with more sources, and keep earlier picks.

Connect language to situations. Courtesy phrases, signs, local replies and Show a local cards
belong beside the experiences where they help. Put recall exercises in optional practice;
do not interrupt the briefing with mandatory or trivial quizzes.

## Meet the completeness standard

Before calling a playbook or route drafted, compare it with the completeness standard in
`docs/CONTENT.md`. Its models are the Iceland playbooks `pack-for-exposure` and
`rental-counter-before-counter`: explain why the destination is different, name concrete
things the reader can act on, offer a structured choice, give contrasting traveler stories
when experiences vary, and move current facts into live checks. A card that passes the script
but reads thinner than the models is still a draft. Routes need a day-by-day plan with where
you sleep, travel time, highlights, a flexible day and season notes.

## Iterate to evidence

After each coherent draft:

1. Run `python tools/content/audit_research.py <country>/research --strict` for a full dossier,
   or without `--strict` while research is still explicitly draft.
2. Follow `.agents/skills/verify-country-pack/SKILL.md` for evidence, editorial and traveler-task
   review.
3. Turn each failed criterion into a concrete research, synthesis or writing change.
4. Repeat until the intended gate passes; preserve unresolved findings instead of smoothing
   them out in prose.

The existing Iceland `validate.py --preview` gate is additional when its canonical files are
edited. It does not replace the research and editorial gates.
