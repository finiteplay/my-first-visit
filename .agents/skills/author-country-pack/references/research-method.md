# Traveler research method

Use this reference for a new country, a substantial refresh, or a topic whose current evidence
is weak or disputed.

## 1. Frame the traveler

Record the destination, audience origin, likely first-timer status, season range, trip length,
budget/comfort range, mobility needs and relevant trip modes. One shared destination dossier
may feed several audience or trip-style lenses.

## 2. Discover topics broadly

Search recent firsthand material before deciding the table of contents. Useful query families
include:

- `<destination> trip report <year>`
- `<destination> first trip wish I knew`
- `<destination> mistake regret surprise`
- `<destination> worth it overrated underrated`
- `<destination> no car / self drive / family / solo / accessibility`
- `<destination> campervan / motorhome / RV / train / bus / ferry / cruise / bicycle / walking`
- `<destination> winter / summer / shoulder season`
- a discovered topic plus `experience`, `claim`, `problem`, or `trip report`

Sample across at least three independent traveler communities for a full dossier. Depending on
the destination, these may include Reddit travel communities, Tripadvisor forums/reviews, the
Rick Steves Travel Forum, regional communities, accessibility/family forums and detailed trip
reports. Treat each as a distinct sample with its own audience and moderation bias, not as a
representative survey. Include positive reports, ordinary uneventful trips and dissatisfied
reports; problem-only searches create a distorted corpus. Add recent travel programs, guides
and blogs—including locally popular travel media—for topic discovery and presentation ideas.
Use official and provider sources to verify the claims within their scope.

### Travel-mode discovery pass

Do not declare modes from a reusable car-versus-tour list. Start with broad “how people travel”
queries, inspect recent trip reports, and follow destination-specific language that appears.
Candidate modes can include car plus fixed lodging, compact campervan, larger motorhome, guided
tour, public transport, rail pass, ferry, cruise, domestic flight, bicycle or walking route.
These are discovery prompts, not required categories.

Keep a mode distinct when it materially changes lodging, route flexibility, daily chores,
reservations, cost, accessibility, safety or legal rules. For each candidate, record:

- evidence that real travelers use or seriously consider it;
- traveler fit and the experience people hope to gain;
- advantages and ordinary frictions, including positive and disappointing accounts;
- seasonal and geographic limits;
- official or provider checks; and
- whether it is primary, supporting or excluded from this pack, with a reason.

Also scan itinerary shape independently of transport. Research whether travelers commonly use
one base, two regional bases, frequent lodging changes or a continuous circuit, and capture the
real trade-offs: packing and recovery versus backtracking, return-drive fatigue and geographic
reach. A Reykjavík base with tours and a South Coast base with a car may share the same useful
planning principle even though their transport differs.

Do not call a mode popular from forum counts. Say it recurs in the researched corpus unless an
appropriate market or official source supports a stronger prevalence claim.

## 3. Capture independent accounts

Create `content/<cc>/research/corpus.csv` using
[the dossier schema](dossier-schema.md). One row represents one independently attributable
account or source. Multiple people in one thread may be separate rows with the same URL. Do not
count a repost, quotation or copied article as independent evidence.

Paraphrase the relevant observation in `notes`; preserve the URL and dates. Use `unknown` when
traveler context is genuinely unavailable rather than inferring identity or circumstances.

For a full first pass, collect at least 30 relevant firsthand accounts and expect 50–100 for a
complex destination. Keep the majority within 24 months. Expand high-impact, disputed or
underrepresented topics rather than filling a numeric quota with redundant posts.

## 4. Build topics and contradictions

Create `content/<cc>/research/dossier.yaml` using the JSON subset of YAML. Each core topic must
state the user's decision, its signal strength, sources, anecdotes, synthesis, limitations and
needed live checks.

Use these signal values:

- `repeated`: recurring independent reports across communities;
- `split`: credible outcomes or recommendations differ;
- `emerging`: useful but currently thin evidence;
- `single-anecdote`: valuable color, explicitly not a pattern.

For `split`, record the meaningful stances rather than forcing a winner. Seek contextual causes:
season, route, provider, preparation, traveler origin, budget, ability, risk tolerance and luck.

## 5. Verify by source role

Traveler stories answer `what happened to someone like me?` Official sources answer current
rules and procedures. Provider terms answer what that provider promised on that date. Travel
media answer what may be important or engaging. No role substitutes for another.

Safety, health, emergency, legal and insurance topics need an authoritative, specialist or
provider-specific source. Preserve an accessed date and make changing instructions a live
handoff instead of permanent offline advice.

## 6. Decide when to stop

Research in meaningfully different batches: another community, traveler profile, season or
trip mode. Continue if a core topic has one community, one viewpoint, unexplained disagreement,
missing context, or a required verification gap.

A cycle may stop when:

- two consecutive different batches add no new high-impact topic or decision factor;
- every core topic has evidence from at least two traveler communities;
- split topics preserve real contrasting perspectives;
- sensitive topics have the required non-forum verification;
- gaps are explicitly recorded.

This is corpus saturation, not a claim of statistical representativeness.
