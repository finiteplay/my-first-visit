---
name: verify-country-pack
description: Audit a First Day Away country research dossier and reader-facing content for evidence quality, useful anecdotes, audience fit, engagement, optional-practice boundaries and traveler decision support. Use before calling a country or major topic draft complete.
---

# Verifying a country pack

Read `docs/EDITORIAL.md` and
[references/quality-rubric.md](references/quality-rubric.md). Verification produces evidence;
it is not a request to merely reread the prose and declare it good.

## 1. Run deterministic gates

For a full research dossier:

```bash
python tools/content/audit_research.py content/<cc>/research --strict
```

During an explicitly incomplete research pass, omit `--strict`, report every warning and keep
the dossier status `draft`.

When canonical country sources were edited, also run their format/preview gate. Iceland uses:

```bash
python tools/content/validate.py --pack content/is --preview
```

Do not describe either result as release approval.

## 2. Perform three distinct reviews

**Evidence review:** Pick every material or sensitive claim and trace it to the right source
role. Check dates, trip context, independence, contradiction handling and quantifier strength.
Confirm that anecdotes remain anecdotes rather than implied incident rates.
Audit the travel-mode inventory: confirm modes were discovered from destination evidence rather
than copied from another pack, materially different modes were not collapsed, and exclusions
have an evidence-backed reason.

**Editorial review:** Score every core section with the rubric. Check whether the opening earns
attention, the advice reflects the target traveler, opinion is labeled, changing facts have a
handoff, and prose is original. Remove compulsory or trivial questions; optional practice is
reviewed separately.

**Presentation review:** Open the compiled HTML in a normal browser and in the Android WebView
at phone width, large text and both themes. Check heading order, reading flow, image purpose,
alternative text, captions, credits, link behavior, layout stability and the useful no-image
fallback. For attraction photos, confirm the following for each one:

- It is a landscape image with an aspect ratio of at least 4:3.
- It comes from an approved source.
- Its file page shows a commercial-use-with-attribution license, with no NC or ND terms.
- The content author selected it, and the manifest records that choice.
- The attraction stays fully visible on every card, carousel and popup size.

Confirm that the article remains understandable with JavaScript unavailable and that
no remote resource is requested.

**Traveler-task review:** Give a reviewer only the content and a realistic decision prompt,
not the intended answer. Examples: choose whether to rent a car; prepare questions about rental
coverage; plan a no-car arrival day; choose between a public pool and a premium lagoon. Record
whether the reviewer can identify options, trade-offs, preparation steps, uncertainty and a
next action within 90 seconds.

Run at least one traveler task for every primary travel mode. A mode name or filter is not
coverage: the reviewer must find mode-specific fit, advantages, frictions and preparation.

Use a fresh reviewer or fresh-context pass when available and authorized. The content author
must still inspect the raw results and make the revisions.

## 3. Record failures like test failures

Create or update `content/<cc>/research/REVIEW.md` from `content/REVIEW_TEMPLATE.md`. For every
failure record:

- criterion and severity;
- exact content or evidence affected;
- observed failure, not a vague preference;
- whether the fix needs research, synthesis, writing, native review or product work;
- rerun evidence.

Do not lower a gate to make a draft pass. A missing perspective becomes an explicit research
task; an unresolved claim stays labeled or is removed.

## 4. Stop condition

A research-backed draft is complete only when deterministic strict checks pass, no critical
rubric item fails, every core topic meets the rubric threshold, and all planned traveler tasks
pass. Publication additionally requires the existing native, destination, safety, rights,
media, accessibility and application gates.
