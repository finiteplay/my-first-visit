# MyFirstVisit

An offline, experience-led briefing for an American traveler visiting a country, often for
the first time. It synthesizes recent traveler experiences, official information and an
explicit editorial point of view into practical decisions, playbooks, routes, places and a
language toolkit. Quiz-like language practice is optional. Each country is a downloadable
pack, and downloaded content works in airplane mode.

Status: **research-backed Iceland editorial draft; app not built.** Iceland now has a strict-
audited traveler dossier, briefing, playbooks and routes alongside the earlier language toolkit.
Independent reviews, the Android app, production compiler, native audio and licensed photos
remain pending.

## First country example

Read [Iceland's package notes](content/is/README.md), its research dossier and the new briefing,
playbooks and routes. [PREVIEW.md](content/is/PREVIEW.md) remains the generated language/media
review copy. Together they demonstrate the pattern in [EDITORIAL.md](docs/EDITORIAL.md), while
the review report keeps human and release gates visibly pending. Native-speaker review is still
required before any draft language content is used for communication.

## Documentation

The specifications are the contract, and the code will follow them.

- [DESIGN.md](docs/DESIGN.md): product, user, destination briefing, optional practice, quiet
  mode, packs, roadmap and open questions
- [CONTENT.md](docs/CONTENT.md): research-backed briefings, playbooks, routes, places, language
  toolkit, semantic-HTML authoring, media, source layout, Iceland source pack and Japan sample
- [EDITORIAL.md](docs/EDITORIAL.md): traveler-story research, evidence and anecdote rules,
  editorial voice, optional practice, and the recursive quality workflow
- [UI_SPEC.md](docs/UI_SPEC.md): screens, navigation, components, colour, type, motion,
  accessibility
- [ARCHITECTURE.md](docs/ARCHITECTURE.md): native Compose shell, restricted offline WebView,
  modules, pack delivery and storage, and departures from the card games' platform rules

## Media

Photos, pronunciation audio and the volcano image are not kept in git. Git holds `content/<cc>/media-manifest.json`
(logical path -> content-hashed key); the bytes live in a media store (`~/.finiteplay/media-store`, or `MFV_MEDIA_STORE`)
that mirrors the public bucket. Use `tools/media/media_store.py`: `ingest` after adding or changing media, `sync-local`
to fill the git-ignored `local-site/media/` for the preview, `upload --apply` to publish to the bucket. The site reads
media from `MFV_MEDIA_BASE` (default `media/`) when it is built.

## Publisher

[FinitePlay](https://finiteplay.org)
