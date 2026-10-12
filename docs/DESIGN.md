# First Day Away — Design

Status: **draft, app not built.** Iceland has a strict-audited research dossier, primary
briefing, playbooks and routes plus the earlier language-first source pack at `../content/is/`.
Independent reviews and release assets remain pending. Product behavior below is planned,
not shipped.

First Day Away gives an American traveler a researched, engaging briefing for the first trip
to a country: what the experience will feel like, which decisions are easier to make before
arrival, what recent travelers repeatedly mention, where experiences differ, and how to choose
an itinerary and travel style. A practical language toolkit remains available, with optional
quiz-like practice for users who want it. Downloaded content works fully offline and is designed
to be useful during one flight and throughout the trip.

Companion specs:

- [CONTENT.md](CONTENT.md) — what a country pack contains, the 50 phrase slots, transcription and
  audio rules, the tip and sight formats, and sample content for Iceland and Japan
- [EDITORIAL.md](EDITORIAL.md) — how recent traveler accounts, travel media, official sources,
  anecdotes and editorial judgment become trustworthy, engaging content
- [UI_SPEC.md](UI_SPEC.md) — screens, navigation, components, visual system, accessibility
- [ARCHITECTURE.md](ARCHITECTURE.md) — modules, what is taken from `card_games`, pack delivery
  and storage

## The user

A US adult traveling abroad, often to that country for the first time. The v1 target is
American because the content should address decisions and surprises through a US traveler
lens, and because transcriptions are written for General American pronunciation. Later origin
lenses can reuse destination evidence while changing comparisons, assumptions and advice.

What they have on board: a phone, maybe headphones, no Wi-Fi, 2–12 idle hours, a seat
neighbour, and little patience for grammar.

Their test of success: *"Do I understand what this trip will be like, have I made the awkward
decisions before landing, and can I quickly find the words and practical advice I need?"*

## Product promise

- **One flight, one country.** A briefing sized for focused flight time, with progressive
  disclosure rather than a mandatory course.
- **Works in airplane mode.** Everything in a downloaded pack is on the phone before take-off.
- **Download what you need.** The app is small; each country is a separate pack of at most
  12 MB, fetched once on the ground.
- **Useful after landing.** Briefings, playbooks, routes, saved cards, the phrasebook and
  "Show a local" mode stay on the phone for the rest of the trip.
- **Research-backed, not crowd-ranked.** Recent traveler accounts reveal the questions and
  experiences; official and provider sources verify the claims within their scope.
- **Opinion with provenance.** The guide may recommend and compare, but distinguishes recurring
  traveler reports, split opinion, editorial judgment and current official guidance.

## What it is not

- Not primarily a language course: no grammar curriculum, compulsory drills, streaks or levels.
- Not a translator: there is no free-text input and nothing is translated live.
- Not a booking or raw-review site: no checkout, live review feed or invented crowd rating.
  Editorial synthesis may use traveler reports as research and link to changing sources.
- No accounts, no ads, no analytics, no push notifications (the `card_games` platform rules,
  kept where they still fit; [ARCHITECTURE.md](ARCHITECTURE.md) lists where this app departs
  from them).

## Ideas borrowed from travel media, traveler forums and language apps

The main experience borrows the journey, scenes, contrasts and practical recommendations of
good travel programs and trip reports. It does not copy their scripts, signature formats or
media. Traveler forums supply research questions and contrasting outcomes, not a live review
feed or incident statistics. Duolingo-like practice is available only when the user chooses it.

| From | Idea | First Day Away version | Left out |
|---|---|---|---|
| Travel programs and blogs | A destination experienced as a journey | Briefings open with what the trip feels like and progress through realistic choices and scenes | Copied wording, footage, branded formats or undisclosed promotion |
| Traveler forums | Recent stories, surprises and disagreements | Researched synthesis with contextual anecdotes and evidence labels | Raw review feeds, vote counts as truth, or forum posts as incident rates |
| Guidebooks | Editorial judgment and useful routes | Labeled *Our take*, audience-specific playbooks and realistic itineraries | False neutrality or a universal route |
| TripAdvisor | Place cards and trip reports | Place cards connected to traveler fit, route context and recent experiences | Star ratings, endless ranked lists and ads |
| Duolingo | Bite-size listening and recall | A separate **Practice** mode for selected words, signs and replies | Mandatory quizzes, streaks, hearts, leagues and content gates |
| Any source | Save for later | **Save** a briefing, checklist, phrase, route or place | Accounts and shared online trips |

Ratings are left out on purpose: we have no reviews, and an invented star score would be a lie.
The tier is an editorial judgment and is labeled as one.

## The destination briefing

The core of the app is a reader-controlled destination briefing: a concise orientation,
decision playbooks, experiences and practical routes discovered through traveler research.
The user may read linearly, jump to a current concern, save a card, or filter for a trip mode
and season. Nothing is locked behind completion.

The briefing is assembled around real traveler tasks rather than a fixed syllabus. A pack may
offer a 15-minute orientation, deeper decision playbooks, experience-led routes and searchable
reference cards. The user chooses the order and depth. Reading-time labels are rough editorial
estimates, never countdowns or claims that a destination can be mastered in a set time.

Guide content is an illustrated publication, not a sequence of database fields exposed to the
reader. Editors author and review each briefing, playbook and route as semantic HTML, with
photographs, maps, captions, traveler accounts, comparisons and callouts placed in the reading
flow. In the Android app, those installed offline documents appear inside the native navigation
and saved-content shell. The user should experience one coherent app; “WebView” is an
implementation detail, not a browser-like mode with an address bar or remote pages.

Typical guide paths are *Start here*, *Before you book*, *Driving*, *Weather and clothing*,
*Food and everyday rhythm*, *Experiences worth planning around*, and *If plans change*. The
actual set follows the research dossier: a country must not inherit irrelevant topics merely to
fill a template.

### Optional language practice

The user normally meets language inside a briefing, playbook or phrasebook. If they choose
Practice, a **learn card** shows the phrase in the local script, American respelling, meaning,
context and audio before recall. The deterministic generator may then use the exercise types
below (see [ARCHITECTURE.md](ARCHITECTURE.md)).

| Exercise | The user… | Used for |
|---|---|---|
| Learn | reads and listens; taps *Got it* | Every new item |
| Listen and pick | hears audio, picks the English meaning from 3–4 | Phrases, numbers |
| Pick the phrase | sees English, picks the local phrase (each option plays on tap) | Phrases |
| Match pairs | matches 5 local ↔ English pairs | Optional recap |
| Build it | assembles a multi-word phrase from tiles | Phrases of 2+ words |
| Say it | records themselves, plays it back against the native audio, rates *Nailed it / Close / Again* | Optional; skipped in quiet mode |
| Scenario | reads or hears a local line ("Arigatō gozaimashita!") and picks the right response | Phrases in context, customs |
| What would you do? | picks the polite option in a situation | Customs tips |
| Read the sign | sees a word in local spelling, picks how it sounds | Reading primer |

**Say it** is self-rated, not scored by speech recognition. On-device recognition for Icelandic
or Japanese is not reliably available offline, and a wrong score from a machine is worse than
an honest self-check. The recording stays in memory and is never saved.

**Feedback.** A correct answer shows a calm confirmation. A wrong one shows a correction
with the right answer, its audio, and one line on why ("*Takk fyrir* thanks someone for their
help; *takk* also works on its own"). A missed item comes back later in the same session,
if the user continues the practice session. Practice never interrupts a briefing.

**Practice memory** is optional and separate from reading progress: each practiced language
item may be *new*, *seen*, or *got it*. Merely reading or saving a card never changes practice
memory.

### Quiet mode

Planes are shared spaces. **Quiet mode** is on automatically when no headphones are connected,
and can be turned on by hand:

- audio never plays through the speaker by itself; tapping a play button asks once whether to
  play out loud
- *Say it* becomes *Say it in your head*: the user is shown the phrase, thinks it, then taps to
  hear the native audio, and rates themselves
- nothing else changes, so a whole flight works without sound

Headphones are detected through the audio output device list; nothing is recorded or
uploaded.

### Optional practice without guilt

- No points are required to access or complete a country briefing.
- A lightweight practice-session summary may show words reviewed and saved for later.
- A country keepsake or stamp, if retained, represents a trip or saved pack—not a claim that
  the traveler mastered the destination.
- **No streaks, no reminders.** A traveler opens the app because they are flying, not because a
  counter will reset.

## During and after the trip

The downloaded pack remains a travel reference:

- **Briefing and playbooks**: practical decisions, checklists, traveler experiences and live
  handoffs, filtered by trip mode and season.
- **Routes and places**: realistic ways to combine experiences, with fit and limitations rather
  than an endless popularity ranking.
- **Phrasebook**: all 50 phrases plus the reading-primer words, by category, searchable in
  English and the respelling, with audio.
- **Show a local**: any phrase full-screen, in the local script, as large as fits, with a
  play button. Built for taxi drivers, pharmacists, and noisy bars. *This address, please*
  (slot 23) has a field for the user to type their hotel address, stored on the phone.
- **Places**: sights and experiences by region, each with an *Open in Maps* link that hands
  coordinates to the phone's map app.
- **Saved**: every briefing, checklist, route, phrase and place the user saved.
- **Practice**: an optional language tool launched by the user, never a prerequisite.

## Country packs

Each destination is a pack: researched briefings, decision playbooks, practical routes, places,
the language toolkit and licensed media in one download. Packs are downloaded on demand,
stored on the phone, kept until deleted, and updated when their content changes.
[CONTENT.md](CONTENT.md) defines source and runtime contents; [EDITORIAL.md](EDITORIAL.md)
defines the evidence contract; [ARCHITECTURE.md](ARCHITECTURE.md) defines delivery.

A pack is per **country**, not per language: Mexico and Spain are separate packs with
separately recorded audio, phrase choices and customs. A country with more than one major
language (Switzerland, Belgium) gets its primary traveler language, and the pack says which
other languages the user will meet. Packs are free of charge or paid; see open questions.

### Launch set

Chosen for US outbound travel volume, plus the two countries used as worked examples in this
spec. To confirm before content work starts (open question 3).

| Pack | Language | Why |
|---|---|---|
| Mexico | Spanish (Mexican) | Largest US outbound destination with a non-English language |
| Italy | Italian | Top European destination |
| France | French | Top European destination |
| Spain | Spanish (Castilian) | Shows the per-country rule against Mexico |
| Germany | German | Top European destination |
| Japan | Japanese | Non-Latin script; the hardest test of the reading primer |
| Iceland | Icelandic | Unusual letters (þ, ð, æ); the "horses, not ponies" tip |
| Greece | Greek | Second non-Latin script |

Countries where English is the main language still benefit from the primary briefing,
playbooks, routes and traveler research. Their language toolkit can be a short `words that
differ` and signs list rather than an artificial 50-phrase course.

## What success looks like

The app collects no analytics, so v1 success is measured only from sources that already
exist:

| Measure | Source | Target for the first 90 days |
|---|---|---|
| Store rating | Play Console | ≥ 4.5 |
| Installs that download at least one pack | Not measurable without telemetry; see open question 5 | — |
| Crash-free users | Play Console vitals | ≥ 99.5% |
| Review themes | Play reviews, tagged by hand monthly | "it worked on the plane" ≥ "missing X" |

Before launch: moderated tests with at least 8 US travelers. Each receives realistic planning
and arrival decisions and must find options, trade-offs, preparation steps, uncertainty and a
next action quickly. Language tasks—greet, thank, order a drink, find the toilet and show an
address—are tested separately for users who use the toolkit. Exact acceptance criteria live in
the editorial verification skill and the eventual execution plan.

## Roadmap

1. **v1**: Android, research-backed briefing packs, playbooks, routes, places, phrasebook,
   Show a local, optional practice, quiet mode and Saved. The guide reader uses reviewed
   semantic HTML in a restricted offline WebView; navigation, downloads, settings, saved state,
   language tools and practice remain native.
2. **v1.1**: more audience/trip-mode lenses and packs by demand.
3. **v2**: iOS (see open question 1); interface languages beyond US English (the
   phrase meanings and tips are translated, the transcriptions re-written per source language).
4. **Later**: city packs (Tokyo, Paris) layered on a country pack; regional phrase variants;
   user-suggested tips with editorial review.

## Open questions

1. **Android first, or iOS too?** The `card_games` stack is Android-only (Kotlin, Compose), and
   reusing it is the reason to start there. But iPhones are over half of US smartphones, and the
   target user is American. Options: ship Android v1 and follow with iOS, or build on Compose
   Multiplatform from the start, which reuses the Kotlin code but not the Android-only parts of
   `card_games` `core/ui`.
2. **Pack delivery**: self-hosted static files (recommended in
   [ARCHITECTURE.md](ARCHITECTURE.md)) or Play Asset Delivery (no server, but content updates
   require an app release, and its library is outside the Apache/MIT/BSD license rule).
3. **Launch set**: confirm the 8 countries above.
4. **Business model**: the whole app free, one free pack then paid packs, or a one-time unlock.
   Paid packs need Play Billing, which is network and a new dependency.
5. **Measurement**: keep zero analytics (and accept not knowing pack-download or completion
   rates), or add a single anonymous count per pack download at the pack host (server-side,
   from download logs only, no device identifier).
6. **Audio recording**: budget for native speakers per country (about 150 short clips each at
   two speeds), or allow reviewed neural TTS for first drafts. [CONTENT.md](CONTENT.md) requires
   human recordings for release.
7. **Name**: **First Day Away** is the selected name. Complete trademark clearance and Play Store availability checks before launch.
