(() => {
  "use strict";

  const data = window.ICELAND_CONTENT;
  // Only content-author-selected photos (content/is/photos.json) are shown; every other place
  // stays in an explicit pending state rather than showing an unselected or unrelated image.
  const selectedPhotos = data.photos || {};
  const placeAudio = Object.fromEntries(Object.values(data.placeAudio?.items || {}).filter(entry => entry.showInApp).map(entry => [entry.local, entry]));
  const audioControls = local => {
    const clip = placeAudio[local];
    if (!clip) return `<button class="audio-placeholder" type="button" disabled aria-label="Play ${escapeHtml(local)}">▶ <span>audio placeholder</span></button>`;
    const button = (take, label) => `<button class="audio-play" type="button" data-audio="${escapeHtml(clip.files[take].file)}" aria-label="${label} pronunciation of ${escapeHtml(local)}">▶ ${label}</button>`;
    return `<span class="audio-controls">${button("normal", "Play")}<span class="audio-note">draft synthetic voice</span></span>`;
  };
  const photoAlt = (item, index) => `${item.name}${index ? `, photo ${index + 1}` : ""}`;
  const photoCredit = photo => `${photo.author} · ${photo.license} · ${photo.source}`;
  const photoStyle = photo => photo.objectPosition === "contain"
    ? "object-fit:contain" : `object-position:${photo.objectPosition || "center"}`;
  const placeRank = {
    "sight-perlan": 1, "sight-thingvellir": 2, "sight-gullfoss": 3, "sight-geysir": 4,
    "sight-skogafoss": 5, "sight-harpa": 6, "sight-hallgrimskirkja": 7, "sight-whales": 8,
    "sight-mink": 9, "sight-laugardalslaug": 10, "sight-national-museum": 11,
    "sight-seljalandsfoss": 12, "sight-reynisfjara": 13, "sight-jokulsarlon": 14,
    "sight-godafoss": 15, "sight-myvatn": 16, "sight-aurora-reykjavik": 17, "sight-flyover": 18
  };
  const placeDetails = {
    "sight-perlan": "Perlan is the easy Reykjavík answer when the weather is doing something difficult. The museum brings glaciers, volcanoes, caves and northern lights into one building, then sends you upstairs for a wide view over the city and bay. Tripadvisor currently places it among Reykjavík’s highest-ranked attractions, but the real reason to go is that it gives a first-time visitor a useful mental map of Iceland before heading out.\n\nAllow a few hours if you want the exhibitions and observation deck rather than a quick photograph. It is not a substitute for seeing the landscape itself, but it is a warm, well-organized introduction and a good rainy-day plan.",
    "sight-harpa": "Harpa is worth seeing even if you are not going to a concert. Walk around the glass façade, look back toward the water, and take a few minutes inside to notice how the light changes through the geometric panels. It feels grand without requiring a whole afternoon.\n\nThis is also a useful place to build a small harbor afternoon. Whales of Iceland, the Aurora Reykjavík experience and FlyOver Iceland are nearby and can be combined on foot in a couple of hours, depending on opening times and how long you linger. Check the walking route and book timed attractions ahead when possible.",
    "sight-whales": "Whales of Iceland is an indoor museum with life-size models of whales found in Icelandic waters. It is more about scale and curiosity than a live-animal encounter, which makes it a thoughtful companion to a whale-watching boat trip or a rainy afternoon. Travelers often like the way the models make field-guide names suddenly memorable.\n\nPair it with Harpa and the other harbor attractions rather than treating it as a cross-country detour. Tripadvisor reviews are mixed on value, so decide whether the subject interests you; people who love whales tend to find the 1–2 hour visit worthwhile.",
    "sight-aurora-reykjavik": "Aurora Reykjavík is a compact, indoors introduction to the northern lights: photographs, explanations and practical context for why forecasts can promise conditions without promising a show. It helps set expectations before you join a night tour.\n\nTreat it as a short experience, not proof that you have ‘seen the aurora’. The harbor location makes it easy to combine with Harpa and Whales of Iceland, and it is especially convenient when clouds or wind make an outdoor evening unpleasant.\n\nWhat the operator describes: the museum is at Fiskislóð 53 in the Grandi harbor area, about a ten-minute walk from downtown. The exhibition covers mythology, science, solar cycles, photography and aurora-hunting tips, with a 360-degree VR aurora experience and a 30-minute film. A visit typically takes 45 to 60 minutes, it is open daily all year (check the seasonal hours) and it is described as fully accessible with free parking. The same company sells aurora tours in season, so treat its tour pitch as an operator's.",
    "sight-flyover": "FlyOver Iceland is a theatrical flying-ride experience rather than a real sightseeing flight. You are suspended in front of a large screen with wind, mist and movement, so it can be a fun way to preview the country’s scale when you have limited time or poor weather.\n\nSome travelers love the immersive sensation; others prefer spending the ticket on an actual viewpoint. Decide based on whether you want a polished attraction or a quieter museum, and reserve a time if it is part of your harbor walk.",
    "sight-mink": "Mink Viking Portrait Studio is one of Reykjavík’s more memorable small-group experiences. You are dressed and photographed in a deliberately theatrical Viking style, with staff guiding the pose and story rather than asking you to perform alone. It is playful, personal and very different from a standard museum visit.\n\nBook ahead and check exactly what the session includes, especially image delivery and timing. Tripadvisor currently shows it as one of the city’s highest-rated fun-and-games experiences, but the appeal depends on enjoying a staged portrait and committing to the joke.",
    "sight-laugardalslaug": "Laugardalslaug is a lovely way to begin understanding Reykjavík as a place where people live, not only a launchpad for excursions. The pool, hot tubs and changing-room routine are part of an ordinary local rhythm, and a slow soak can reset you after a flight or a long drive.\n\nRead the shower instructions and bring a towel plan. It is not a sightseeing checklist item; it is better when you give yourself enough time to relax, notice the etiquette and let the weather be part of the experience.",
    "sight-thingvellir": "Þingvellir combines a dramatic rift landscape with the story of Iceland’s early assembly. The paths make the geology legible: you can see where the land is pulling apart while walking through a place that carries unusual historical weight.\n\nIt is often the first substantial stop on a Golden Circle day, so arrive with enough time to walk rather than only photograph the parking area. Weather can change quickly, and the marked paths are part of the visit, not an inconvenience.",
    "sight-gullfoss": "Gullfoss is powerful in a way photographs rarely capture: the river seems to disappear into the canyon and the spray reaches you before you understand the scale. The two-stage drop makes the viewpoint feel active and changeable rather than like a single static waterfall.\n\nGive yourself time to watch the water and keep behind barriers. Wind, spray and winter ice can make the lower approaches uncomfortable or unavailable, so the safest viewpoint is still a worthwhile visit.",
    "sight-geysir": "The Geysir area gives you a quick lesson in Iceland’s restless ground. Strokkur erupts regularly enough that you can wait without turning the stop into an all-day gamble, while the steaming pools and smell of sulfur make the whole site feel alive between eruptions.\n\nPeople sometimes arrive expecting Great Geysir itself to erupt on cue. Think of Strokkur as the dependable show and stay behind the ropes; the ground around hot springs is not a place to improvise a closer photograph.",
    "sight-skogafoss": "Skógafoss is one of those waterfalls that rewards both the quick stop and the longer pause. From the base, the wall of water and spray can make a sunny day feel theatrical; from above, the stairs give you a different sense of the river’s route.\n\nYou do not need to climb to enjoy it. If the steps are wet, windy or crowded, stay below and watch how the light changes in the mist.",
    "sight-national-museum": "The National Museum helps put names and dates behind the landscapes you will be seeing. A few objects can turn a drive past a farm, church or fishing village into a story about settlement, work and survival rather than a series of pretty views.\n\nIt is a good choice when you want context without committing to a full day indoors. Pick a small number of rooms to explore slowly and check the museum’s photography rules before lifting your camera.",
    "sight-reynisfjara": "Reynisfjara is beautiful precisely because it feels elemental: black sand, basalt columns, surf and offshore stacks. It is also the place where Iceland’s water deserves more respect than your camera does. Sneaker waves can reach much farther than the calm water suggests.\n\nStay well back from the sea, follow warning signs and never let a dramatic photograph pull you toward the waterline. A shorter, safer visit is still a successful visit.",
    "sight-jokulsarlon": "Jökulsárlón is a major journey from Reykjavík, but the drifting ice makes the distance feel earned. Pieces of glacier move slowly through the lagoon toward the ocean, and the scene keeps changing while you stand there.\n\nPlan it as part of a Southeast overnight route rather than squeezing it into an exhausting day trip. You can have a memorable visit from shore; climbing on ice or approaching the water is neither necessary nor safe.",
    "sight-seljalandsfoss": "Seljalandsfoss is famous for the path behind the falling water, but the front view is already beautiful and often more comfortable. The green cliff and narrow ribbon of water make it feel almost like a stage set, especially when the weather moves through.\n\nBring waterproof layers and treat the rear path as conditional. Ice, spray and falling material can close it, and a closure is a safety decision rather than a challenge to solve.",
    "sight-petras-stone-collection": "Petra’s Stone Collection is a small museum with a personal story. Ljósbjörg Petra María Sveinsdóttir (1922–2012) began collecting stones in 1946 and opened her home to visitors in 1974; the house and garden in Stöðvarfjörður still show thousands of specimens, including zeolites, agates, jasper and quartz. It is often described as one of the largest private stone collections in the world, which is a claim to enjoy rather than a fact to repeat.\n\nTreat it as a gentle one-to-two-hour stop on the Eastfjords leg of the Ring Road, with a garden to wander and a café. It is a seasonal museum open in the summer months and sources give slightly different closing dates, so check before you build a day around it. The village is tiny, so it is a good place to slow down.",
    "sight-vok-baths": "Vök Baths is a geothermal spa on the shore of Lake Urriðavatn, a few minutes from Egilsstaðir. Its floating pools give an infinity view over the lake, and the rest is a gentle circuit: two hot pools on the shore, a sauna, a cold-water spray tunnel, a cold plunge, a tea bar and a pool bar in the water. The operator says it uses natural geothermal water with no chemicals. The name is the Icelandic word for a hole in lake ice, which is a fair description of the idea.\n\nPlan it as an end-of-day soak on the East Iceland leg, not as a reason to drive across the island. It is smaller and calmer than the big lagoons in the southwest. Check the opening hours and how to book before you go: when we looked, the operator asked for reservations by email. Follow the shower rules, and ask what is included before you pack towels.",
    "sight-godafoss": "Goðafoss is a broad, graceful waterfall that fits naturally into a North Iceland day around Akureyri or Mývatn. Its curved shape gives you several viewpoints, so you can spend a little time finding the angle that shows the river’s width.\n\nWet rock and winter ice can make the edges deceptive. Stay on marked approaches and let the waterfall come to you instead of trying to stand nearest the brink.",
    "sight-myvatn": "The Mývatn area is best understood as a collection of volcanic landscapes rather than one single attraction. Lava formations, pseudocraters, birdlife and geothermal stops reward a day with a little breathing room.\n\nChoose a few stops instead of racing around the lake. In summer, midges are a practical annoyance rather than a reason to skip the area; a head net or face covering can make the difference.",
    "sight-hallgrimskirkja": "Hallgrímskirkja is Reykjavík’s visual anchor, visible from many streets before you reach it. The stepped concrete form is inspired by Icelandic landscape, and the quiet interior gives the building a very different mood from the busy square outside.\n\nTreat it as an active church first. Check tower access and visiting hours, keep your voice down during services and take a moment to look outward from the surrounding streets as well as upward at the façade."
  };
  const playbookGrid = document.querySelector("#playbook-grid");
  const routeList = document.querySelector("#route-list");
  const placeGrid = document.querySelector("#place-grid");
  const reader = document.querySelector("#reader");
  const article = document.querySelector("#reader-article");
  const escapeHtml = (value = "") => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);

  function summary(item) {
    const value = item.body || item.hook || item.whyItWorks || item.whyGo || "";
    return Array.isArray(value) ? value[0] : value;
  }

  function renderPlaybooks(filter = "all") {
    const items = data.playbooks.filter(item => filter === "all" || (item.fits || []).includes(filter));
    playbookGrid.innerHTML = items.map(item => `
      <article class="guide-card">
        ${item.cardImage ? `<img class="card-image" src="${escapeHtml(item.cardImage.src)}" alt="${escapeHtml(item.cardImage.alt)}" width="1440" height="960" loading="lazy">` : ""}
        <div class="meta"><span>${escapeHtml((item.fits || ["Advice"])[0].replaceAll("-", " "))}</span><span>·</span><span>${escapeHtml(item.readingMinutes)} min read</span></div>
        <h3>${escapeHtml(item.title)}</h3>
        <p>${escapeHtml(summary(item))}</p>
        <button class="text-button" type="button" data-open="playbook:${escapeHtml(item.id)}">Read this advice <span aria-hidden="true">→</span></button>
      </article>`).join("");
  }

  function renderRoutes() {
    routeList.innerHTML = data.routes.map((item, index) => `
      <button class="route-row" type="button" data-open="route:${escapeHtml(item.id)}">
        <span class="number">0${index + 1}</span>
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.duration)}</span>
        <span class="arrow" aria-hidden="true">↗</span>
      </button>`).join("");
  }

  // Priority for a first visit comes from each place's `tier`. Words, not stars: every label is a positive
  // recommendation, and the lowest one means "good when you have spare time", not "poor".
  const PRIORITIES = {
    "must-see": { level: 1, label: "Don't miss", icon: "📌" },
    "worth-it": { level: 2, label: "Worth a stop", icon: "🧭" },
    "if-you-have-time": { level: 3, label: "If you have time", icon: "⏳" }
  };
  const priorityOf = item => PRIORITIES[item.tier] || PRIORITIES["if-you-have-time"];
  const priorityHtml = item => {
    const priority = priorityOf(item);
    return `<span class="priority priority-${priority.level}" aria-label="Priority for a first visit: ${priority.label}"><span class="priority-icon" aria-hidden="true">${priority.icon}</span>${priority.label}</span>`;
  };
  let placeCategory = "all";

  function renderPlaceFilters() {
    const host = document.querySelector("#place-filters");
    if (!host) return;
    const counts = data.places.reduce((map, item) => map.set(item.category, (map.get(item.category) || 0) + 1), new Map());
    const categories = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    host.innerHTML = [["all", "All", data.places.length], ...categories.map(([name, count]) => [name, name, count])].map(([value, label, count]) =>
      `<button class="filter${value === placeCategory ? " active" : ""}" type="button" data-category="${escapeHtml(value)}" aria-pressed="${value === placeCategory}">${escapeHtml(label)} <span class="filter-count">${count}</span></button>`).join("");
  }

  function renderPlaces(query = "") {
    const term = query.trim().toLocaleLowerCase();
    const tierOrder = { "must-see": 0, "worth-it": 1, "if-you-have-time": 2 };
    const items = data.places
      .filter(item => placeCategory === "all" || item.category === placeCategory)
      .filter(item => !term || [item.name, item.region, item.category, item.whyGo].join(" ").toLocaleLowerCase().includes(term))
      .sort((a, b) => (tierOrder[a.tier] ?? 3) - (tierOrder[b.tier] ?? 3) || (placeRank[a.id] || 999) - (placeRank[b.id] || 999) || a.name.localeCompare(b.name));
    placeGrid.innerHTML = items.map(item => `
      <article class="place-card" data-open="place:${escapeHtml(item.id)}" tabindex="0" role="button" aria-label="Open place card for ${escapeHtml(item.name)}">
        ${selectedPhotos[item.id]?.length ? `<img class="place-card-image" src="${escapeHtml(selectedPhotos[item.id][0].file)}" alt="${escapeHtml(photoAlt(item, 0))}" style="${escapeHtml(photoStyle(selectedPhotos[item.id][0]))}" width="480" height="320" loading="lazy">` : ""}
        <span class="region">${escapeHtml(item.region)} · ${escapeHtml(item.category)}</span>
        ${priorityHtml(item)}
        <h3>${escapeHtml(item.name)}</h3>
        <p>${escapeHtml(item.whyGo)}</p>
        <span class="time">${escapeHtml(item.timeNeeded)}</span>
      </article>`).join("") || `<p class="place-card">No places match that filter or search.</p>`;
    const count = document.querySelector("#place-count");
    if (count) count.textContent = `${items.length} of ${data.places.length} places`;
  }

  const list = (items, className = "") => items?.length ? `<ul class="${className}">${items.map(value => `<li>${escapeHtml(typeof value === "string" ? value : value.label || value.name)}</li>`).join("")}</ul>` : "";
  const paragraphs = items => (Array.isArray(items) ? items : items ? [items] : []).map(value => `<p>${escapeHtml(value)}</p>`).join("");
  const practiceLink = item => item ? `<div class="practice-link" data-lesson-id="${escapeHtml(item.lessonId)}"><strong>${escapeHtml(item.label)} <span aria-hidden="true">→</span></strong><span>${escapeHtml(item.status)}</span></div>` : "";

  // Live-condition links: the same three official services everywhere they matter.
  const LIVE = {
    weather: { label: "Weather and warnings", url: "https://en.vedur.is/" },
    roads: { label: "Road conditions", url: "https://umferdin.is/en" },
    safetravel: { label: "Safetravel alerts", url: "https://safetravel.is/travel-conditions/" }
  };
  const liveStrip = keys => `<p class="live-strip"><strong>Check today:</strong> ${keys.map(key => `<a href="${escapeHtml(LIVE[key].url)}" target="_blank" rel="noopener">${escapeHtml(LIVE[key].label)}</a>`).join(" · ")}</p>`;
  const liveCheckList = checks => checks?.length ? `<h2>Check live</h2><ul>${checks.map(check => /^https?:/.test(check.url || "")
    ? `<li><a href="${escapeHtml(check.url)}" target="_blank" rel="noopener">${escapeHtml(check.label)} <span aria-hidden="true">↗</span></a></li>`
    : `<li>${escapeHtml(check.label)} <span class="muted">(ask the provider)</span></li>`).join("")}</ul>` : "";

  function briefingHtml(item) {
    return `<p class="article-meta">Destination briefing · ${item.readingMinutes} minutes · ${escapeHtml(item.researchedAsOf)}</p>
      <h1 id="reader-title">${escapeHtml(item.title)}</h1>
      <p class="hook">${escapeHtml(item.hook)}</p>
      <p>${escapeHtml(item.lede)}</p>
      ${item.sections.map(section => `<section><h2>${escapeHtml(section.title)}</h2><p class="article-meta">${escapeHtml(section.evidenceLabel)}</p>${paragraphs(section.body)}${practiceLink(section.practiceLink)}${section.doBeforeDeparture ? `<div class="callout"><strong>Do before departure</strong>${list(section.doBeforeDeparture)}</div>` : ""}${section.liveChecks ? `<div class="callout"><strong>Check live</strong>${list(section.liveChecks)}</div>` : ""}</section>`).join("")}
      <p class="callout"><strong>Keep this:</strong> ${escapeHtml(item.closing)}</p>`;
  }

  function playbookHtml(item) {
    const decisions = item.decision ? Object.entries(item.decision).map(([key, value]) => `<div class="option"><strong>${escapeHtml(key.replace(/([A-Z])/g, " $1"))}</strong><p>${escapeHtml(value)}</p></div>`).join("") : "";
    const options = item.options ? item.options.map(value => `<div class="option"><strong>${escapeHtml(value.name)}</strong><p>${escapeHtml(value.bestFor)}</p><p><em>Trade-off:</em> ${escapeHtml(value.tradeoff)}</p></div>`).join("") : "";
    return `<p class="article-meta">Decision guide · ${item.readingMinutes} minutes · ${escapeHtml(item.evidenceLabel)}</p>
      <h1 id="reader-title">${escapeHtml(item.title)}</h1>
      ${item.hook ? `<p class="hook">${escapeHtml(item.hook)}</p>` : ""}
      ${paragraphs(item.body)}
      ${item.travelerStories?.length ? `<h2>What travelers experienced</h2>${item.travelerStories.map(story => `<blockquote class="story">${escapeHtml(story)}</blockquote>`).join("")}` : ""}
      ${decisions || options ? `<h2>Your options</h2><div class="option-grid">${decisions}${options}</div>` : ""}
      ${item.trackers?.length ? `<h2>Websites that track conditions</h2>${item.trackersIntro ? `<p>${escapeHtml(item.trackersIntro)}</p>` : ""}<div class="option-grid">${item.trackers.map(site => `<div class="option tracker"><strong><a href="${escapeHtml(site.url)}" target="_blank" rel="noopener">${escapeHtml(site.name)} <span aria-hidden="true">↗</span></a></strong><p><em>Shows:</em> ${escapeHtml(site.shows)}</p><p><em>Use it for:</em> ${escapeHtml(site.useItFor)}</p></div>`).join("")}</div>` : ""}
      ${item.whereToSoak?.map(group => `<h2>${escapeHtml(group.group)}</h2><p>${escapeHtml(group.intro)}</p><div class="option-grid">${group.places.map(place => `<div class="option place-entry"><strong>${escapeHtml(place.name)}</strong>${place.local ? `<div class="say-it">${place.local !== place.name ? `<span class="local-name">${escapeHtml(place.local)}</span>` : ""}<span class="respelling" title="Draft respelling; native review pending">${escapeHtml(place.respelling)}</span>${audioControls(place.local)}</div>` : ""}<p class="where">${escapeHtml(place.where)}</p><p>${escapeHtml(place.character)}</p><p><em>Best for:</em> ${escapeHtml(place.bestFor)}</p><p><em>Heads-up:</em> ${escapeHtml(place.headsUp)}</p>${placeLinks(place)}</div>`).join("")}</div>`).join("") || ""}
      ${item.whatToExpect ? `<h2>What to expect</h2><p>${escapeHtml(item.whatToExpect)}</p>` : ""}
      ${item.checklist ? `<h2>Before you go</h2>${list(item.checklist)}` : ""}
      ${item.avoid ? `<h2>Avoid</h2>${list(item.avoid)}` : ""}
      ${liveCheckList(item.liveChecks)}
      ${item.ourTake ? `<div class="callout"><strong>Our take</strong><p>${escapeHtml(item.ourTake)}</p></div>` : ""}
      ${item.warning ? `<div class="callout"><strong>Keep in mind</strong><p>${escapeHtml(item.warning)}</p></div>` : ""}
      ${item.limits ? `<h2>What this evidence cannot tell you</h2><p>${escapeHtml(item.limits)}</p>` : ""}`;
  }

  function routeHtml(item) {
    return `<p class="article-meta">Practical route · ${escapeHtml(item.duration)}</p>
      <h1 id="reader-title">${escapeHtml(item.title)}</h1>
      <p class="hook">${escapeHtml(item.pace)}</p>
      ${liveStrip(["weather", "roads", "safetravel"])}
      ${item.whoFor ? `<p><strong>Who it suits:</strong> ${escapeHtml(item.whoFor)}</p>` : ""}
      ${item.whyItWorks ? `<h2>Why it works</h2><p>${escapeHtml(item.whyItWorks)}</p>` : ""}
      ${item.days?.length ? `<h2>Day by day</h2><div class="option-grid">${item.days.map((day, index) => `<div class="option route-day"><strong>Day ${index + 1}${day.flexible ? " · flexible" : ""}</strong><p class="where">Sleep: ${escapeHtml(day.base)}</p><p><em>Getting around:</em> ${escapeHtml(day.travel)}</p>${list(day.highlights)}${day.placeIds?.length ? `<p class="route-places">${day.placeIds.map(id => { const place = data.places.find(p => p.id === id); return place ? `<button type="button" class="place-chip" data-open="place:${escapeHtml(id)}">${escapeHtml(place.name)}</button>` : ""; }).join("")}</p>` : ""}${day.weatherSwap ? `<p><em>If the weather turns:</em> ${escapeHtml(day.weatherSwap)}</p>` : ""}${day.ifTired ? `<p><em>If you are tired:</em> ${escapeHtml(day.ifTired)}</p>` : ""}</div>`).join("")}</div><p class="article-meta">Drive times are planning estimates unless marked official; confirm them on a live map.</p>` : ""}
      ${item.seasonNotes ? `<h2>How the season changes it</h2><p>${escapeHtml(item.seasonNotes)}</p>` : ""}
      ${item.tradeoff ? `<h2>The trade-off</h2><p>${escapeHtml(item.tradeoff)}</p>` : ""}
      ${item.skipIf ? `<div class="callout"><strong>Skip it if</strong><p>${escapeHtml(item.skipIf)}</p></div>` : ""}
      ${item.limits ? `<h2>What this route cannot tell you</h2><p>${escapeHtml(item.limits)}</p>` : ""}
      ${item.safety ? `<div class="callout"><strong>Safety boundary</strong><p>${escapeHtml(item.safety)}</p></div>` : ""}
      ${liveCheckList(item.liveChecks)}`;
  }

  // Where a place is: a Google Maps link plus a small map with one dot. Places near the capital use
  // the local outline from map.yaml `regions`; everything else uses the country outline.
  const mapsUrl = item => `https://www.google.com/maps/search/?api=1&query=${item.location.latitude},${item.location.longitude}`;
  const kmBetween = (lon1, lat1, lon2, lat2) => {
    const rad = Math.PI / 180, dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(a));
  };

  function placeMinimap(item) {
    const map = data.map, loc = item.location;
    if (!map?.outline || !loc) return "";
    const region = (map.regions || []).find(r => kmBetween(loc.longitude, loc.latitude, r.center[0], r.center[1]) <= r.radiusKm);
    const W = region ? 520 : 400, PAD = region ? 0 : 20;
    let west, south, east, north, rings, K, context = "", areaName;
    if (region) {
      [west, south, east, north] = region.bbox;
      rings = region.land;
      K = Math.cos(region.center[1] * Math.PI / 180);
      areaName = region.title;
    } else {
      const lons = map.outline.map(p => p[0]), lats = map.outline.map(p => p[1]);
      west = Math.min(...lons); east = Math.max(...lons); south = Math.min(...lats); north = Math.max(...lats);
      rings = [map.outline];
      K = Math.cos(65 * Math.PI / 180);
      areaName = "Iceland";
    }
    const scale = (W - 2 * PAD) / ((east - west) * K);
    const H = Math.round((north - south) * scale + 2 * PAD);
    const x = lon => (lon - west) * K * scale + PAD, y = lat => (north - lat) * scale + PAD;
    const path = points => points.map((p, i) => `${i ? "L" : "M"}${x(p[0]).toFixed(1)} ${y(p[1]).toFixed(1)}`).join(" ");
    if (region) {
      context = data.places.filter(p => p.id !== item.id && p.location && p.location.longitude >= west && p.location.longitude <= east && p.location.latitude >= south && p.location.latitude <= north)
        .map(p => `<circle class="minimap-other" cx="${x(p.location.longitude).toFixed(1)}" cy="${y(p.location.latitude).toFixed(1)}" r="4.5"/>`).join("");
    } else {
      const ring = (map.lines || []).find(l => l.style === "ring");
      if (ring) context = `<path class="minimap-road" d="${path(ring.points)}"/>`;
    }
    const cx = x(loc.longitude), cy = y(loc.latitude);
    const anchor = cx > W * 0.6 ? "end" : "start";
    const lx = cx + (anchor === "end" ? -14 : 14), ly = Math.min(Math.max(cy + 5, 18), H - 8);
    const credit = region ? region.credit : map.credit;
    return `<div class="place-where">
      <h2>Where it is</h2>
      <figure class="minimap">
        <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${escapeHtml(item.name)} on a small map of ${escapeHtml(areaName)}">
          <rect class="minimap-sea" width="${W}" height="${H}"/>
          <path class="minimap-land" d="${rings.map(r => path(r) + "Z").join(" ")}"/>
          ${context}
          <circle class="minimap-halo" cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="15"/>
          <circle class="minimap-dot" cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="7.5"/>
          <text class="minimap-label" x="${lx.toFixed(1)}" y="${ly.toFixed(1)}" text-anchor="${anchor}">${escapeHtml(item.local)}</text>
        </svg>
        <figcaption>${escapeHtml(areaName)}. Approximate position, not for navigation. ${escapeHtml(credit)}</figcaption>
      </figure>
      <p class="place-links"><a class="maps-link" href="${escapeHtml(mapsUrl(item))}" target="_blank" rel="noopener">Open ${escapeHtml(item.local)} in Google Maps <span aria-hidden="true">↗</span></a>${item.website ? `<a class="maps-link" href="${escapeHtml(item.website.url)}" target="_blank" rel="noopener">${escapeHtml(item.website.label)} <span aria-hidden="true">↗</span></a>` : ""}</p>
    </div>`;
  }

  // Maps and website links for a soak/lagoon entry (pins come from the entry's own `location`).
  const placeLinks = place => {
    const links = [];
    if (place.location) links.push(`<a class="maps-link" href="${escapeHtml(mapsUrl({ location: place.location }))}" target="_blank" rel="noopener">${place.location.mapNote ? "Google Maps: trailhead" : "Google Maps"} <span aria-hidden="true">↗</span></a>`);
    if (place.website) links.push(`<a class="maps-link" href="${escapeHtml(place.website.url)}" target="_blank" rel="noopener">${escapeHtml(place.website.label)} <span aria-hidden="true">↗</span></a>`);
    return links.length ? `<p class="place-links">${links.join("")}</p>${place.location?.mapNote ? `<p class="map-note">${escapeHtml(place.location.mapNote)}</p>` : ""}` : "";
  };

  function placeHtml(item) {
    const gallery = selectedPhotos[item.id] || [];
    const photo = gallery[0];
    const detail = Array.isArray(item.description) ? item.description.join("\n\n") : (item.description || placeDetails[item.id] || item.whyGo);
    const detailParagraphs = detail.split(/\n\n/).map(value => `<p class="place-description">${escapeHtml(value)}</p>`).join("");
    return `<p class="article-meta">Place card · ${escapeHtml(item.region)} · ${escapeHtml(item.category)}</p>
      ${photo ? `<figure class="place-photo"><div class="photo-carousel" data-carousel><button type="button" class="carousel-arrow prev" aria-label="Previous photo">‹</button><div class="carousel-track">${gallery.map((image, index) => `<img class="carousel-image${index === 0 ? " active" : ""}" src="${escapeHtml(image.file)}" alt="${escapeHtml(photoAlt(item, index))}" style="${escapeHtml(photoStyle(image))}" width="1440" height="960" ${index ? "loading=\"lazy\"" : ""}>`).join("")}</div><button type="button" class="carousel-arrow next" aria-label="Next photo">›</button></div><figcaption>${gallery.map((image, index) => `<a href="${escapeHtml(image.sourceUrl)}" rel="noopener">Photo ${index + 1}</a>: ${escapeHtml(photoCredit(image))}`).join(" · ")}</figcaption></figure>` : `<div class="place-photo-placeholder" role="img" aria-label="Photo placeholder for ${escapeHtml(item.name)}"><span>Photo placeholder</span><small>Rights-cleared destination photo to be added</small></div>`}
      <h1 id="reader-title">${escapeHtml(item.name)}</h1>
      <div class="name-toolkit">
        <div><span class="name-label">Local name</span><strong>${escapeHtml(item.local)}</strong></div>
        <div><span class="name-label">Say it like this for now</span><strong>${escapeHtml(item.respelling)}</strong></div>
        ${audioControls(item.local)}
      </div>
      <p class="place-rating"><strong>Priority for a first visit:</strong> ${priorityHtml(item)}</p>
      ${placeRank[item.id] ? `<p class="place-rank"><strong>Suggested order:</strong> #${placeRank[item.id]} in this starter list</p>` : ""}
      ${detailParagraphs}
      <p class="place-time"><strong>Time to allow:</strong> ${escapeHtml(item.timeNeeded)}</p>
      ${placeMinimap(item)}
      ${liveStrip(["weather"].concat(item.region === "Capital area" ? [] : ["roads"], item.category === "Nature" ? ["safetravel"] : []))}
      <div class="callout"><strong>Photo and audio status</strong><p>${photo ? "This destination-specific photo is a licensing candidate and still needs final rights, accuracy and accessibility review." : "No destination-specific photo is bundled yet. This card intentionally remains an explicit pending state rather than showing an unrelated image."}${placeAudio[item.local] ? ` Pronunciation audio is a draft synthetic voice, not a native-speaker recording, and has not had native review. ${escapeHtml(data.placeAudio.credit)}.` : " Pronunciation audio is not available yet; the control is a placeholder until a native recording or approved voice is added."}</p></div>`;
  }

  function openReader(type, id) {
    const groups = { briefing: data.briefings, playbook: data.playbooks, route: data.routes, place: data.places };
    const item = groups[type]?.find(value => value.id === id);
    if (!item) return;
    article.innerHTML = type === "briefing" ? briefingHtml(item) : type === "playbook" ? playbookHtml(item) : type === "route" ? routeHtml(item) : placeHtml(item);
    reader.showModal();
    article.scrollTop = 0;
    reader.scrollTop = 0;
  }

  document.addEventListener("click", event => {
    const arrow = event.target.closest("[data-carousel] .carousel-arrow");
    if (arrow) {
      const carousel = arrow.closest("[data-carousel]");
      const images = [...carousel.querySelectorAll(".carousel-image")];
      const current = images.findIndex(image => image.classList.contains("active"));
      const next = (current + (arrow.classList.contains("next") ? 1 : -1) + images.length) % images.length;
      images.forEach((image, index) => image.classList.toggle("active", index === next));
      if (images[0].getAttribute("src") === "assets/perlan-building-1.jpg") {
        const author = next === 2 ? "Tony Hisgett · CC BY 2.0" : "Ray Swi-hymn · CC BY-SA 2.0";
        const source = next === 2 ? "Perlan_Reykjavik_2_(25474770205).jpg" : next === 1 ? "20190623_Perlan_8867_(48469993062).jpg" : "20190623_Perlan_8866_(48469844986).jpg";
        carousel.parentElement.querySelector("figcaption").innerHTML = `${author} · <a href="https://commons.wikimedia.org/wiki/File:${source}" target="_blank" rel="noopener">Source</a> · <a href="https://creativecommons.org/licenses/${next === 2 ? "by" : "by-sa"}/2.0/" target="_blank" rel="noopener">License</a> · resized; display cropped`;
      }
      return;
    }
    const opener = event.target.closest("[data-open]");
    if (opener) openReader(...opener.dataset.open.split(":"));
  });
  document.addEventListener("keydown", event => {
    const place = event.target.closest(".place-card");
    if (place && (event.key === "Enter" || event.key === " ")) { event.preventDefault(); openReader(...place.dataset.open.split(":")); }
  });
  document.querySelector(".reader-close").addEventListener("click", () => reader.close());
  reader.addEventListener("click", event => { if (event.target === reader) reader.close(); });
  document.querySelectorAll(".filter").forEach(button => button.addEventListener("click", () => {
    document.querySelectorAll(".filter").forEach(item => item.classList.toggle("active", item === button));
    renderPlaybooks(button.dataset.filter);
  }));
  document.querySelector("#place-search").addEventListener("input", event => renderPlaces(event.target.value));
  document.querySelector("#place-filters")?.addEventListener("click", event => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    placeCategory = button.dataset.category;
    renderPlaceFilters();
    renderPlaces(document.querySelector("#place-search").value);
  });
  document.querySelector(".theme-button").addEventListener("click", () => document.body.classList.toggle("night"));
  document.querySelector(".menu-button").addEventListener("click", event => {
    const nav = document.querySelector("#primary-nav");
    const open = nav.classList.toggle("open");
    event.currentTarget.setAttribute("aria-expanded", String(open));
  });
  document.querySelectorAll("#primary-nav a").forEach(link => link.addEventListener("click", () => document.querySelector("#primary-nav").classList.remove("open")));
  addEventListener("scroll", () => document.querySelector(".site-header").classList.toggle("scrolled", scrollY > 30), { passive: true });

  function renderMap() {
    const map = data.map;
    const host = document.querySelector("#basics-map");
    if (!map?.outline || !host) return;
    const K = Math.cos(65 * Math.PI / 180), W = 1000, PAD = 28;
    const lons = map.outline.map(p => p[0]), lats = map.outline.map(p => p[1]);
    const lonMin = Math.min(...lons), lonMax = Math.max(...lons), latMin = Math.min(...lats), latMax = Math.max(...lats);
    const scale = (W - 2 * PAD) / ((lonMax - lonMin) * K);
    const H = Math.round((latMax - latMin) * scale + 2 * PAD);
    const x = lon => ((lon - lonMin) * K * scale + PAD).toFixed(1);
    const y = lat => ((latMax - lat) * scale + PAD).toFixed(1);
    const path = points => points.map((p, i) => `${i ? "L" : "M"}${x(p[0])} ${y(p[1])}`).join(" ");
    const marker = point => {
      const cx = +x(point.lon), cy = +y(point.lat);
      const shape = {
        town: `<circle class="mk-town" cx="${cx}" cy="${cy}" r="7"/>`,
        gc: `<circle class="mk-gc" cx="${cx}" cy="${cy}" r="5.5"/>`,
        glacier: `<circle class="mk-glacier" cx="${cx}" cy="${cy}" r="9"/><path class="mk-glacier-x" d="M${cx - 4.5} ${cy}h9M${cx} ${cy - 4.5}v9M${cx - 3.2} ${cy - 3.2}l6.4 6.4M${cx + 3.2} ${cy - 3.2}l-6.4 6.4"/>`,
        "glacier-lagoon": `<rect class="mk-lagoon" x="${cx - 6}" y="${cy - 6}" width="12" height="12" rx="2"/>`,
        volcano: `<path class="mk-volcano" d="M${cx} ${cy - 10} L${cx + 9} ${cy + 7} L${cx - 9} ${cy + 7} Z"/>`
      }[point.kind] || "";
      const label = `<text class="map-label ${point.kind}" x="${(+cx + point.dx).toFixed(1)}" y="${(+cy + point.dy).toFixed(1)}" text-anchor="${point.anchor}">${escapeHtml(point.label)}</text>`;
      return shape + label;
    };
    const line = item => `<path class="map-line ${escapeHtml(item.style)}" d="${path(item.points)}"/>`;
    const legend = map.legend.map(entry => `<li><span class="lg lg-${escapeHtml(entry.kind)}" aria-hidden="true"></span>${escapeHtml(entry.label)}</li>`).join("");
    const byKind = kind => map.points.filter(p => p.kind === kind).map(p => p.label).join(", ");
    host.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="map-title map-desc">
        <title id="map-title">${escapeHtml(map.title)}</title>
        <desc id="map-desc">Schematic map of Iceland showing the Ring Road, the Golden Circle, main towns, glaciers, a glacier lagoon and the volcano Eyjafjallajökull.</desc>
        <path class="map-land" d="${path(map.outline)}Z"/>
        ${map.lines.filter(l => l.style === "ring").map(line).join("")}
        ${map.lines.filter(l => l.style === "golden").map(line).join("")}
        ${map.points.map(marker).join("")}
      </svg>
      <ul class="map-legend" aria-label="Map legend">${legend}</ul>
      <figcaption id="map-caption">${escapeHtml(map.intro)}</figcaption>
      <details class="map-text">
        <summary>Map as text</summary>
        <p><strong>Ring Road:</strong> ${escapeHtml(map.lines[0].label)}, circling the island through ${escapeHtml(byKind("town"))}.</p>
        <p><strong>Golden Circle:</strong> ${escapeHtml(map.lines[1].label)}, from Reykjavík to ${escapeHtml(byKind("gc"))} and back.</p>
        <p><strong>Glaciers:</strong> ${escapeHtml(byKind("glacier"))}. <strong>Glacier lagoon:</strong> ${escapeHtml(byKind("glacier-lagoon"))}. <strong>Volcano:</strong> ${escapeHtml(byKind("volcano"))}.</p>
        <p class="map-credit">${escapeHtml(map.credit)}</p>
      </details>`;
  }

  function renderVolcano() {
    const v = data.basics?.volcano;
    const host = document.querySelector("#basics-volcano");
    if (!v || !host) return;
    const image = v.image;
    host.innerHTML = `
      <figure class="volcano-photo">
        <img src="${escapeHtml(image.file)}" alt="${escapeHtml(image.alt)}" width="${image.width}" height="${image.height}" loading="lazy">
        <figcaption>${escapeHtml(image.caption)} <span class="photo-credit-inline">${escapeHtml(image.author)} · ${escapeHtml(image.license)} · <a href="${escapeHtml(image.sourceUrl)}" rel="noopener">${escapeHtml(image.source)}</a></span></figcaption>
      </figure>
      <div class="volcano-body">
        <p class="name-english">Famous volcano</p>
        <p class="name-local">${escapeHtml(v.local)}</p>
        <p class="name-say"><span class="name-label">Say it like this for now</span><strong>${escapeHtml(v.respelling)}</strong></p>
        <div class="name-audio">${audioControls(v.local)}</div>
        <p class="name-meaning">${escapeHtml(v.meaning)}</p>
        <p>${escapeHtml(v.summary)}</p>
        <ul class="volcano-facts">${v.facts.map(fact => `<li>${escapeHtml(fact)}</li>`).join("")}</ul>
        <p class="volcano-visit"><strong>See it:</strong> ${escapeHtml(v.visit)}</p>
        <p class="basics-note">${escapeHtml(v.pronunciationNote)}</p>
      </div>`;
  }

  function renderBestTime() {
    const info = data.basics?.bestTime;
    const host = document.querySelector("#basics-besttime");
    if (!info || !host) return;
    const bullets = items => `<ul>${items.map(value => `<li>${escapeHtml(value)}</li>`).join("")}</ul>`;
    host.innerHTML = `
      <p class="besttime-intro">${escapeHtml(info.intro)}</p>
      <div class="season-grid">${info.seasons.map(season => `
        <article class="season-card season-${escapeHtml(season.id)}">
          <header><span class="season-icon" aria-hidden="true">${season.icon || ""}</span><div><h4>${escapeHtml(season.name)}</h4><p class="season-months">${escapeHtml(season.months)}</p></div></header>
          <p class="season-daylight">${escapeHtml(season.daylight)}</p>
          <p class="name-label">Good for</p>${bullets(season.goodFor)}
          <p class="name-label">Watch for</p>${bullets(season.watchFor)}
        </article>`).join("")}</div>
      <p class="besttime-takeaway">${escapeHtml(info.takeaway)}</p>
      <p class="basics-note">${escapeHtml(info.limits)}</p>`;
  }

  function renderDailyChecks() {
    const info = data.basics?.dailyChecks;
    const host = document.querySelector("#basics-checks");
    if (!info || !host) return;
    host.innerHTML = `<p class="besttime-intro">${escapeHtml(info.intro)}</p>
      <div class="check-grid">${info.links.map(link => `<a class="check-card" href="${escapeHtml(link.url)}" target="_blank" rel="noopener"><strong>${escapeHtml(link.label)} <span aria-hidden="true">↗</span></strong><span>${escapeHtml(link.why)}</span></a>`).join("")}</div>`;
  }

  function renderBasics() {
    const basics = data.basics;
    if (!basics) return;
    document.querySelector("#basics-intro").textContent = basics.intro;
    document.querySelector("#basics-note").textContent = basics.pronunciationNote;
    document.querySelector("#basics-names").innerHTML = basics.names.map(name => `
      <article class="name-card">
        <p class="name-english">${escapeHtml(name.english)}</p>
        <p class="name-local">${escapeHtml(name.local)}</p>
        <p class="name-say"><span class="name-label">Say it like this for now</span><strong>${escapeHtml(name.respelling)}</strong></p>
        <div class="name-audio">${audioControls(name.local)}</div>
        <p class="name-meaning">${escapeHtml(name.meaning)}</p>
        <p>${escapeHtml(name.story)}</p>
      </article>`).join("");
    document.querySelector("#basics-numbers").innerHTML = basics.numbers.map(item => `
      <div class="number-tile"><span class="number-icon" aria-hidden="true">${item.icon || ""}</span><span class="name-label">${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong><p>${escapeHtml(item.detail)}</p></div>`).join("");
  }

  renderBasics();
  renderMap();
  renderBestTime();
  renderDailyChecks();
  renderVolcano();
  renderPlaybooks();
  renderRoutes();
  renderPlaceFilters();
  renderPlaces();

  let currentAudio = null;
  document.addEventListener("click", event => {
    const button = event.target.closest("[data-audio]");
    if (!button) return;
    if (currentAudio) currentAudio.pause();
    currentAudio = new Audio(button.dataset.audio);
    currentAudio.play().catch(() => {});
  });
})();
