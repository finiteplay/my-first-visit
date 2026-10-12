"""Build the deployable MyFirstVisit website.

    python tools/site/build_site.py --out dist/MyFirstVisit --media-base https://media.finiteplay.org/myfirstvisit/

Layout of the output folder (it is published at https://finiteplay.org/MyFirstVisit/):
    index.html            product landing page          /MyFirstVisit/
    en/is/index.html      the Iceland guide in English  /MyFirstVisit/en/is/   (reader language / country)
    en/is/words.html      pronunciation page            /MyFirstVisit/en/is/words
    en/is/...             scripts, styles, article images and content.js

Photos and audio are not in the output: content.js points at --media-base (the public bucket). Pages get
`noindex` unless --index is passed; flip that only after the editorial and traveler reviews are done.
Everything is relative-linked, so the same output also works from any folder.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_URL = "https://finiteplay.org/MyFirstVisit"
LANG, COUNTRY = "en", "is"


def head_extra(url: str, index: bool, title: str, description: str) -> str:
    tags = [] if index else ['<meta name="robots" content="noindex, nofollow">']
    tags += [f'<link rel="canonical" href="{html.escape(url)}">',
             '<meta property="og:type" content="website">',
             '<meta property="og:site_name" content="MyFirstVisit">',
             f'<meta property="og:title" content="{html.escape(title)}">',
             f'<meta property="og:description" content="{html.escape(description)}">',
             f'<meta property="og:url" content="{html.escape(url)}">',
             '<meta name="twitter:card" content="summary">']
    return "\n  ".join(tags)


def inject(path: Path, url: str, index: bool) -> None:
    text = path.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", text, re.S).group(1)
    description = re.search(r'<meta name="description" content="(.*?)">', text, re.S).group(1)
    extra = head_extra(url, index, html.unescape(title), html.unescape(description))
    if "<!-- HEAD_EXTRA -->" in text:
        text = text.replace("<!-- HEAD_EXTRA -->", extra, 1)
    else:
        text = text.replace("</head>", f"  {extra}\n</head>", 1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "MyFirstVisit"))
    ap.add_argument("--media-base", default="media/", help="URL (or relative path) the site loads photos and audio from")
    ap.add_argument("--site-url", default=SITE_URL)
    ap.add_argument("--index", action="store_true", help="allow search engines (default: noindex)")
    args = ap.parse_args()

    out = Path(args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    guide = out / LANG / COUNTRY
    env = dict(os.environ, MFV_SITE_OUT=str(guide), MFV_MEDIA_BASE=args.media_base)
    subprocess.run([sys.executable, str(ROOT / "local-site" / "build.py")], check=True, env=env)

    base = args.site_url.rstrip("/")
    inject(guide / "index.html", f"{base}/{LANG}/{COUNTRY}/", args.index)
    inject(guide / "words.html", f"{base}/{LANG}/{COUNTRY}/words", args.index)
    shutil.copyfile(Path(__file__).with_name("landing.html"), out / "index.html")
    inject(out / "index.html", f"{base}/", args.index)

    content = (guide / "content.js").read_text(encoding="utf-8")
    if not args.media_base.startswith("http") and args.media_base != "media/":
        print("note: media base is a relative path; photos and audio must be served from there", file=sys.stderr)
    if args.media_base.startswith("http") and '"media/' in content:
        print("ERROR: content.js still has relative media/ references", file=sys.stderr)
        return 1
    files = [p for p in out.rglob("*") if p.is_file()]
    print(f"{out}: {len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.1f} MB, "
          f"{'indexable' if args.index else 'noindex'}, media from {args.media_base}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
