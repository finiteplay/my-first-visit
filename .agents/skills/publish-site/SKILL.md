---
name: publish-site
description: Ship MyFirstVisit content to https://finiteplay.org/MyFirstVisit/ — media to the R2 bucket, commit and push without leaking secrets or third-party data, trigger the company-site deploy, and verify the live pages. Use after content or site changes are checked locally, or when asked to deploy, publish, clean history or check the live site.
---

# Publishing the site

Hosting: the guide is static. `finiteplay/finiteplay.org`'s GitHub Action checks out the public repo
`finiteplay/my-first-visit`, runs `tools/site/build_site.py --out dist/MyFirstVisit --media-base
https://media.finiteplay.org/myfirstvisit/` and deploys the Cloudflare Worker. Photos and audio are served from the
R2 bucket `finiteplay-media` (custom domain `media.finiteplay.org`), never from git.

## 1. Media first

```bash
python tools/media/media_store.py ingest <cc>      # encode new/changed media, update media-manifest.json
python tools/media/media_store.py verify <cc>
python tools/media/media_store.py upload <cc> --via-wrangler finiteplay-media --apply   # needs `wrangler login`
python tools/media/media_store.py prune-store <cc>   # dry run; --apply after a successful ingest
```

Keys are content hashes and immutable (`Cache-Control: max-age=31536000, immutable`): never overwrite a key; a
changed file gets a new key. Upload before deploying, or the live pages reference missing files.
Encoding standard: photos 1440 px long edge, sRGB WebP q80, EXIF/GPS stripped, plus a 640 px card copy; audio
trimmed, peak −1.5 dBFS, AAC-LC mono 48 kbit/s. Originals stay in `~/.finiteplay/media-store/<cc>/originals/`
(the only copy — keep it backed up).

## 2. Commit safely

- Stage explicit paths or review `git status` before `git add -A`. Running wrangler inside the repo creates
  `.wrangler/` (account details): it is git-ignored now; never commit it.
- Never commit: media bytes, `~/.finiteplay/score-inputs/*`, API keys (`~/.finiteplay/secrets/`), `.env`, review
  site data. The repo is public.
- Push with the gh credential helper (SSH is not set up on this machine):
  `git -c credential.helper= -c "credential.helper=!gh auth git-credential" push origin main`.

## 3. Deploy

Guide-only changes do not trigger a deploy. Run:

```bash
gh workflow run deploy.yml -R finiteplay/finiteplay.org
gh run watch <id> --exit-status -R finiteplay/finiteplay.org
```

Pages stay `noindex` until the author approves indexing (then add `--index` in that workflow and the URLs to the
company sitemap). Do not add a home-page link on finiteplay.org without the author.

## 4. Verify live (do not report done before this)

- Wait ~1 minute after the deploy (edge propagation returns brief 404s).
- `curl` the landing page, `/en/is/`, `/en/is/words` (expect 200) and one media key (expect 200, immutable cache).
- Confirm the changed markup or data is served (grep the live `content.js`, `app.js` or `styles.css`).
- For visible changes, open the live page in Chrome (Playwright) at 1440 and 390 px and look.

## 5. When something leaked

1. Stop; do not push more. Back up first: `git bundle create <backup>/repo.bundle --all`.
2. Remove the data from every commit with `git filter-repo` (paths: `--invert-paths --path ...`; values inside
   JSON: a `--blob-callback` that parses and rewrites the file, verified on every historical blob first with a
   round-trip test so formatting is preserved).
3. Check: the HEAD tree hash is unchanged (unless the fix needs it), `git grep` over `$(git rev-list --all)` finds
   nothing, tests pass. `git reflog expire --expire=now --all && git gc --prune=now --aggressive`.
4. Force-push. GitHub keeps old commits reachable by hash (and across a fork network); for secrets or personal data,
   delete and recreate the repo (needs `gh auth refresh -s delete_repo`) and confirm the old hashes return 422.
   Rotate any exposed credential regardless.
5. Tell the author exactly what was exposed, for how long, and what cannot be recalled (earlier clones).
