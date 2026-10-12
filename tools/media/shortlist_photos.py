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
        kept += [x for x in existing.get("attractions", {}).get(sid, {}).get("candidates", [])
                 if "-m" in x["id"] and x["sourceUrl"] not in {k["sourceUrl"] for k in kept}]
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
main{padding:16px;max-width:1400px;margin:auto}
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
.warn{color:var(--warn);font-weight:600}
select{font:inherit;font-size:.75rem}
dialog{max-width:95vw;padding:0;border:0;background:#000} dialog img{max-width:95vw;max-height:90vh;display:block}
</style></head><body>
<header><h1>Photo shortlist: choose 3–5 per attraction (1–2 = partial)</h1>
<span id="total"></span><button id="export">Download selection</button></header>
<main id="m"></main>
<dialog id="dlg"><img id="dlgimg" alt=""></dialog>
<script>
const DOC = __DATA__;
const KEY = "fda-photo-selection";
let sel = {};
try { sel = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
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
    const s = document.createElement("section");
    s.innerHTML = `<h2>${esc(a.name)} <span class="sub">(${esc(a.local)})</span></h2>
      <p class="sub"><span class="count ${n>=3?"ok":"bad"}">${n} selected${n>=1&&n<3?" (partial, can add more later)":""}</span> · ${a.candidates.length} verified candidates
      ${a.shortfall ? `· <span class="warn">${esc(a.shortfall)}</span>` : ""}
      · rejected: ${esc(Object.entries(a.rejectedCounts||{}).map(([k,v])=>k+" "+v).join(", ") || "none")}</p>
      <div class="grid"></div>`;
    const g = s.querySelector(".grid");
    for (const c of a.candidates) {
      const p = picks[c.id];
      const pos = p?.objectPosition || "center";
      const d = document.createElement("div");
      d.className = "c" + (p ? " sel" : "");
      d.innerHTML = `<label class="pick"><input type="checkbox" ${p?"checked":""}> Select ${esc(c.id)}</label>
        <img class="full" src="${esc(c.thumb)}" alt="${esc(c.title)}" loading="lazy">
        <div class="prev">
          <div><div class="frame r32 cover"><img src="${esc(c.thumb)}" alt="" style="object-position:${pos}"></div>card 3:2 crop</div>
          <div><div class="frame r169 cover"><img src="${esc(c.thumb)}" alt="" style="object-position:${pos}"></div>popup 16:9</div>
          <div><div class="frame r21 cover"><img src="${esc(c.thumb)}" alt="" style="object-position:${pos}"></div>banner 21:9</div>
        </div>
        <div class="meta">Focus <select>${POS.map(x=>`<option ${x===pos?"selected":""}>${x}</option>`).join("")}<option value="contain" ${pos==="contain"?"selected":""}>contain (no crop)</option></select><br>
        ${esc(c.width)}×${esc(c.height)} (${esc(c.ratio)}) · ${esc(c.source)}<br>
        <b>${esc(c.license)}</b> · ${esc(c.author)}<br>
        <a href="${esc(c.sourceUrl)}" target="_blank" rel="noopener">file page</a> · ${esc(c.title)}
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
  document.getElementById("total").textContent = `${done}/${total} attractions have photos (3–5 complete, 1–2 partial)`;
}
document.getElementById("dlg").onclick = e => e.currentTarget.close();
document.getElementById("export").onclick = () => {
  const out = { schemaVersion: 1, selectedAt: new Date().toISOString().slice(0,10), selections: {} };
  for (const [sid, picks] of Object.entries(sel)) {
    const ids = Object.keys(picks); if (!ids.length) continue;
    out.selections[sid] = ids.map(id => ({ id, objectPosition: picks[id].objectPosition }));
  }
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 1)], { type: "application/json" }));
  a.download = "selection.json"; a.click();
};
render();
</script></body></html>
"""

if __name__ == "__main__":
    sys.exit(main())
