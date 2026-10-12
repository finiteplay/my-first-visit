# Country Pack Content

Status: **draft specification; app and pack compiler not built.** Iceland has a strict-audited
traveler dossier, briefing, playbooks and routes plus complete sources for the earlier
language-first model at `../content/is/`; Japan remains a language excerpt. Iceland still lacks
independent traveler/destination/native approval, native audio and licensed photos.

A country pack is an offline, reader-facing synthesis of destination research. The briefings,
playbooks and realistic routes are primary; language and optional practice support them.
The research dossier remains an authoring artifact and supplies provenance, contradictions,
freshness and update work.

| Part | Count | Shown in |
|---|---|---|
| Research dossier | normally 30+ recent firsthand accounts across 3+ communities for a full first pass; expand by topic | Authoring only; evidence labels and source links compile into reader content |
| Destination briefing | 1 concise orientation | Guide home and linear read |
| Decision playbooks | determined by research, not a quota | Guide; filtered by trip mode and season |
| Practical routes | enough to cover declared primary trip modes | Guide and Places |
| Places and experiences | research-selected, with route fit rather than an arbitrary ranking quota | Places and playbooks |
| Phrases | up to 50 stable toolkit slots; 50 for the current non-English-country model | Language; Show a local; optional Practice |
| Reading primer | 6–12 rules + 6–12 sign words when useful | Language and relevant playbooks |
| Scenario lines | useful things a local may say | Language and optional Practice |
| Audio | every phrase at two speeds, every primer word, sight name and scenario line | everywhere |
| Photos and maps | selected for the briefing, playbooks, routes and places | Guide and Places |

Size budget per pack: **≤ 12 MB** (expected about 6 MB: ~2.5 MB audio, ~3 MB photos). The pack
build fails over budget.

## The language toolkit and 50 phrase slots

This detailed supporting schema appears early so stable IDs can be specified in one place; it
does not set the product hierarchy. Briefings, playbooks and routes remain the primary content.

The current non-English-country model fills the same 50 slots so the phrasebook, Show a local
and optional practice can share stable behavior. A pack may **replace up to 5 slots** with local
essentials. The replacement stays in the same category, and the pack records why ("Iceland has
no trains"). English-speaking destinations may ship a smaller differences/signs toolkit instead
of manufacturing a 50-phrase curriculum.

| # | Category | Slot (English meaning) |
|---|---|---|
| 1 | Courtesy | Hello |
| 2 | Courtesy | Good morning / Good day |
| 3 | Courtesy | Goodbye |
| 4 | Courtesy | Please |
| 5 | Courtesy | Thank you |
| 6 | Courtesy | Thank you very much |
| 7 | Courtesy | You're welcome |
| 8 | Courtesy | Excuse me (to get attention or pass) |
| 9 | Courtesy | Sorry |
| 10 | Courtesy | Yes |
| 11 | Courtesy | No |
| 12 | Courtesy | I don't understand |
| 13 | Courtesy | Do you speak English? |
| 14 | Courtesy | My name is … |
| 15 | Getting around | Where is …? |
| 16 | Getting around | Toilet / restroom |
| 17 | Getting around | Train station |
| 18 | Getting around | Airport |
| 19 | Getting around | Hotel |
| 20 | Getting around | Left |
| 21 | Getting around | Right |
| 22 | Getting around | Straight ahead |
| 23 | Getting around | This address, please (taxi) |
| 24 | Food and drink | A table for two, please |
| 25 | Food and drink | The menu, please |
| 26 | Food and drink | Water |
| 27 | Food and drink | Coffee |
| 28 | Food and drink | Beer |
| 29 | Food and drink | I'd like … |
| 30 | Food and drink | I'm allergic to … |
| 31 | Food and drink | Delicious! |
| 32 | Food and drink | Cheers! |
| 33 | Food and drink | The check, please |
| 34 | Money and numbers | How much is it? |
| 35 | Money and numbers | Can I pay by card? |
| 36 | Money and numbers | Cash |
| 37 | Money and numbers | This one, please |
| 38 | Money and numbers | Open (sign) |
| 39 | Money and numbers | Closed (sign) |
| 40–45 | Money and numbers | One, Two, Three, Four, Five, Ten |
| 46 | Help | Help! |
| 47 | Help | Call the police |
| 48 | Help | I need a doctor |
| 49 | Help | I'm lost |
| 50 | Help | Pharmacy |

Slots ending in "…" take a word from the pack (*Where is* + *the toilet*), and the
phrasebook offers complete saved examples. Store them in `completions.yaml`, linked to the
base slot; never blindly concatenate a dictionary word, since grammatical forms may change.
Names and addresses are user-supplied, not translated or prerecorded. Slot 30 has six
prescribed categories (peanuts, tree nuts, shellfish, gluten, milk, eggs) as separate cards.
This is not an allergy-prevalence ranking or an exhaustive list. Independent translation and
safety review are required; distinguish allergy from celiac disease and intolerance, and
confirm ingredients and cross-contact requirements with staff.

### What each phrase carries

| Field | Rule |
|---|---|
| Local text | As a local writes it, in the local script (こんにちは, Góðan daginn) |
| Romanization | Only for non-Latin scripts (Japanese: Hepburn with macrons, *arigatō*) |
| American respelling | Per the key below. Required |
| IPA | Optional; shown only if the user turns on *Show IPA* |
| Meaning | Plain US English |
| When to use | One line, ≤ 90 characters ("Shops and restaurants say this as you leave; nod back") |
| Formality | `neutral`, `polite` or `casual`, shown only when it matters |
| Audio | `normal` and `slow` takes (below) |
| Audio of the reply | Optional: the likely answer, for scenario exercises |

## American respelling

The respelling is the most important text in the app. It is written for a General American
reader, uses only the key below, and never uses IPA symbols. A reader who has never seen the
language should say something a local understands.

| Spelling | Sounds like | | Spelling | Sounds like |
|---|---|---|---|---|
| ah | f**a**ther | | oh | g**o** |
| a | c**a**t | | aw | l**aw** |
| ay | d**ay** | | oo | f**oo**d |
| eh | b**e**d | | uu | b**oo**k |
| ee | s**ee** | | ow | c**ow** |
| ih | s**i**t | | oy | b**oy** |
| eye, ai | **eye** | | uh | c**u**p |
| ur | f**ur**, with no r sound | | th | **th**in |
| dh | **th**is | | kh | Scottish lo**ch**, German Ba**ch** |
| y | **y**es | | rr | a rolled or tapped r |
| zh | mea**s**ure | | ng | si**ng** |

- Syllables are separated by hyphens. The stressed syllable is in CAPITALS: *GOH-dhan DAH-gihn*.
  Familiar English consonants may be used alongside the vowel/sound key. Avoid ambiguous
  vowel shortcuts such as `ye` for `eye`. Function words may be unstressed in connected
  speech; native listening review remains necessary.
- Languages without word stress (Japanese, French) use no capitals. Each syllable gets equal
  weight, and the primer says so.
- One respelling per phrase. Alternatives go in *When to use*, not in brackets.
- A sound English lacks gets the nearest key spelling, plus a reading-primer rule that explains
  it (Icelandic *ö* is *ur*, and the primer explains "with no r").

## Audio

Every phrase is recorded by a **native speaker of that country's variety** (Mexican Spanish
for Mexico, Castilian for Spain). Neural TTS may be used for prototypes only. A pack built
with any TTS clip is marked `draft` and cannot be published.

| Property | Value |
|---|---|
| Takes | `normal` (natural, unhurried speech) and `slow` (re-recorded slowly, not time-stretched) |
| Voices | One main voice per pack. Scenario lines (a local talking to you) use a second voice, so the user hears two people |
| Format | Ogg Vorbis, mono, 44.1 kHz, about 64 kb/s (the format `card_games` already plays) |
| Loudness | −16 LUFS integrated, true peak ≤ −1 dBTP, every clip in a pack matched |
| Edges | Silence trimmed to 150 ms at each end |
| Naming | `<slot or id>_<take>.ogg`: `p05_normal.ogg`, `p05_slow.ogg`, `sign_deguchi_normal.ogg` |
| Provenance | Speaker (by role, not by name unless they agree), date, licence, SHA-256, in the pack's `CREDITS.json`, as `card_games/docs/SOUND_ASSETS.md` does |

The pack build measures loudness and length. A clip over 6 s, or more than 1 LU from the
target, fails the build.

## Reading primer

The primer teaches the user to **sound out** what they see on signs and maps. It does not
teach them to read the language. Each rule is one letter or letter group, its respelling, and
an example word that the user will actually meet (a place name, a sign).

| Field | Rule |
|---|---|
| Pattern | The letter(s) as written: `þ`, `ll`, `hv`, `ー` |
| Sounds like | A respelling from the key, plus at most one sentence |
| Example | A real word: local text, respelling, meaning, audio |
| Trap | Optional: the usual American mistake ("not *jay*, *y*: *Já* is *yow*") |

Sign words are 6–12 words in the local script that the user should recognize by shape: exit,
entrance, toilet, men, women, station, open, closed, no smoking, pull/push where relevant.

For a non-Latin script the primer begins with one card on how the writing system works
(Japanese: three scripts, and what each is used for), then focuses on recognizing signs.

## Briefings and playbooks

Briefings and playbooks are researched narrative content, not a renamed collection of tips.
They use recent traveler accounts to discover what matters, preserve contrasting anecdotes,
separate traveler pattern from official/provider facts, and help the target traveler make a
decision. Their source and quality contract is [EDITORIAL.md](EDITORIAL.md).

Each core section carries stable identity plus:

| Field | Rule |
|---|---|
| User need | The decision, surprise or desired experience this section resolves |
| Audience and fit | Traveler origin, season and trip modes for which it applies |
| Hook | A concrete scene, consequence or choice; not generic destination praise |
| Traveler pattern | A calibrated synthesis linked to the research dossier |
| Anecdotes | Context, event, action and outcome; contrasting experiences where found |
| Editorial take | Labeled recommendation for this audience, with reasoning |
| Checklist | Preparation steps the user can complete before arrival |
| Live check | Provider/current source for facts that can change |
| Limitations | What the corpus cannot establish |
| Related items | Places, routes, phrases, signs and optional practice |

### Completeness standard (planned gate)

Status: **specified; enforced for playbook and route structure by `audit_guide.py`.**
Editorial quality still needs the human review in `EDITORIAL.md`.

The bar is set by two Iceland playbooks that read as finished: *What Iceland's changing
weather feels like, and what to pack* (`pack-for-exposure`) and *Rental car insurance: decide
before you collect the keys* (`rental-counter-before-counter`). A card that is shorter, vaguer
or less sourced than these is a draft, however tidy its fields look.

What the two models share, and every playbook must have:

| Element | Minimum | What the models do |
|---|---|---|
| Card image | `cardImage` with descriptive alt text | Shows the situation the card is about, not generic scenery |
| Hook | One concrete sentence on what is at stake | "The rental counter can introduce several Iceland-specific choices just when you are tired" |
| Body | 4+ paragraphs, 300+ words | Explains *why this place is different* (gravel, wind on doors; wind turning mild air cold), then walks through the paths a traveler can take |
| Specifics | Named things the reader can act on | Damage types by name; layers by season; what to ask the card administrator; rent in Reykjavík vs bring vs buy |
| Structured choice | `decision` with three paths, **or** `options` (3+) each with `bestFor` and `tradeoff` | Easiest / research / accept-more-risk; or June–August / shoulder / November–April |
| Action list | `checklist` of 5+ steps, **or** `avoid` with 3+ mistakes | Steps the reader can finish before arrival |
| Live checks | 3+ entries; current facts go here, not in prose | Official weather, road conditions, the exact agreement or benefit guide |
| Evidence | 8+ source IDs, covering at least one `traveler` and one `official` or `provider` source | 14–15 sources across traveler, official and provider roles |

Additional requirements by evidence:

- **`Experiences vary` cards** need 2+ `travelerStories` with contrasting outcomes and the
  circumstances that may explain them, and a `limits` statement saying what the corpus cannot
  establish. (Insurance: a covered windshield, an uneventful trip, a slow card reimbursement.)
- **Safety, legal, insurance, health and emergency topics** need a `warning` that names the
  authoritative or contract-specific check. This is judged in review, not by the script.
- **Bring, rent or buy** must be compared when gear is consequential (see `AGENTS.md`).

Routes follow the same principles. No Iceland route has met them yet, so this route standard
is derived from the playbook models rather than from an approved route example:

| Element | Minimum |
|---|---|
| Who it suits | `fits` plus a `whoFor` sentence naming the traveler, season and transport mode |
| Days | `days` list with one entry per day (at least the number of nights). Each entry has `base` (where you sleep), `travel` (drive time or transport, e.g. "about 2 h 15 min driving"), `highlights` and an optional `ifTired`/`weatherSwap` |
| Buffer | At least one flexible or weather-swap day on routes of 4+ nights |
| Season | `seasonNotes` saying how the route changes in the dark or stormy months |
| Trade-off | `tradeoff` or `skipIf` that names who should choose something else |
| Safety and live checks | `safety` when roads, beaches or glaciers are involved; 2+ `liveChecks` |
| Evidence | 5+ source IDs, with at least one traveler and one official source |

Drive times and opening periods are planning estimates; label them and send the reader to a
live source for the actual day.

### Best time to visit

Status: **built for the Iceland draft; checked by `audit_guide.py`.**

The basics section has a "Best time to visit" block in `basics.yaml` under `bestTime`: four season cards
(months, daylight, good for, watch for, sources) and a short takeaway that says which season suits which
traveler. Facts about roads, campsites, daylight and the aurora should come from an official source when one
exists and say so in the card; operator and rental-company claims are labeled as such. Keep it to what the
season changes for a traveler; leave price and weather figures to the live checks.

### Weather and road-status links

The same three official services (national weather service, road administration, the safety association's
travel conditions) are linked wherever a traveler decides to go somewhere: the basics section ("Check every
morning", `dailyChecks`), the weather section, the top of every route, and every place card ("Check today",
with roads only for places outside the capital area and the safety link only for nature stops). A playbook or
route `liveChecks` entry with a real URL is shown as a link. A new country needs the equivalent three services.

### Place priority and category filters

Every place shows a priority label for a first visit, derived from its `tier` in `sights.yaml`: "Don't miss"
(`must-see`), "Worth a stop" (`worth-it`) and "If you have time" (`if-you-have-time`). Each label has a small icon (pin, compass, hourglass; hidden from screen readers). Use words and icons, not
stars or scores: every label is a positive recommendation, so a lower priority never reads as a bad review. It is our
judgment, not a traveler or review-site score, and needs the reviewer's sign-off. The place grid is ordered by
priority, then by the original starter-list rank, then by name. The category buttons are built from the places'
`category` values with counts; no hand-maintained list is needed for a new category. The area buttons come from
`areas` in `sights.yaml` ({id, label, regions}): group fine regions into the few areas travelers think in
(Reykjavík area, Golden Circle, South, North, East, Snæfellsnes). Every place's `region` must belong to exactly
one area, which `audit_guide.py` checks. Area and type filters combine with the search box.

### Place lists inside a guide

A guide can list places with `placeGroups` ({group, intro, placeIds}) plus an optional `placeGroupsNote`. The app
builds each entry from the place data (name opening the place card, priority label, time, one line, website and
Google Maps links), so there is nothing to keep in sync by hand. The Reykjavík time guide uses it for the city's
sights; list only places that already have a card.

### Trip detail level and the stop map

Every trip is written to the same depth: who it is for, why it works, the trade-off and when to skip it, one entry
per day (a base town, a qualitative `travel` note, highlights, an "if tired" cut, a weather swap where one makes
sense, a flexible day when the trip is four nights or more), season notes, a safety boundary, what the evidence
cannot tell you, and live checks. Leave out restaurants, hotels and driving times; say only how hard the day is.

Each day lists `placeIds`: place cards (`sight-...`) or soak entries from the pool guide (`soak:` plus the slug of the
entry's name, such as `soak:blue-lagoon`), in the order they are visited. The app turns them into chips that open the
card and into a schematic map of the trip: one dot per stop, colored by day, joined in order within each day (and, for a trip with `mapConnectDays: true` that changes base most nights,
between days with a dashed line), cropped to the stops
(a trip entirely inside the capital area uses the local outline). `audit_guide.py` fails on an id that does not exist.

### TripAdvisor link and rating

Each place can carry `tripadvisor` ({url, rating, reviews, checkedAt, note}): a link to the place's TripAdvisor page, the
overall rating out of 5 and the review count, shown on the card and the place page. The grid sorts by TripAdvisor's own
ordering first: `icelandRank`, a place's position in TripAdvisor's list of top things to do in the country (only the
places on that list have one), then everything else by rating and review count. Two other sorts are offered: stars alone
and our own priority. `localRank` ({rank, of, destination, category, text}) records the place's rank inside its own TripAdvisor
destination (for example "#1 of 22 things to do in Selfoss"). A place without an Iceland position shows it on the card
instead ("#5 in Reykjavík"; a category rank reads "#1 Fun & Games in Reykjavík") and the full wording on the place page. Ratings change constantly and are TripAdvisor's
numbers, so `checkedAt` is required and the page tells the reader the date. TripAdvisor blocks automated page reads,
so the Iceland values came from search-result summaries: confirm each on the page before release. Places that are
villages or areas have no rating of their own (`rating: null`) and sort last. Before a public release, check
TripAdvisor's terms for showing ratings, or switch to link-only or their official content API.

### Placeholder feature images

A place without an author-selected photo can show `featureImage`: the image from the place's own website (its `og:image` or a
large hero picture), hotlinked and labeled as a placeholder. Rules: landscape between 4:3 and 2.2:1; it must show the
place (not a logo, a café, another site or a letterboxed graphic); never download it into the pack; show the source site and
that it is not licensed for reuse; remove it when a cleared photo is selected or if the owner objects. It is a development
convenience, not a release asset: get permission or replace it before publishing.

### Country map and number tiles

Status: **built for the Iceland draft; the map is checked by `audit_guide.py`.**

The basics section carries a small schematic map drawn as inline SVG (no network, light and dark
themes, a text alternative under "Map as text"). Source: `content/<cc>/map.yaml`: a simplified
coastline, route lines (the main circular road and one famous short loop), towns, glacier points,
a glacier lagoon and one famous volcano, each with a label offset. The coastline comes from Natural
Earth (public domain); positions and lines are simplified by hand and labelled "not for navigation".
Every point and waypoint must fall inside the outline's bounding box. The famous volcano is also in
the word page with a respelling and audio, so the name can be said before the trip.

The basics section also has a **volcano card** for the country's best-known volcano: name with respelling and
audio, a short summary, sourced facts, a "see it" tip and one image. The image block in `basics.yaml` must record
author, license (public domain, CC0, CC BY or CC BY-SA), source URL, download date, alt text and review status, and
the file must exist; the audit checks this. Prefer public-domain agency imagery (for example NASA) for events
that no free photograph covers.

Each "Iceland in numbers" tile has an `icon` (an emoji, hidden from screen readers) so the facts are
easy to scan.

### Place location: Google Maps link and minimap

Status: **built for the Iceland draft.**

Every place card ends with "Where it is": a small SVG map with one highlighted dot and an "Open in
Google Maps" link built from the place's `location` pin (`sights.yaml`). No network is needed for the
map. Places within `radiusKm` of a region centre in `map.yaml` `regions` (Iceland: the Reykjavik area,
15 km) get that local outline; a region can instead be tied to a place `region` with `forRegions` (the Golden Circle uses an
inland map of lakes and main roads built with `tools/maps/build_region_inland.py`), with the other places in the area as grey dots; every other place gets
the country outline and the main road. Pins are still "draft-pin" until someone verifies the entrance
and accessibility. A new country needs its own `regions` entry only if it has a main city with sights
close by; build it with `tools/maps/build_region_outline.py` from OSM coastline ways (ODbL, credit
shown under the map; needs `shapely` in the tooling venv).

Each place also has a `website` ({url, label, kind, checkedAt}) shown beside the map link: the operator's own site
when there is one, otherwise the managing authority (national park, Environment Agency, Safetravel) or the
regional tourism board, with the label saying which. Do not link a booking marketplace or a review site, and
re-check each URL (HTTP 200, right page) before release.

The same two links (`location` pin and `website`) go on every entry of a `whereToSoak` list in a playbook (pools,
lagoons, hot springs). If the pin is a trailhead or car park instead of the place itself, say so in
`location.mapNote`; leave `website` out when no official or authority page exists.

A playbook can also carry `trackers` ({name, url, shows, useItFor}), a short list of live-data websites with what each
shows and its limits (the aurora guide uses it for forecast and cloud sites). `liveChecks` entries with a real URL are
shown as links; `provider-specific` ones are shown as plain text. Each card in the advice list needs its own card
image: do not reuse one image across two guides.

### Word page ("Say it in Icelandic")

Status: **built for the Iceland draft as its own page, `local-site/words.html`; checked by
`audit_guide.py`.**

A separate, browsable list of simple words, assembled at build time from the language toolkit so
words are authored once. Source: `content/<cc>/vocabulary.yaml` (group order, introductions, extra
words and the simplicity rule) plus `phrases.csv`, the primer's signs and the audio manifest.

**Keep it simple.** The page lists single words and short two-word expressions only. Sentences,
requests with a blank to fill in and anything longer stay in the phrase toolkit and practice, not
on this page, so "Hringdu í lögregluna" (call the police) is represented by *Lögregla* (police).
The rule is `rules.maxWords` in `vocabulary.yaml`; place names are exempt.

| Group | Contents | Shown |
|---|---|---|
| Courtesy | Phrases in the `courtesy` category | Always, with or without audio |
| Emergency and help | Phrases in the `help` category plus extra words (police, ambulance, hospital, doctor, accident) | Always; carries the local emergency number |
| Getting around, Food and drink, Money and numbers, Signs, Place names | Remaining phrase categories, signs and place names | Only words with approved audio |

Every extra word needs a respelling, a meaning, `sourceIds` and at most `maxWords` words. A word
appears once, in the first group that claims it. Audio comes from
`tools/audio/generate_place_audio.py`: a draft synthetic voice with the best of several takes,
checked with Whisper. A slow take was tried and dropped because its quality was poor. Draft audio
and respellings stay labeled until a native reviewer approves them. Notes must be plain language
and never refer to internal ids.

### Basic information ("Iceland at a glance")

Status: **built for the Iceland draft; checked by `audit_guide.py`.**

A short orientation section shown early on the home page, before the playbooks. It is written
in the friendly, practical voice of someone who has been, and it sends readers to the full
playbooks instead of repeating them. Source: `content/<cc>/basics.yaml`.

| Part | Rule |
|---|---|
| Names | The country and capital: English name, local name, American respelling (see "American respelling"), meaning, a short story, and audio. Respelling and audio are drafts until a native reviewer approves them |
| Numbers | 4+ facts (people, size, capital, wildlife counts, emergency number). Each has `sourceIds`. Where sources disagree, give a range and say so; never pick the figure that looks neatest |

Counts and populations change; state the date or year they were measured. Keep the section short:
anything that needs more than a paragraph belongs in a playbook. Do not repeat decision-guide advice here; if a
useful fact is not in a guide, add it to the guide that fits.

## Short practical cards

Short cards may support a briefing or playbook. They are true, useful and kind; they do not
replace the researched synthesis. A card may be something an American traveler is likely to
get wrong or be surprised by. It is not trivia, and it never sneers at either culture.

| Field | Rule |
|---|---|
| Title | ≤ 40 characters, says the point ("Horses, not ponies") |
| Severity | `avoid` (a real faux pas), `good-to-know`, `locals-love-it` (an easy win), `safety` |
| Category | Greetings · Dining and tipping · Money · Getting around · Dress and sacred places · Gestures · Taboos · Safety · Phrases in context |
| Body | ≤ 280 characters: what happens, what to do instead |
| Why | Optional, ≤ 200 characters: the reason behind it |
| Linked phrase | Optional: a phrase slot or scenario line to practise with it |
| Optional practice | A plausible scenario may be linked into Practice; no question is required on the information card |
| Source | A link the editor checked (not shown in the app; kept in the content source) |
| Reviewed by | A native or long-term resident reviewer, by role |

Editorial rules:

- Say "most people" or "usually", not "all Icelanders".
- Explain fast-changing decisions but move current prices, hours, exchange rates, availability,
  closures and contract terms to a dated live/provider source.
- Safety tips are allowed to be blunt.
- Common-sense precautions may be direct. Sensitive claims still need the source role required
  by `EDITORIAL.md`; friendly wording is not a substitute.
- Every pack has at least one `phrases in context` tip, such as how to react when shop staff
  thank you in Japan.

## Places and experiences

Place cards carry editorial judgment, not crowd ratings. Research selects them because they
support a desired experience, route or traveler decision—not to fill a top-ten quota. Each card
states who it fits, what travelers found memorable or difficult, and how it combines with a
realistic day.

| Field | Rule |
|---|---|
| Name | English name, local name (with audio), respelling |
| Where | Region and nearest city |
| Category | Nature · Landmark · Museum · Sacred place · Neighborhood · Experience |
| Editorial fit | `signature`, `worth-it-for`, `skip-if`, with the audience or trip profile made explicit |
| Why go | ≤ 120 characters |
| Time needed | A range ("1–2 hours", "a full day") |
| Best time | Season or time of day ("early morning, before the tour buses") |
| Tip | ≤ 200 characters, practical |
| Phrase here | Optional: a phrase slot or a custom line useful at this place |
| Location | Latitude and longitude, for *Open in Maps* |
| Photo | 1280×720 WebP, ≤ 250 KB, plus a 480×270 thumbnail; credit and licence |

Photos must be owned, CC0, CC BY or CC BY-SA. The credit line is shown on the photo in the app,
and the licence is listed in Settings › About › Acknowledgements, beside the code licences.

## Pack source and build

Guide articles are authored as semantic HTML and compiled into a pack by `tools/packs`
([ARCHITECTURE.md](ARCHITECTURE.md)). HTML is the editorial source because it can be opened in
a browser, reviewed in familiar visual or source editors, and express figures, captions,
quotations, comparisons and callouts without forcing editors to manipulate nested YAML.
Research evidence, media rights, language tables and pack metadata remain structured sidecar
files. Generated runtime indexes are never canonical editorial sources.

The authoring HTML uses a deliberately small vocabulary: `article`, `header`, `section`,
`h1`–`h3`, `p`, `ul`, `ol`, `figure`, `img`, `figcaption`, `blockquote`, `aside`, `table`,
`details`, `summary`, `a`, `em` and `strong`. Classes and `data-*` attributes come from a
documented allowlist. Scripts, event-handler attributes, iframes, forms, embedded remote media
and arbitrary inline styles are build errors. Important safety or decision information must
also exist as text; an image alone is never the instruction.

Stable article, section and interactive-action IDs survive wording and layout changes.
`data-source-id` connects a material assertion or paraphrased account to the source registry;
`data-media-id` connects a figure to `media.yaml`. Authors may use a generated relative preview
`src` while editing, but the compiler resolves it from the media ID and rejects unknown,
unlicensed or missing release assets. Alternative text describes the image; `figcaption`
explains why it matters. Credits and licence details come from the media registry rather than
being recopied into every article.

The source layout is meant for editors and reviewers, not just engineers:

```
content/is/                 one folder per country (ISO 3166-1 alpha-2)
  research/
    corpus.csv              recent accounts and authoritative sources with context
    dossier.yaml            topic signals, anecdotes, disagreements and synthesis
    REVIEW.md               gates, failures, revisions and traveler-task evidence
  pack.yaml                 country, language, audiences, version and feature availability
  articles/
    start-here.html         destination orientation and audience-specific framing
    <playbook-id>.html      practical decisions and recurring situations
    <route-id>.html         realistic combinations of experiences
  phrases.csv               one row per slot: slot, local, romanization, respelling, ipa,
                            meaning, when, formality
  completions.yaml          complete examples and allergy cards linked to stable phrase ids
  primer.yaml               rules and sign words
  tips.yaml                 short supporting cards
  sights.yaml               places and experiences
  scenarios.yaml            things a local says; may feed optional practice
  sources.yaml              source links, scope, date and review limits
  media.yaml                intended audio/photo inventory, with honest missing status
  README.md                 editorial decisions and review/validation steps
  PREVIEW.md                generated reading copy; not a second source of content
  RECORDING_BRIEF.md         speaker script, delivery rules and photo assignments
  audio/                    p01_normal.ogg … (names as above)
  photos/                   <sight id>.jpg originals; the build makes the WebPs
  CREDITS.csv               every audio and photo file: author, licence, source, date
```

The current Iceland `briefings.yaml`, `playbooks.yaml` and `routes.yaml` are transitional
research-backed draft sources created before this authoring decision. Migrate them into
`articles/*.html` before the production pack compiler is called complete. Do not maintain the
same prose in both formats; once an article is migrated, HTML becomes its sole editorial source.

The research gate checks corpus recency and diversity, source-role fit, independent support,
contrasting anecdotes, sensitive-topic verification and the recorded stopping judgment. The
pack build parses and sanitizes every article, validates the element/class/attribute allowlist,
IDs, heading order, internal links, evidence references, image references, alternative text and
captions. It also checks required stable language slots, replacement limits, respelling syntax,
audio takes and loudness, photo rights, archive size and that no runtime document depends on a
remote resource. Optional-practice coverage is checked only when the pack declares Practice
available.

Those are planned production checks. Reviewers also open the built article set in an ordinary
browser at phone and large-text widths before approval. The Python validator checks the text draft and
preliminary publication readiness only. The `.yaml` examples use the JSON subset of YAML
to keep this early check dependency-free. A draft may pass text checks with missing media;
it cannot pass `--release`. Coordinates in range do not prove a safe entrance, and respelling
syntax does not prove pronunciation. Review both explicitly.

## Example: Iceland

The canonical first-country example is [content/is/](../content/is/README.md).
Read its [package notes](../content/is/README.md), research dossier, briefing, playbooks and
routes for the research-backed example. Its [generated content preview](../content/is/PREVIEW.md)
covers the older language/media layer: phrases, reading guide, supporting cards, places and
local-response scenarios. Do not maintain a second Iceland translation table here.

The draft uses two justified replacements: slot 4 teaches **takk in a request** instead of a
universal word for please; slot 17 teaches **strætó (bus)** instead of train station.
Complete saved questions and orders demonstrate the required noun forms. The lost phrase
avoids choosing a gendered adjective, and the allergy categories have separate complete cards.

Sources and review limits are recorded in [sources.yaml](../content/is/sources.yaml).
The [recording brief](../content/is/RECORDING_BRIEF.md) and media inventory specify every
required take and photo. No media rights or native approval are implied by a text-check pass.

The pack is a research-backed editorial draft, not a downloadable release. The strict dossier
and guide-structure gates pass; independent timed traveler tests are still pending.
Native-speaker review of all language and respellings, destination and allergy/safety review,
authentic media, verified entrance pins, optional-practice testing and production compilation
remain required.

## Sample: Japan

Draft, not yet reviewed by a native speaker.

Language note: *English is understood in big-city hotels and stations, much less elsewhere.
A little Japanese and a lot of politeness go a long way.*

Replaced slots: **26 Water → Itadakimasu** (water is served free; this is said before every
meal) and **28 Beer → Gochisōsama deshita** (said after a meal, often to staff as you leave).
Japanese respellings have no capitals: give each syllable equal weight.

### Phrases (excerpt)

| # | Local | Romanization | Respelling | Meaning | When to use |
|---|---|---|---|---|---|
| 1 | こんにちは | konnichiwa | kohn-nee-chee-wah | Hello | Daytime greeting |
| 6 | ありがとうございます | arigatō gozaimasu | ah-ree-gah-toh goh-zai-mahs | Thank you very much | The polite thanks, safe with anyone |
| 8 | すみません | sumimasen | soo-mee-mah-sen | Excuse me / sorry | Calling a waiter, squeezing past, small apologies |
| 10 | はい | hai | hai | Yes | Also means "I'm listening" |
| 11 | いいえ | iie | ee-eh | No | Softer: a small wave of the hand |
| 13 | 英語を話せますか？ | eigo o hanasemasu ka? | ay-goh oh hah-nah-seh-mahs kah | Do you speak English? | |
| 15 | トイレはどこですか？ | toire wa doko desu ka? | toh-ee-reh wah doh-koh dess kah | Where is the toilet? | |
| 26 | いただきます | itadakimasu | ee-tah-dah-kee-mahs | (said before eating) | Before every meal, hands together optional |
| 28 | ごちそうさまでした | gochisōsama deshita | goh-chee-soh-sah-mah desh-tah | Thank you for the meal | After eating, or to staff as you leave |
| 32 | 乾杯！ | kanpai! | kahn-pai | Cheers! | Wait until everyone has a drink |
| 33 | お会計お願いします | okaikei onegaishimasu | oh-kai-keh oh-neh-gai-shee-mahs | The check, please | Or cross your index fingers in an X |
| 37 | これをください | kore o kudasai | koh-reh oh koo-dah-sai | This one, please | Point at the menu photo as you say it |

### Reading primer (excerpt)

The first card: *Japanese uses three scripts together. Hiragana (rounded) writes grammar and
native words. Katakana (angular) writes foreign words, often English, so トイレ is "toire",
toilet. Kanji are Chinese characters for meaning. You won't learn to read in a flight, but you
can learn to spot the signs that matter.*

| Pattern | Sounds like | Example | Trap |
|---|---|---|---|
| a i u e o | ah, ee, oo, eh, oh: always the same | sake — sah-keh | Not "SAH-kee" |
| ō, ū (long vowels) | hold the vowel twice as long | Tōkyō — toh-kyoh | Not "toe-KEY-oh" |
| desu, -masu | the u nearly vanishes | desu — dess | |
| doubled consonant | a tiny pause before it | kitte (stamp) — kit-teh | |
| r | a light tap between r, l and d | arigatō | Not the American r |
| ー (katakana dash) | lengthens the vowel before it | コーヒー kōhī — koh-hee (coffee) | |
| No stress | every syllable gets equal weight | | |

Sign words: 出口 *deguchi* Exit · 入口 *iriguchi* Entrance · 男 Men · 女 Women · 駅 *eki*
Station · トイレ *toire* Toilet · 禁煙 *kin'en* No smoking.

### Supporting cards (excerpt)

These examples predate the experience-led model. They may support future playbooks, but their
quiz-like presentation is optional practice rather than the primary reader flow.

| Title | Severity | Body |
|---|---|---|
| When staff say "arigatō gozaimasu" | good-to-know (phrases in context) | Shop and restaurant staff thank you constantly, often as "arigatō gozaimashita!" as you leave. You don't owe a reply: a small nod or smile is the natural answer. If you want to say something, "arigatō" back is fine; after a meal, "gochisōsama deshita" is perfect. |
| When someone thanks *you* | good-to-know (phrases in context) | "Dō itashimashite" (you're welcome) is the textbook answer, but it can sound stiff. A modest "iie, iie" (no, no) with a small wave of the hand is what most people say. |
| Don't tip | avoid | Tipping isn't part of the culture, and staff may chase you down to return the money. Good service is already in the price. |
| Chopsticks: never upright in rice | avoid | Standing chopsticks in a bowl of rice, or passing food from chopstick to chopstick, echoes funeral rites. Rest them on the holder or across the bowl. |
| Quiet on trains | avoid | No phone calls on trains, and keep conversations low. Set your phone to silent ("manner mode"). |
| Cash on the tray | good-to-know | At the register, put cash or your card on the small tray, not into the cashier's hand. Your change comes back the same way. |
| Carry your trash | good-to-know | Public trash cans are rare. Keep a small bag for your trash until you find a bin, often next to convenience-store or vending-machine areas. |

### Sights (excerpt)

| Sight | Local name | Tier | Why go | Time needed | Tip |
|---|---|---|---|---|---|
| Fushimi Inari Taisha | 伏見稲荷大社 | must-see | Thousands of vermilion torii gates winding up a forested mountain | 2–3 hours for the full hike | Go early morning; crowds thin past the first viewpoint |
| Sensō-ji | 浅草寺 | must-see | Tokyo's oldest temple, through the giant lantern gate | 1–2 hours | Wash your hands at the purification fountain before entering |
| Itsukushima Shrine | 厳島神社 | must-see | The great torii gate that seems to float at high tide | Half a day from Hiroshima | Check the tide: at low tide you can walk out to the gate |
| Nara Park | 奈良公園 | worth-it | Free-roaming deer that bow for crackers | 2–3 hours | Bow to a deer and it may bow back; keep paper maps out of reach |
