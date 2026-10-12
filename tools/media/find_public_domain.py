"""List public-domain / CC0 landscape photos on Wikimedia Commons for given search terms.

Unlike shortlist_photos.py (attribution licenses, author picks), this only accepts files whose
file page states Public domain or CC0, so no attribution is legally required (credit is still
shown). The agent must still confirm the subject matches the card; it never accepts a
look-alike.

    python tools/media/find_public_domain.py "Laugardalslaug" "aurora borealis Iceland" [--min-width 1600]
"""
from __future__ import annotations

import argparse
import re
import sys
import time

sys.path.insert(0, __file__.rsplit("tools", 1)[0] + "tools/media")
import shortlist_photos as sp  # noqa: E402


def is_public_domain(short: str) -> bool:
    s = (short or "").lower()
    return bool(re.search(r"public domain|cc0|\bpd\b|pdm", s)) and "cc by" not in s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="+")
    ap.add_argument("--min-width", type=int, default=1600)
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()
    for term in args.terms:
        print(f"## {term}")
        seen = set()
        try:
            found = sp.commons_candidates(term, limit=args.limit)
        except Exception as e:  # rate limit etc.
            print("  search failed:", e)
            continue
        for c in found:
            if c["sourceUrl"] in seen or not is_public_domain(c["license"]):
                continue
            seen.add(c["sourceUrl"])
            w, h = c["width"], c["height"]
            if c["mime"] not in ("image/jpeg", "image/png") or not h or w < args.min_width:
                continue
            ratio = w / h
            if ratio < sp.MIN_RATIO or ratio > sp.MAX_RATIO:
                continue
            print(f"  {c['license']:<18} {w}x{h} ({ratio:.2f}) {c['author'][:28]:<28} {c['title']}")
            print(f"      {c['sourceUrl']}")
        time.sleep(2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
