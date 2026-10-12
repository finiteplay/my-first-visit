# First Day Away

An offline, experience-led briefing for an American traveler visiting a country, often for
the first time. A country pack helps the traveler make decisions before arrival, understand
what the trip will feel like, choose experiences, avoid recurring mistakes, and keep useful
language close at hand. Optional quiz-like language practice is supporting functionality,
not the primary content experience.

Publisher: FinitePlay LLC. The Android app is at design stage. Iceland has a strict-audited
traveler dossier, briefing, playbooks and routes plus the earlier language sources. Independent
traveler/destination/native reviews, media and pack compilation are pending.

Its structure, toolchain, conventions and licensing come from `../card_games`
(`docs/ARCHITECTURE.md` "Relationship to card_games" lists what is taken and how). When in doubt
about a convention not written here, follow `../card_games/AGENTS.md`.

## Specifications are authoritative

The docs are the contract; the code follows them. If implementation shows that a requirement
must change, update the spec in the same change. Never resolve a conflict silently in code.

- `docs/DESIGN.md`: product, user, primary briefing, optional practice, offline use and packs
- `docs/CONTENT.md`: semantic-HTML guide authoring, research-backed pack contents, language
  toolkit, media, source layout and build checks
- `docs/EDITORIAL.md`: traveler research, evidence labels, anecdote use, editorial voice,
  engagement and the write-review-test-repeat quality loop
- `docs/UI_SPEC.md`: screens, navigation, components, visual system, accessibility
- `docs/ARCHITECTURE.md`: native-shell/offline-WebView boundary, modules, dependency rule and
  gates, pack delivery, optional-practice engine, persistence, departures from the card games'
  platform rules

Each doc says whether it describes what is built or what is planned. Keep that true.

For research or destination-content work, read and follow
`.agents/skills/author-country-pack/SKILL.md`. Before calling a research dossier or country
draft complete, also follow `.agents/skills/verify-country-pack/SKILL.md`.

`content/is/README.md` records the first pack's earlier language-first authoring conventions.
Run `python tools/content/validate.py --preview` after edits to its canonical CSV/YAML files;
never edit the generated preview. That validator proves only the legacy Iceland text shape.
It does not prove that traveler research is deep, representative, current, engaging, or
decision-useful. `--release` must continue to fail while reviews or media are missing.

## Content-authoring invariants

- Treat user feedback on an example country as a potential system-level finding. Fix the
  immediate content, identify the underlying research, authoring, schema or verification gap,
  and update the relevant project guidance and deterministic checks when the lesson should
  recur. Generalize the question and workflow—not Iceland-specific conclusions or wording—to
  other destinations. Record why a lesson is destination-specific when it should not propagate.
- Begin with traveler questions, surprises, decisions, regrets and desired experiences. Do
  not begin by filling phrase, quiz or sight quotas.
- Discover the destination's actual travel modes before fixing the table of contents. Do not
  inherit a car-versus-tour template. Treat a mode as distinct when it materially changes
  lodging, route flexibility, daily chores, booking, safety, cost, accessibility or legal
  constraints—for example compact campervan versus car plus lodging, not merely “self-drive.”
- Record primary, supporting and deliberately excluded modes in the dossier with source IDs,
  traveler fit, advantages, frictions, seasonality and reader-content coverage. Candidate
  modes are prompts for research, not a quota, and forum recurrence is not proof of popularity.
- Discover itinerary shape separately from transport: one base, two regional bases, frequent
  lodging changes and continuous circuits create different packing, recovery and backtracking
  trade-offs even when travelers use the same car, tour or public transport.
- Make season advice goal-specific. If readers ask for good, bad or worst months, state which
  trip goal, region and travel mode make a period a poor fit; never turn monthly climate into a
  forecast. Give season-specific clothing adjustments on top of an all-season safety baseline,
  and distinguish access, daylight, demand, wildlife and dark-sky trade-offs.
- When destination-specific gear is consequential, research three paths: bring or buy before
  departure, rent locally, and buy locally. Compare availability, sizing, pickup/return effort,
  price, expected reuse, quality and authenticity. Do not turn a reputable local product into
  a claim that every locally sold item has the same origin or quality.
- Every place entry exposed as a popup must carry the English display name, local name,
  approved respelling/transcription, pronunciation-audio status and media status. A
  placeholder is honest draft state; it must not masquerade as a cleared photo or finished
  native recording. Media provenance and rights review remain separate from place facts.
- Prefer real, locally bundled photos from Wikimedia Commons or Flickr Creative Commons for
  destination-specific imagery. Approved sources for attraction photos are Wikimedia Commons
  and Flickr; add another source only by updating this rule. Select only files whose
  individual page states a license that allows free commercial use with attribution at most:
  CC0, public domain (with the basis stated), CC BY or CC BY-SA, any version. Reject NC
  (non-commercial), ND (no derivatives, which forbids cropping), “all rights reserved”,
  GFDL-only and unclear or conflicting licenses. On Flickr, also confirm that the photo is the
  uploader's own work and not a re-upload. Do not infer a license from a search
  result, uploader profile or “free photo” label. Store the original URL, author, license,
  license URL, download date and an accuracy/release status in the pack media manifest. Show
  a compact credit in the reader and keep a full attribution list available offline. Unsplash,
  Pexels, Pixabay and similar stock sources may supply generic atmosphere, but must not be
  presented as an exact landmark photo without destination verification. Check people, logos,
  artwork, property and venue restrictions separately from copyright. Use generated images
  only as clearly labeled prototypes when a cleared real image is unavailable.
- Never use a generic landscape, city street, stock mood image or generated illustration as a
  substitute for a named destination. If an exact destination image is not available and
  verified, leave the image area in an explicit pending state; an honest empty state is better
  than a visually attractive but misleading place match.
- For each attraction, source a shortlist of 10–20 landscape-oriented candidate photos from
  the approved sources only. Verify the actual file page, destination match, license, author
  and source before presenting the shortlist to the content author. For each candidate, show a
  thumbnail, the source link, author, license, pixel dimensions and aspect ratio, so the
  selection is informed. Present the shortlist as a local review page or an equivalent
  side-by-side view, not as bare URLs.
- Keep the content author in the loop. The author chooses 3–5 photos per attraction. Agents
  must not pick, rank into a final gallery or ship photos the author has not selected. Record
  the author's choice and the date in the media manifest. If there are fewer than 10 valid
  candidates, present the available verified set and explain the shortfall rather than
  padding with unrelated pictures. A gallery with 1–2
  author-selected photos is an allowed `partial` gallery: show what the author chose, flag it
  in the manifest, and extend it later from further sources or another shortlist round, keeping
  earlier picks. With no author-selected photo, leave the slot pending.
- Landscape only: width must exceed height, with an aspect ratio of at least 4:3 (1.33).
  Reject portrait, square and panoramas so wide that the subject becomes a sliver at card
  size. Read the real pixel dimensions from the file or file page; never trust a thumbnail.
- No harmful cropping on any surface. The same photo appears in several places: list card,
  carousel, popup and full-screen viewer. Before presenting a candidate, and again after
  selection, preview the actual render at every card size, at phone width, in both themes.
  The attraction must be fully recognizable on every surface. Do not cut off its top, edges
  or defining feature. Where a fixed-ratio frame would crop it, set a per-image focal point
  (`object-position`) or use a full-image fit (`contain`) with a neutral background. Store
  that per-image display setting in the manifest so every card uses it. Never assume a wide
  image will crop safely, and do not use a non-destination picture to fill the gallery.
  Store the selected candidate IDs and source/author/license metadata in the pack.
- Recent firsthand traveler reports are a core research input. Research across independent
  communities and traveler profiles; store dates, trip context, links and paraphrased
  observations in the dossier.
- Forums demonstrate recurring concerns and disagreements, not population frequency. Never
  convert a number of posts into an incident rate or write `most travelers` without evidence
  that supports that quantifier.
- Separate `traveler pattern`, `split opinion`, `editorial take`, `official guidance`, and
  `provider-specific terms`. A source that proves one does not prove the others.
- Give useful contrasting anecdotes: issue and no issue, covered and not covered, a choice
  that worked and one the traveler regretted. Include the circumstances that may explain the
  difference. Never invent the missing side of a story.
- Opinion is welcome when it is useful to the target traveler and labeled. For uncertain
  choices, explain what travelers report, what varies, what to verify, and which trade-off the
  user must decide for themselves.
- A television program, blog or guide can signal that a topic is engaging or important. Trace
  important factual claims to multiple independent or authoritative sources. Do not copy a
  source's wording, sequence, signature format, images or footage.
- Anything safety-, health-, legal-, emergency- or insurance-sensitive needs an authoritative
  or contract-specific check in addition to anecdotes. Friendly wording does not remove that
  requirement.
- Practice is opt-in. Do not interrupt briefings with mandatory quizzes, gate reference
  content behind lessons, or add trivial questions merely to create interaction.
- Every country draft goes through research, synthesis, writing, evidence review, editorial
  review and traveler-task testing. Record unresolved weaknesses and repeat the loop; do not
  silently promote a draft.

## Invariants worth restating

- No network code outside `packs/store`, and no network call that the user did not start.
- Guide articles are reviewed semantic HTML rendered from an installed pack in a restricted
  WebView. They are not remote web pages: file access, arbitrary navigation and unapproved
  script are disabled, and external links leave the app through an explicit native handoff.
- Every downloaded guide, place, language-reference and optional-practice item works in
  airplane mode, start to finish.
- Phrase audio never plays through the speaker unasked when quiet mode is on.
- Phrase audio in a published pack is human, native-speaker recording; TTS only in `draft` packs.
- Respellings use only the key in `docs/CONTENT.md`.
- Fast-changing information is labeled and handed off to a live or provider-specific source.
  A timeless offline briefing may explain what to check and why, but not freeze a current
  price, opening hour, forecast, closure or contract term as durable truth.
- `packs/model`, `guide/model` and `practice/engine` stay pure Kotlin. HTML presentation stays
  outside those models; the Android app owns the restricted WebView host.
- Optional-practice generation is deterministic from (pack version, session id, seed);
  reference vectors pin it.
- Progress is keyed by stable item ids and survives pack updates and deletes.
