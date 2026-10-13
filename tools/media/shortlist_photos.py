"""Build a verified photo shortlist per attraction for content-author selection.

Searches the approved sources (Wikimedia Commons; Flickr when FLICKR_API_KEY or ~/.finiteplay/flickr.key is set),
keeps only exact-place landscape files whose own file page states a license that allows
commercial use with attribution, downloads local preview thumbnails, and writes
`content/<cc>/media-candidates/candidates.json` plus `review.html`.

The author picks 3-5 photos per attraction in review.html; agents never pick for them.

    python tools/media/shortlist_photos.py is [--only sight-gullfoss] [--max 20]
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = "MyFirstVisit-shortlist/1.0 (FinitePlay LLC; content research)"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
MIN_RATIO, MAX_RATIO = 4 / 3, 2.2  # landscape only; reject slivers of panoramas
MIN_WIDTH = 1600
THUMB_WIDTH = 640

# Words a candidate's title or description must contain (exact-place pre-filter;
# the content author still confirms the match).
KEYWORDS = {
    "sight-laugardalslaug": ["Laugardalslaug"],
    "sight-thingvellir": ["Þingvellir", "Thingvellir", "Almannagjá"],
    "sight-gullfoss": ["Gullfoss"],
    "sight-geysir": ["Strokkur", "Geysir"],
    "sight-hallgrimskirkja": ["Hallgrímskirkja", "Hallgrimskirkja"],
    "sight-harpa": ["Harpa"],
    "sight-national-museum": ["National Museum of Iceland", "Þjóðminjasafn"],
    "sight-seljalandsfoss": ["Seljalandsfoss"],
    "sight-skogafoss": ["Skógafoss", "Skogafoss"],
    "sight-reynisfjara": ["Reynisfjara", "Reynisdrangar"],
    "sight-jokulsarlon": ["Jökulsárlón", "Jokulsarlon"],
    "sight-godafoss": ["Goðafoss", "Godafoss"],
    "sight-myvatn": ["Mývatn", "Myvatn"],
    "sight-perlan": ["Perlan"],
    "sight-whales": ["Whales of Iceland"],
    "sight-aurora-reykjavik": ["Aurora Reykjavík", "Aurora Reykjavik"],
    "sight-flyover": ["FlyOver Iceland", "Flyover Iceland"],
    "sight-mink": ["Mink Viking"],
    "sight-petras-stone-collection": ["Petra", "Steinasafn", "Stöðvarfjörður"],
    "sight-vok-baths": ["Vök"],
    "sight-old-harbour": ["Old Harbour", "Gamla höfnin", "Reykjavík harbour", "Reykjavik harbour", "Reykjavíkurhöfn"],
    "sight-laugavegur": ["Laugavegur", "Skólavörðustígur", "Skolavordustigur", "Rainbow Street"],
    "sight-magic-ice": ["Magic Ice"],
    "sight-ytri-tunga": ["Ytri Tunga", "Ytri-Tunga"],
    "sight-budakirkja": ["Búðakirkja", "Budakirkja", "Búðir church", "Budir church", "Black Church"],
    "sight-arnarstapi-hellnar": ["Arnarstapi", "Hellnar", "Gatklettur"],
    "sight-londrangar": ["Lóndrangar", "Londrangar"],
    "sight-djupalonssandur": ["Djúpalónssandur", "Djupalonssandur", "Dritvík"],
    "sight-kirkjufellsfoss": ["Kirkjufellsfoss", "Kirkjufell"],
    "sight-bjarnarhofn": ["Bjarnarhöfn", "Bjarnarhofn"],
    "sight-glaumbaer": ["Glaumbær", "Glaumbaer"],
    "sight-akureyri-botanical-garden": ["Lystigarður", "Akureyri Botanical"],
    "sight-hverir": ["Hverir", "Námaskarð", "Namaskard", "Hverarönd", "Namafjall"],
    "sight-skutustadagigar": ["Skútustaðagígar", "Skutustadagigar", "pseudocrater", "pseudo crater"],
    "sight-dettifoss": ["Dettifoss"],
    "sight-hengifoss": ["Hengifoss", "Litlanesfoss"],
    "sight-djupivogur": ["Djúpivogur", "Djupivogur", "Eggin í Gleðivík", "Gledivik"],
    "sight-diamond-beach": ["Diamond Beach", "Breiðamerkursandur", "Breidamerkursandur", "Fellsfjara"],
    "sight-fjallsarlon": ["Fjallsárlón", "Fjallsarlon"],
    "sight-skaftafell": ["Skaftafell"],
    "sight-svartifoss": ["Svartifoss"],
    "sight-dverghamrar": ["Dverghamrar"],
    "sight-foss-a-sidu": ["Foss á Síðu", "Foss a Sidu", "Eldhraun"],
    "sight-lava-show": ["Lava Show"],
    "sight-kvernufoss": ["Kvernufoss"],
    "sight-gljufrabui": ["Gljúfrabúi", "Gljufrabui"],
    "sight-caves-of-hella": ["Caves of Hella", "Hella caves", "Ægissíðu", "Aegissida"],
    "sight-urridafoss": ["Urriðafoss", "Urridafoss"],
    "sight-bruarfoss": ["Brúarfoss", "Bruarfoss"],
    "sight-kerid": ["Kerið", "Kerid"],
    "sight-raufarholshellir": ["Raufarhólshellir", "Raufarholshellir", "Lava Tunnel"],
    "sight-sky-lagoon": ["Sky Lagoon"],
    "sight-blue-lagoon": ["Blue Lagoon", "Bláa lónið", "Blaa lonid"],
    "sight-hvammsvik": ["Hvammsvík", "Hvammsvik"],
    "sight-reykjadalur": ["Reykjadalur"],
    "sight-earth-lagoon-myvatn": ["Mývatn Nature Baths", "Myvatn Nature Baths", "Jarðböðin", "Earth Lagoon"],
    "sight-secret-lagoon": ["Secret Lagoon", "Gamla laugin", "Gamla Laugin"],
    "sight-forest-lagoon": ["Forest Lagoon", "Skógarböðin"],
    "sight-fontana": ["Laugarvatn Fontana", "Fontana Laugarvatn"],
    "sight-geosea": ["GeoSea", "Geosea"],
    "sight-krauma": ["Krauma", "Deildartunguhver"],
}

# Search terms per attraction. Extra terms help find exact-place files.
QUERIES = {
    "sight-laugardalslaug": ["Laugardalslaug"],
    "sight-thingvellir": ["Þingvellir", "Thingvellir Almannagjá"],
    "sight-gullfoss": ["Gullfoss"],
    "sight-geysir": ["Strokkur", "Geysir Haukadalur"],
    "sight-hallgrimskirkja": ["Hallgrímskirkja"],
    "sight-harpa": ["Harpa Reykjavík concert hall"],
    "sight-national-museum": ["National Museum of Iceland", "Þjóðminjasafn Íslands"],
    "sight-seljalandsfoss": ["Seljalandsfoss"],
    "sight-skogafoss": ["Skógafoss"],
    "sight-reynisfjara": ["Reynisfjara", "Reynisdrangar"],
    "sight-jokulsarlon": ["Jökulsárlón"],
    "sight-godafoss": ["Goðafoss"],
    "sight-myvatn": ["Mývatn", "Myvatn lake"],
    "sight-perlan": ["Perlan Reykjavík"],
    "sight-whales": ["Whales of Iceland museum"],
    "sight-aurora-reykjavik": ["Aurora Reykjavík northern lights center"],
    "sight-flyover": ["FlyOver Iceland"],
    "sight-mink": ["Mink Viking Portrait"],
    "sight-petras-stone-collection": ["Steinasafn Petru", "Petra's Stone Collection", "Stöðvarfjörður"],
    "sight-vok-baths": ["Vök Baths", "Urriðavatn Egilsstaðir"],
    "sight-old-harbour": ["Old Harbour Reykjavík", "Reykjavík harbour", "Gamla höfnin"],
    "sight-laugavegur": ["Laugavegur Reykjavík", "Skólavörðustígur rainbow street"],
    "sight-magic-ice": ["Magic Ice Reykjavík ice bar"],
    "sight-ytri-tunga": ["Ytri Tunga seals", "Ytri-Tunga"],
    "sight-budakirkja": ["Búðakirkja", "Budakirkja black church"],
    "sight-arnarstapi-hellnar": ["Arnarstapi", "Hellnar Arnarstapi path", "Gatklettur"],
    "sight-londrangar": ["Lóndrangar", "Londrangar"],
    "sight-djupalonssandur": ["Djúpalónssandur", "Djupalonssandur beach"],
    "sight-kirkjufellsfoss": ["Kirkjufellsfoss", "Kirkjufell"],
    "sight-bjarnarhofn": ["Bjarnarhöfn shark museum", "Bjarnarhöfn"],
    "sight-glaumbaer": ["Glaumbær", "Glaumbaer turf"],
    "sight-akureyri-botanical-garden": ["Akureyri Botanical Garden", "Lystigarður Akureyrar"],
    "sight-hverir": ["Hverir Mývatn", "Námaskarð", "Hverarönd"],
    "sight-skutustadagigar": ["Skútustaðagígar", "Skutustadagigar pseudocraters"],
    "sight-dettifoss": ["Dettifoss"],
    "sight-hengifoss": ["Hengifoss", "Litlanesfoss"],
    "sight-djupivogur": ["Djúpivogur", "Eggin í Gleðivík"],
    "sight-diamond-beach": ["Diamond Beach Iceland", "Breiðamerkursandur", "Fellsfjara"],
    "sight-fjallsarlon": ["Fjallsárlón"],
    "sight-skaftafell": ["Skaftafellsjökull", "Skaftafell"],
    "sight-svartifoss": ["Svartifoss"],
    "sight-dverghamrar": ["Dverghamrar"],
    "sight-foss-a-sidu": ["Eldhraun", "Foss á Síðu"],
    "sight-lava-show": ["Lava Show Vík"],
    "sight-kvernufoss": ["Kvernufoss"],
    "sight-gljufrabui": ["Gljúfrabúi", "Gljufrabui"],
    "sight-caves-of-hella": ["Caves of Hella", "Hellarnir Ægissíðu"],
    "sight-urridafoss": ["Urriðafoss"],
    "sight-bruarfoss": ["Brúarfoss", "Bruarfoss"],
    "sight-kerid": ["Kerið crater", "Kerid crater"],
    "sight-raufarholshellir": ["Raufarhólshellir", "Raufarholshellir lava tunnel"],
    "sight-sky-lagoon": ["Sky Lagoon Kópavogur"],
    "sight-blue-lagoon": ["Blue Lagoon Iceland", "Bláa lónið"],
    "sight-hvammsvik": ["Hvammsvík"],
    "sight-reykjadalur": ["Reykjadalur", "Reykjadalur hot spring"],
    "sight-earth-lagoon-myvatn": ["Mývatn Nature Baths", "Jarðböðin"],
    "sight-secret-lagoon": ["Secret Lagoon Flúðir", "Gamla Laugin"],
    "sight-forest-lagoon": ["Forest Lagoon Akureyri"],
    "sight-fontana": ["Laugarvatn Fontana"],
    "sight-geosea": ["GeoSea Húsavík"],
    "sight-krauma": ["Krauma", "Deildartunguhver"],
}


def allowed_license(short: str, url: str) -> str | None:
    """Return a normalized license if it permits commercial use with attribution."""
    s = (short or "").lower().replace("_", " ")
    if not s or re.search(r"\bnc\b|non-?commercial|\bnd\b|no ?deriv|all rights|fair use", s):
        return None
    if s.startswith("gfdl") and "cc" not in s:
        return None  # GFDL-only rejected
    if "cc0" in s or "public domain" in s or s.startswith("pd"):
        return short
    if re.match(r"cc[ -]by([ -]sa)?([ -]\d(\.\d)?)?", s):
        return short
    return None


def get_json(url: str, params: dict) -> dict:
    full = url + "?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(full, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:  # network hiccup or 429
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    return {}


def strip_html(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def commons_candidates(query: str, limit: int = 60) -> list[dict]:
    data = get_json(COMMONS_API, {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": 6, "gsrlimit": limit,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata|mime",
        "iiurlwidth": THUMB_WIDTH,
    })
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        w, h = info.get("width", 0), info.get("height", 0)
        out.append({
            "source": "Wikimedia Commons",
            "title": p["title"],
            "sourceUrl": info.get("descriptionurl"),
            "fileUrl": info.get("url"),
            "thumbUrl": info.get("thumburl"),
            "mime": info.get("mime"),
            "width": w, "height": h,
            "author": strip_html(meta.get("Artist", {}).get("value", "")),
            "license": meta.get("LicenseShortName", {}).get("value", ""),
            "licenseUrl": meta.get("LicenseUrl", {}).get("value", ""),
            "description": strip_html(meta.get("ImageDescription", {}).get("value", ""))[:300],
            "restrictions": meta.get("Restrictions", {}).get("value", ""),
        })
    return out


def flickr_candidates(query: str, key: str, limit: int = 100, pages: int = 1) -> list[dict]:
    # Flickr license ids: 4 CC BY 2.0, 5 CC BY-SA 2.0, 7 no known restrictions,
    # 9 CC0, 10 PDM, 11 CC BY 4.0, 12 CC BY-SA 4.0. NC/ND ids are excluded.
    names = {"4": ("CC BY 2.0", "https://creativecommons.org/licenses/by/2.0/"),
             "5": ("CC BY-SA 2.0", "https://creativecommons.org/licenses/by-sa/2.0/"),
             "9": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
             "10": ("Public Domain Mark", "https://creativecommons.org/publicdomain/mark/1.0/"),
             "11": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"),
             "12": ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/")}
    photos = []
    for page in range(1, pages + 1):
        data = get_json("https://api.flickr.com/services/rest/", {
            "method": "flickr.photos.search", "api_key": key, "format": "json", "nojsoncallback": 1,
            "text": query, "license": ",".join(names), "content_type": 1, "media": "photos",
            "sort": "relevance", "per_page": limit, "page": page,
            "extras": "license,owner_name,o_dims,url_l,url_z,url_o,description,tags",
        })
        photos += data.get("photos", {}).get("photo", [])
    out = []
    for p in photos:
        lic = names.get(str(p.get("license")))
        w = int(p.get("width_o") or p.get("width_l") or 0)
        h = int(p.get("height_o") or p.get("height_l") or 0)
        if not lic:
            continue
        out.append({
            "source": "Flickr", "title": p.get("title", ""),
            "sourceUrl": f"https://www.flickr.com/photos/{p['owner']}/{p['id']}/",
            "fileUrl": p.get("url_l") or p.get("url_o"), "thumbUrl": p.get("url_z") or p.get("url_l"),
            "mime": "image/jpeg", "width": w, "height": h, "author": p.get("ownername", ""),
            "license": lic[0], "licenseUrl": lic[1],
            "description": strip_html(p.get("description", {}).get("_content", ""))[:300]
                           + (" tags: " + p["tags"] if p.get("tags") else ""),
            "restrictions": "", "note": "Confirm the uploader's own work (not a re-upload).",
        })
    return out


def reject_reason(c: dict) -> str | None:
    if c["mime"] not in ("image/jpeg", "image/png", "image/webp"):
        return "not a photo format"
    if not allowed_license(c["license"], c["licenseUrl"]):
        return f"license not allowed: {c['license'] or 'missing'}"
    if not c["author"]:
        return "no author stated"
    if not c["width"] or not c["height"]:
        return "dimensions unknown"
    ratio = c["width"] / c["height"]
    if ratio < MIN_RATIO:
        return f"not landscape enough ({ratio:.2f})"
    if ratio > MAX_RATIO:
        return f"too wide ({ratio:.2f})"
    if c["width"] < MIN_WIDTH:
        return f"too small ({c['width']}px)"
    return None


def download(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    for attempt in range(5):
        try:
            time.sleep(1.0)  # be polite to upload.wikimedia.org
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
            return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            print(f"  thumbnail failed: {url}: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"  thumbnail failed: {url}: {e}", file=sys.stderr)
            return False
    return False


def fold(s: str) -> str:
    """Lowercase and fold Icelandic letters so 'Þingvellir' matches 'Thingvellir'."""
    s = s.lower()
    for a, b in (("þ", "th"), ("ð", "d"), ("æ", "ae"), ("ö", "o"), ("á", "a"), ("é", "e"),
                 ("í", "i"), ("ó", "o"), ("ú", "u"), ("ý", "y")):
        s = s.replace(a, b)
    return s


def names_place(c: dict, keywords: list[str]) -> bool:
    text = fold(urllib.parse.unquote(c["title"]) + " " + c["description"]).replace("_", " ")
    return any(fold(k) in text for k in keywords)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("--only", action="append")
    ap.add_argument("--max", type=int, default=20)
    args = ap.parse_args()

    pack = ROOT / "content" / args.country
    sights = json.loads((pack / "sights.yaml").read_text(encoding="utf-8"))["items"]
    out_dir = pack / "media-candidates"
    thumbs = out_dir / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    cand_path = out_dir / "candidates.json"
    existing = json.loads(cand_path.read_text(encoding="utf-8")) if cand_path.exists() else {}
    flickr_key = os.environ.get("FLICKR_API_KEY")
    key_file = Path.home() / ".finiteplay" / "flickr.key"  # outside the project on purpose
    if not flickr_key and key_file.exists():
        flickr_key = key_file.read_text(encoding="utf-8").strip() or None
    print("Flickr:", "enabled" if flickr_key else f"disabled (no FLICKR_API_KEY or {key_file})")

    result = dict(existing.get("attractions", {}))
    for s in sights:
        sid = s["id"]
        if args.only and sid not in args.only:
            continue
        print(f"{sid}: searching", flush=True)
        raw, seen, rejected = [], set(), {}
        for q in QUERIES.get(sid, [s["local"]]):
            raw += commons_candidates(q)
            if flickr_key:
                raw += flickr_candidates(q, flickr_key, pages=2)
        kept = []
        for c in raw:
            if c["sourceUrl"] in seen:
                continue
            seen.add(c["sourceUrl"])
            why = None if names_place(c, KEYWORDS.get(sid, [s["local"]])) else "place not named"
            why = why or reject_reason(c)
            if why:
                rejected[why.split(":")[0].split(" (")[0]] = rejected.get(why.split(":")[0].split(" (")[0], 0) + 1
                continue
            c["ratio"] = round(c["width"] / c["height"], 2)
            c["id"] = f"{sid}-c{len(kept) + 1:02d}"
            thumb = thumbs / f"{c['id']}.jpg"
            if c["thumbUrl"] and download(c["thumbUrl"], thumb):
                c["thumb"] = f"thumbs/{thumb.name}"
                kept.append(c)
            if len(kept) >= args.max:
                break
        # Keep manually added candidates (tools/media/add_candidate.py).
        # ... and the author's own photos (tools/media/add_personal_candidates.py).
        kept += [x for x in existing.get("attractions", {}).get(sid, {}).get("candidates", [])
                 if x.get("personal") or ("-m" in x["id"] and x["sourceUrl"] not in {k["sourceUrl"] for k in kept})]
        result[sid] = {
            "name": s["name"], "local": s["local"],
            "candidates": kept,
            "rejectedCounts": rejected,
            "shortfall": None if len(kept) >= 10 else
                f"Only {len(kept)} verified candidates passed license and landscape checks.",
        }
        print(f"  kept {len(kept)}; rejected {sum(rejected.values())} {rejected}")

    doc = {
        "schemaVersion": 1,
        "generatedAt": time.strftime("%Y-%m-%d"),
        "sources": ["Wikimedia Commons"] + (["Flickr"] if flickr_key else []),
        "rules": "Commercial use with attribution only (CC0, PD, CC BY, CC BY-SA); "
                 f"landscape {MIN_RATIO:.2f}-{MAX_RATIO} ratio; min width {MIN_WIDTH}px. "
                 "Exact-place match must be confirmed by the content author.",
        "attractions": result,
    }
    cand_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    write_review(out_dir, doc)
    print(f"Wrote {cand_path} and {out_dir / 'review.html'}")
    return 0


def write_review(out_dir: Path, doc: dict) -> None:
    """Write review.html. `applied` records how many author-selected photos each place already has in photos.json."""
    photos_path = out_dir.parent / "photos.json"
    applied, applied_photos = {}, {}
    if photos_path.exists():
        site = json.loads(photos_path.read_text(encoding="utf-8")).get("attractions", {})
        applied = {k: len(v) for k, v in site.items() if v}
        applied_photos = {k: [{"id": x["id"], "objectPosition": x.get("objectPosition", "center")} for x in v] for k, v in site.items() if v}
    doc = dict(doc, applied=applied, appliedPhotos=applied_photos)
    data = json.dumps(doc, ensure_ascii=False).replace("</", "<\\/")
    (out_dir / "review.html").write_text(REVIEW_HTML.replace("__DATA__", data), encoding="utf-8")


REVIEW_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Photo Shortlist Review</title>
<style>
:root{--bg:#f6f4ee;--card:#fff;--ink:#1d2a2c;--muted:#5d6a6b;--accent:#3d6b4a;--warn:#9a5b12;--line:#d9d5ca}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141a1b;--card:#1e2627;--ink:#e8ece9;--muted:#9fb0ae;--accent:#8fc59c;--warn:#e0a85a;--line:#33403f}}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
header h1{font-size:1.1rem;margin:0;flex:1}
button{font:inherit;padding:7px 12px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}
button.alt{background:transparent;color:var(--ink);border-color:var(--line)}
.layout{display:grid;grid-template-columns:290px 1fr;gap:18px;max-width:1700px;margin:auto;padding:0 16px}
nav#toc{position:sticky;top:64px;align-self:start;max-height:calc(100vh - 80px);overflow:auto;padding:12px 4px 12px 0;font-size:.85rem}
nav#toc h2{font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:10px 0 6px}
nav#toc a{display:flex;justify-content:space-between;gap:8px;padding:5px 8px;border-radius:8px;color:var(--ink);text-decoration:none;border:1px solid transparent}
nav#toc a:hover{border-color:var(--line);background:var(--card)}
nav#toc .badge{white-space:nowrap;font-weight:700;color:var(--muted)}
nav#toc .badge.ok{color:var(--accent)} nav#toc .badge.part{color:var(--warn)}
nav#toc .tools{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 8px}
nav#toc .tools button{background:transparent;color:var(--ink);border-color:var(--line);padding:4px 10px;font-size:.78rem}
nav#toc .tools button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
@media (max-width:900px){.layout{grid-template-columns:1fr}nav#toc{position:static;max-height:240px;border-bottom:1px solid var(--line)}}
main{padding:16px 0;min-width:0}
section{scroll-margin-top:70px}
section{margin:0 0 40px}
h2{margin:0 0 4px;font-size:1.25rem} .sub{color:var(--muted);margin:0 0 12px;font-size:.9rem}
.count{font-weight:700} .count.ok{color:var(--accent)} .count.bad{color:var(--warn)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.c{background:var(--card);border:2px solid var(--line);border-radius:12px;padding:10px;font-size:.8rem}
.c.sel{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent)}
.c img.full{width:100%;display:block;border-radius:6px;cursor:zoom-in}
.prev{display:flex;gap:6px;margin:8px 0}
.prev div{flex:1;text-align:center;color:var(--muted);font-size:.7rem}
.frame{background:#e9e7df;border-radius:4px;overflow:hidden}
.frame img{width:100%;height:100%;display:block}
.r32{aspect-ratio:3/2}.r169{aspect-ratio:16/9}.r21{aspect-ratio:21/9}
.cover img{object-fit:cover}.contain img{object-fit:contain}
label.pick{display:flex;gap:6px;align-items:center;font-weight:700;font-size:.9rem;margin-bottom:6px}
.meta{color:var(--muted);word-break:break-word} .meta a{color:var(--accent)}
.insite{margin-left:6px;padding:1px 8px;border-radius:999px;background:var(--accent);color:#fff;font-size:.7rem;font-weight:700}
.c.insite-card{outline:2px solid var(--accent)}
.order{margin:8px 0 12px;padding:8px;border:1px dashed var(--line);border-radius:10px;background:var(--card)}
.order h3{margin:0 0 6px;font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.order .row{display:flex;gap:10px;flex-wrap:wrap;min-height:48px}
.oi{position:relative;width:150px;border:1px solid var(--line);border-radius:8px;background:var(--bg);padding:4px;cursor:grab}
.oi.dragging{opacity:.4} .oi.over{outline:3px solid var(--accent)}
.oi img{display:block;width:100%;height:90px;object-fit:cover;border-radius:5px}
.oi .n{position:absolute;top:6px;left:6px;min-width:22px;height:22px;border-radius:999px;background:var(--accent);color:#fff;font-weight:800;font-size:.8rem;display:grid;place-items:center}
.oi .tools{display:flex;gap:4px;justify-content:space-between;margin-top:4px}
.oi button{padding:1px 8px;font-size:.8rem;background:transparent;color:var(--ink);border:1px solid var(--line)}
.order .empty{color:var(--muted);font-size:.85rem;align-self:center}
.warn{color:var(--warn);font-weight:600}
select{font:inherit;font-size:.75rem}
dialog{max-width:95vw;padding:0;border:0;background:#000} dialog img{max-width:95vw;max-height:90vh;display:block}
</style></head><body>
<header><h1>Photo shortlist: choose 3–5 per attraction (1–2 = partial); set their order</h1>
<span id="total"></span><span id="filestate" class="sub"></span><button id="open" type="button" title="Load picks from selection.json">Open selection.json</button><button id="save" type="button" title="Save into the same selection.json each time">Save to selection.json</button><button id="export" type="button" class="alt">Download copy</button></header>
<div class="layout"><nav id="toc" aria-label="Places"></nav><main id="m"></main></div>
<dialog id="dlg"><img id="dlgimg" alt=""></dialog>
<script>
const DOC = __DATA__;
const KEY = "fda-photo-selection";
let sel = {};
let filter = "all";
try { sel = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
// Places with no pick of their own start from what the site shows now, in its order, so you can deselect and re-order them.
for (const [sid, list] of Object.entries(DOC.appliedPhotos || {})) {
  if (sel[sid] === undefined) sel[sid] = Object.fromEntries(list.map(p => [p.id, { objectPosition: p.objectPosition }]));
}
const siteIds = sid => new Set(((DOC.appliedPhotos || {})[sid] || []).map(p => p.id));
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(sel)); } catch (e) {} render(); };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const POS = ["center","top","bottom","left","right"];
function render() {
  const m = document.getElementById("m"); m.innerHTML = "";
  let done = 0, total = 0;
  for (const [sid, a] of Object.entries(DOC.attractions)) {
    total++;
    const picks = sel[sid] || {};
    const n = Object.keys(picks).length;
    if (n >= 1) done++;
    const inSite = (DOC.applied || {})[sid] || 0;
    if ((filter === "needs" && (inSite || n)) || (filter === "selected" && !n)) continue;
    const s = document.createElement("section");
    s.id = "p-" + sid;
    s.innerHTML = `<h2>${esc(a.name)} <span class="sub">(${esc(a.local)})</span></h2>
      <p class="sub"><span class="count ${n>=3?"ok":"bad"}">${n} selected${n>=1&&n<3?" (partial, can add more later)":""}</span>${inSite ? ` · <b>${inSite} already in the site</b>` : ""} · ${a.candidates.length} verified candidates
      ${a.shortfall ? `· <span class="warn">${esc(a.shortfall)}</span>` : ""}
      · rejected: ${esc(Object.entries(a.rejectedCounts||{}).map(([k,v])=>k+" "+v).join(", ") || "none")}</p>
      <div class="order"></div><div class="grid"></div>`;
    renderOrder(s.querySelector(".order"), sid, a);
    const g = s.querySelector(".grid");
    for (const c of a.candidates) {
      const p = picks[c.id];
      const pos = p?.objectPosition || "center";
      const d = document.createElement("div");
      d.className = "c" + (p ? " sel" : "") + (siteIds(sid).has(c.id) ? " insite-card" : "");
      d.innerHTML = `<label class="pick"><input type="checkbox" ${p?"checked":""}> Select ${esc(c.id)}${siteIds(sid).has(c.id) ? '<span class="insite">in site now</span>' : ""}</label>
        <img class="full" src="${esc(c.thumb)}" alt="${esc(c.title)}" loading="lazy">
        <div class="prev">
          <div><div class="frame r32 cover"><img src="${esc(c.thumb)}" alt="" style="object-position:${pos}"></div>card 3:2 crop</div>
          <div><div class="frame r169 cover"><img src="${esc(c.thumb)}" alt="" style="object-position:${pos}"></div>popup 16:9</div>
          <div><div class="frame r21 cover"><img src="${esc(c.thumb)}" alt="" style="object-position:${pos}"></div>banner 21:9</div>
        </div>
        <div class="meta">Focus <select>${POS.map(x=>`<option ${x===pos?"selected":""}>${x}</option>`).join("")}<option value="contain" ${pos==="contain"?"selected":""}>contain (no crop)</option></select><br>
        ${esc(c.width)}×${esc(c.height)} (${esc(c.ratio)}) · ${esc(c.source)}<br>
        <b>${esc(c.license)}</b> · ${esc(c.author)}<br>
        ${c.sourceUrl ? `<a href="${esc(c.sourceUrl)}" target="_blank" rel="noopener">file page</a> · ` : ""}${esc(c.title)}
        ${c.description ? `<br>${esc(c.description)}` : ""}
        ${c.restrictions ? `<br><span class="warn">Restrictions: ${esc(c.restrictions)}</span>` : ""}
        ${c.note ? `<br><span class="warn">${esc(c.note)}</span>` : ""}</div>`;
      if (pos === "contain") d.querySelectorAll(".prev .frame").forEach(f => f.classList.replace("cover","contain"));
      d.querySelector("input").onchange = e => {
        sel[sid] = sel[sid] || {};
        if (e.target.checked) {
          if (Object.keys(sel[sid]).length >= 5) { e.target.checked = false; return; }
          sel[sid][c.id] = { objectPosition: pos };
        } else delete sel[sid][c.id];
        save();
      };
      d.querySelector("select").onchange = e => {
        if (sel[sid]?.[c.id]) { sel[sid][c.id].objectPosition = e.target.value; save(); }
        else { const v = e.target.value; d.querySelectorAll(".prev img").forEach(i => i.style.objectPosition = v === "contain" ? "center" : v);
               d.querySelectorAll(".prev .frame").forEach(f => { f.classList.toggle("contain", v==="contain"); f.classList.toggle("cover", v!=="contain"); }); }
      };
      d.querySelector("img.full").onclick = () => { document.getElementById("dlgimg").src = c.thumb; document.getElementById("dlg").showModal(); };
      g.appendChild(d);
    }
    m.appendChild(s);
  }
  const pickedTotal = Object.values(sel).reduce((acc, p) => acc + Object.keys(p).length, 0);
  document.getElementById("total").textContent = `${pickedTotal} selected in ${done}/${total} places (3–5 complete, 1–2 partial)`;
  renderToc();
}
function reorder(sid, ids) {
  const old = sel[sid] || {};
  sel[sid] = Object.fromEntries(ids.filter(id => old[id]).map(id => [id, old[id]]));
  save();
}
function renderOrder(box, sid, a) {
  const ids = Object.keys(sel[sid] || {});
  const byId = Object.fromEntries(a.candidates.map(c => [c.id, c]));
  const inSite = siteIds(sid);
  box.innerHTML = `<h3>Gallery order (the first photo is the card picture) · drag, or use ◀ ▶ · ✕ removes</h3><div class="row">${
    ids.length ? ids.map((id, i) => `<div class="oi" draggable="true" data-id="${esc(id)}">
        <span class="n">${i + 1}</span><img src="${esc(byId[id]?.thumb || "")}" alt="">
        <div class="tools"><button type="button" data-act="left" ${i === 0 ? "disabled" : ""} aria-label="Earlier">◀</button>
        <button type="button" data-act="rm" aria-label="Remove">✕</button>
        <button type="button" data-act="right" ${i === ids.length - 1 ? "disabled" : ""} aria-label="Later">▶</button></div>
        <small>${esc(id.replace(sid + "-", ""))}${inSite.has(id) ? " · in site" : ""}</small></div>`).join("")
    : '<span class="empty">Nothing selected' + (inSite.size ? " — saving this clears the photos the site shows now." : ".") + "</span>"}</div>`;
  let drag = null;
  box.querySelectorAll(".oi").forEach(el => {
    const id = el.dataset.id;
    el.ondragstart = e => { drag = id; el.classList.add("dragging"); e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", id); };
    el.ondragend = () => { drag = null; box.querySelectorAll(".over,.dragging").forEach(x => x.classList.remove("over", "dragging")); };
    el.ondragover = e => { if (drag && drag !== id) { e.preventDefault(); el.classList.add("over"); } };
    el.ondragleave = () => el.classList.remove("over");
    el.ondrop = e => {
      e.preventDefault(); if (!drag || drag === id) return;
      const rest = ids.filter(x => x !== drag), at = rest.indexOf(id);
      const r = el.getBoundingClientRect(), after = e.clientX > r.left + r.width / 2;
      rest.splice(at + (after ? 1 : 0), 0, drag); reorder(sid, rest);
    };
    el.querySelectorAll("button").forEach(b => b.onclick = () => {
      const i = ids.indexOf(id), next = ids.slice();
      if (b.dataset.act === "left" && i > 0) { [next[i - 1], next[i]] = [next[i], next[i - 1]]; reorder(sid, next); }
      if (b.dataset.act === "right" && i < ids.length - 1) { [next[i + 1], next[i]] = [next[i], next[i + 1]]; reorder(sid, next); }
      if (b.dataset.act === "rm") { next.splice(i, 1); reorder(sid, next); }
    });
  });
}
function renderToc() {
  const toc = document.getElementById("toc");
  const rows = Object.entries(DOC.attractions).map(([sid, a]) => {
    const n = Object.keys(sel[sid] || {}).length, inSite = (DOC.applied || {})[sid] || 0;
    return { sid, a, n, inSite };
  });
  const link = r => `<a href="#p-${esc(r.sid)}" title="${r.a.candidates.length} candidates"><span>${esc(r.a.name)}</span>
      <span class="badge ${r.n >= 3 ? "ok" : r.n ? "part" : ""}">${r.n}${r.inSite ? ` <small>(+${r.inSite} in site)</small>` : ""}${r.a.candidates.length ? "" : " <small>none found</small>"}</span></a>`;
  const needs = rows.filter(r => !r.inSite);
  const have = rows.filter(r => r.inSite);
  const btn = (v, t) => `<button type="button" data-f="${v}" class="${filter === v ? "on" : ""}">${t}</button>`;
  const keep = toc.scrollTop;
  toc.innerHTML = `<div class="tools">${btn("all", "All")}${btn("needs", "Needs photos")}${btn("selected", "Selected")}</div>
    <h2>Needs photos (${needs.length})</h2>${needs.map(link).join("")}
    <h2>Already have photos (${have.length})</h2>${have.map(link).join("")}`;
  toc.scrollTop = keep;
  toc.querySelectorAll("[data-f]").forEach(b => b.onclick = () => { filter = b.dataset.f; render(); });
}
document.getElementById("dlg").onclick = e => e.currentTarget.close();
const selectionDoc = () => {
  const out = { schemaVersion: 1, selectedAt: new Date().toISOString().slice(0,10), selections: {} };
  for (const [sid, picks] of Object.entries(sel)) {
    const ids = Object.keys(picks);                       // insertion order is the gallery order
    if (!ids.length) { if ((DOC.applied || {})[sid]) out.selections[sid] = []; continue; }   // [] = clear the site gallery
    out.selections[sid] = ids.map(id => ({ id, objectPosition: picks[id].objectPosition }));
  }
  return out;
};
document.getElementById("export").onclick = () => {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(selectionDoc(), null, 1)], { type: "application/json" }));
  a.download = "selection.json"; a.click();
};
// Chrome and Edge can keep a handle to one file: pick selection.json once, then every save overwrites it.
const state = msg => { document.getElementById("filestate").textContent = msg; };
const hasPicker = "showSaveFilePicker" in window;
const idb = () => new Promise((res, rej) => { const r = indexedDB.open("fda-review", 1); r.onupgradeneeded = () => r.result.createObjectStore("h"); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
const putHandle = async h => { try { const db = await idb(); db.transaction("h", "readwrite").objectStore("h").put(h, "selection"); } catch (e) {} };
const getHandle = async () => { try { const db = await idb(); return await new Promise(res => { const q = db.transaction("h").objectStore("h").get("selection"); q.onsuccess = () => res(q.result); q.onerror = () => res(null); }); } catch (e) { return null; } };
const FILE_TYPES = [{ description: "Selection JSON", accept: { "application/json": [".json"] } }];
async function writable(handle) { return (await handle.queryPermission({ mode: "readwrite" })) === "granted" || (await handle.requestPermission({ mode: "readwrite" })) === "granted"; }
document.getElementById("save").onclick = async () => {
  if (!hasPicker) { document.getElementById("export").click(); state("This browser cannot save into a file; downloaded a copy instead."); return; }
  try {
    let handle = await getHandle();
    if (!handle || !(await writable(handle))) {
      handle = await window.showSaveFilePicker({ suggestedName: "selection.json", types: FILE_TYPES });
      await putHandle(handle);
    }
    const w = await handle.createWritable();
    await w.write(JSON.stringify(selectionDoc(), null, 1));
    await w.close();
    state(`Saved into ${handle.name} at ${new Date().toLocaleTimeString()}`);
  } catch (e) { if (e.name !== "AbortError") state("Could not save: " + e.message); }
};
document.getElementById("open").onclick = async () => {
  if (!("showOpenFilePicker" in window)) { state("This browser cannot open a file here; your picks are kept in the browser anyway."); return; }
  try {
    const [handle] = await window.showOpenFilePicker({ types: FILE_TYPES });
    const doc = JSON.parse(await (await handle.getFile()).text());
    for (const [sid, picks] of Object.entries(doc.selections || {})) {
      sel[sid] = sel[sid] || {};
      for (const p of picks) if (Object.keys(sel[sid]).length < 5) sel[sid][p.id] = { objectPosition: p.objectPosition || "center" };
    }
    await putHandle(handle);
    save();
    state(`Loaded ${handle.name}; saving will overwrite it`);
  } catch (e) { if (e.name !== "AbortError") state("Could not open: " + e.message); }
};
if (!hasPicker) document.getElementById("save").textContent = "Download selection";
render();
</script></body></html>
"""

if __name__ == "__main__":
    sys.exit(main())
