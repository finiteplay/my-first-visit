---
name: qa-site
description: Check the MyFirstVisit pages in a real browser — automated layout, image, overflow and console checks plus a visual pass at desktop, tablet and phone widths, with the layout rules learned from author review. Use after any change to pages, styles, images, place data or media, and before reporting a visual change as done.
---

# Site QA

Reading the CSS is not QA. Render the page, measure, and look at screenshots.

## 1. Serve and run the automated checks

```bash
python -m http.server 4173                       # from the project root (background)
python local-site/build.py                       # rebuild content.js and cache-busting hashes first
~/.finiteplay/venv/Scripts/python tools/qa/check_site.py --out <scratchpad>/shots
```

`check_site.py` (Playwright, system Chrome) opens the home page, places, guides, trips and the words page at
390, 800 and 1440 px and fails on: console errors and failing requests, broken or unloaded images, horizontal
overflow, a home-page block or the hero text that is not centred on the content column, a block wider than
1400 px, and a place card more than 1.6× the median card height. Exit code 0 is required, not sufficient.

## 2. Look (screenshots of what changed)

Open every changed surface at 1440, 800 and 390 px, and in the dark theme when colours changed. Check:

- **One column:** hero text, sections, feature blocks and figures share the centred content column (1220 px).
  Feature blocks may be slightly wider but stay centred. Nothing full-bleed except the hero image.
- **Images:** same picture for a guide's card and its article hero; no image dominates the page (landscape
  figures ≤ ~520 px tall on desktop, 4:3 on phones); the subject stays visible in every crop (cards, carousel,
  popup); set `objectPosition` per photo when it does not. An `<img>` with width/height attributes needs
  `height: auto` when CSS sets an aspect ratio, or phones get the attribute height.
- **Headlines:** long sentence headlines in narrow columns get a smaller size than section titles.
- **Cards:** equal rhythm; priority, our stars and the ranking label on one line; no stray class reusing another
  component's styles (a shared class name once added 600 px to cards).
- **Stacking:** two-column blocks stack on ≤ 900 px; a later rule must not override the mobile layout.
- **Links:** Maps opens parking for walk-in sights; weather links use the place's coordinates; no review-site
  numbers, logos or listing links anywhere.

## 3. Freshness

Pages reference `content.js`, `app.js`, `words.js` and `styles.css` with content-hash query strings written by
`build.py`. If someone reports stale or missing pictures, ask for a hard refresh first, then check that the
build ran. Local media missing from `local-site/media/` falls back to the public bucket; run
`media_store.py sync-local <cc>` for offline work. If the local server is down, restart it for the author.

## 4. Report

Give the author the widths you checked, what you saw (attach a screenshot for visual changes), anything the
checks could not prove, and the remaining decisions. Then ship with `.agents/skills/publish-site/SKILL.md`.
