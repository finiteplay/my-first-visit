# Iceland local website

This buildless prototype presents the current Iceland briefing, playbooks, routes and places in
an editor/reviewer-friendly browser experience. It makes no network requests and uses only
local assets.

Rebuild `content.js` after editing canonical Iceland YAML:

```text
python local-site/build.py
```

Open `index.html` directly, or serve the project root when testing browser security and request
behavior:

```text
python -m http.server 4173
```

Then visit `http://localhost:4173/local-site/`.

The four photographs are AI-generated editorial illustrations created for this prototype. They
must not be represented as documentary evidence of a specific place, business or incident.
Their prototype provenance and image-purpose records are in `assets/media.json`.
