---
name: add-places
description: Add new places (sights, lagoons, museums, experiences) to a MyFirstVisit country pack end to end — research, place entry, area and category, pin and parking, pronunciation, photos with the author in the loop, our own rating and ranking, links, and the checks. Use when a user asks to add, replace or remove places, or to bring a new country's place list to the Iceland standard.
---

# Adding places to a country pack

This is the procedure. `AGENTS.md` (rules) and `docs/CONTENT.md` (field contract) win where this file drifts.
Every step says what is automated (a tool you run) and where a human decides (stop and wait).

## 0. Decide what belongs

- A place earns a card because it supports an experience, a route or a decision. No quota.
- Never add restaurants, cafés, hotels, guesthouses or shops as places, and do not name them in routes.
- Do not add a village or town that has nothing to see in itself. Add the sight next to it instead
  (Iceland: Reynisfjara rather than Vík). A town can appear as a route base without a card.
- When a user shares a trip document or list, extract every sight and every itinerary stop, then reconcile:
  a stop that is a sight gets a card and appears in the trip's `placeIds`; leave out food, lodging and driving times.
  Report what you skipped and why, so nothing silently disappears.
- Check for duplicates by local name and by coordinates (within ~300 m) before adding.

## 1. Place entry (`content/<cc>/sights.yaml`)

Fill every field the contract in `docs/CONTENT.md` names: `id` (`sight-<slug>`), `name` (English display name),
`local`, `respelling`, `region`, `nearestCity`, `category`, `tier`, `whyGo`, `description` (2–3 short paragraphs:
what it is, why a first-time visitor goes, what to know), `timeNeeded`, `bestTime`, `tip`, `location`, `website`,
`sourceIds`.

- **Region and area:** `region` must belong to exactly one `areas` entry (the filters travelers think in). If a
  new region appears, add it to an area; `audit_guide.py` fails otherwise.
- **Category:** reuse the existing categories; the filter buttons build themselves from the data.
- **Tier (priority for a first visit):** `must-see`, `worth-it`, `if-you-have-time`. Propose; the author confirms in
  the rating editor (step 6). Labels are words with icons, never stars.
- **Description:** paraphrase traveler and official sources; never copy. Do not cite a review site's ranking or
  rating in prose ("Tripadvisor ranks it #3" is forbidden); say "travelers rate it highly" if supported.
- **Website:** the operator's own site, else the managing authority or regional tourism board. Never a booking
  marketplace or a review site. Check HTTP 200 and that the page is the right place. Lagoons and similar listed
  inside a guide (`whereToSoak`) get links only in the guide entry, not on the overview cards.

## 2. Pin, parking and maps (automated, then reviewed)

- `location`: the sight itself, from OpenStreetMap geocoding, `status: draft-pin…` until someone checks it.
- **Parking:** for walk-in nature sights (category in `WALK_IN`) run
  `python tools/content/find_parking.py <cc>` (dry run), read the report, then `--apply`. It writes `parking`
  from OpenStreetMap (ODbL, storable) and the place page's Google Maps link opens the lot. Sanity rules: a lot
  80 m–2.5 km away; a lot named after the place beats a nearer unnamed one; watch for the wrong bank or side of a
  river (Dettifoss east vs west). Correct or skip with `content/<cc>/parking-overrides.json` (`null` skips).
- Never store coordinates or other data from Google Places (its terms forbid keeping them). Google Maps *links*
  (`/maps/search/?api=1&query=lat,lon`) are fine.
- **Minimap:** places within a `map.yaml` region radius (or `forRegions`) use the local map; others the country
  outline. A new main-city or inland region map is built with `tools/maps/build_region_*.py`.

## 3. Pronunciation (automated draft, human review)

- Only when the local name is in the local language. A place whose own name is English or a brand
  (Sky Lagoon, FlyOver Iceland) gets `"pronounce": false`: no transcription, no play button.
- Respelling uses only the key in `docs/CONTENT.md`. Generate draft audio with
  `tools/audio/generate_place_audio.py`, then `python tools/media/media_store.py ingest <cc>`.
- Synthetic audio is draft; keep the voice's license credit (footer) whenever any synthetic clip ships.

## 4. Photos (author in the loop — never pick for the author)

1. `python tools/media/shortlist_photos.py <cc> --only <id>` builds `content/<cc>/media-candidates/review.html`
   (10–20 verified landscape candidates per place from Wikimedia Commons and Flickr, attribution licenses only,
   a table of contents with selected counts). Add a single Flickr find with `tools/media/add_candidate.py`;
   `tools/media/find_public_domain.py` lists public-domain/CC0-only files for hard cases.
2. **Stop.** The author selects 3–5 per place in the page and saves `selection.json` (same file each time).
3. `python tools/media/apply_selection.py <cc>` downloads and records full attribution; then
   `python tools/media/media_store.py ingest <cc>` (1440 px sRGB WebP + 640 px card, metadata stripped) and
   `sync-local <cc>` for the preview. Bytes never go into git.
4. The author's own trip photos: `python tools/media/sort_personal_photos.py sort <folder> <scratch> --pack <cc>` copies
   them into one folder per place by EXIF GPS (originals untouched), and `portraits <scratch> --apply` sets aside
   portraits of specific people with local face models (close-ups, and recurring travel companions), into `!deleted/`
   with a review page. Measure first without `--apply`, look at `people.jpg` and sample sheets, then apply. After moving
   photos by hand run `refresh`. `python tools/media/add_personal_candidates.py <cc> <scratch>` then adds the kept landscape
   photos to the selection page as `<sight>-pNNN` candidates beside the Commons and Flickr ones (ids are stable; paths
   stay out of the repo); the author picks as usual and `apply_selection.py` resizes the chosen own photos (credit "Own work").
5. No cleared photo yet: a hotlinked `featureImage` from the place's own website may stand in (landscape 4:3–2.2:1,
   shows the place, labeled "not licensed for reuse"); otherwise an honest pending slot. Never a generic image.
6. Advice guides need their own card image each; the article hero uses the same image as the main-page card.

## 5. Data from other sites (ratings) — private inputs only

- Raw ratings, review counts and ranks from review or map sites live only in
  `~/.finiteplay/score-inputs/<cc>.json` (outside the repo). Their terms forbid republishing them, and the repo is
  public. Read a source's terms before collecting from it; script collection from sites that ban it is a risk the
  author must accept explicitly.
- Google: `python tools/content/fetch_google_ratings.py <cc>` (key in `~/.finiteplay/secrets/google-places.key`,
  Places API (New) enabled). It skips businesses that are not the place and checks distance; read its review list
  and drop wrong matches (a restaurant matched instead of a harbour).
- Never publish another site's rating, review count, rank, logo, or a deep link to its listing. The audit fails on
  `tripadvisor`, `google`, `reviews` or `rating` fields in content.

## 6. Our rating and ranking (author decides)

1. `python tools/content/edit_ratings.py <cc> --open` — one list for all places: drag to rank, edit aggregate stars
   (placeholders start from the average of sources), set priority with the radio buttons, "Save to <cc>.json".
2. **Stop** until the author saves. New places land at the end of the list until ranked.
3. `python tools/content/build_score.py <cc>` writes `score {stars, rank, method, asOf}` and `tier`. Use
   `--use-suggestions` only for a first fill; it re-sorts and would overwrite a hand-made order.

## 7. Links on the place page (generated, nothing to store)

Google Maps (parking or pin), the official website, "Weather here" (yr.no forecast and Windy map from the
coordinates), and the official warnings / roads / safety strip. All are built from fields; no per-place URLs
to maintain.

## 8. Wire it in

- Trips: add the place id to the right day's `placeIds` (order of visit); the stop map draws itself.
- Guides: `placeGroups` lists places by id; do not hand-copy names or links.

## 9. Checks (all must pass before you say done)

```bash
python local-site/build.py
python tools/content/audit_guide.py content/<cc>
python tools/content/audit_research.py content/<cc>/research --strict
cd tools/content && python -m unittest test_audit_guide test_audit_research
~/.finiteplay/venv/Scripts/python tools/qa/check_site.py --out <scratch>/shots   # server on :4173
```

Then follow `.agents/skills/qa-site/SKILL.md` for the visual pass (open the new place cards at 1440, 800 and 390 px)
and `.agents/skills/publish-site/SKILL.md` to ship.

## 10. Report to the author

List what was added, what was skipped and why, every wrong match you removed, placeholders still in use, and
each decision waiting for them (photo picks, ranking, tier, parking overrides).
