"""Make an HTML page for editing the rating inputs (stars, number of reviews, place in the ranking) of every place.

    python tools/content/edit_ratings.py is [--open]

Writes ~/.finiteplay/score-inputs/edit-<cc>.html (outside the repository, because it holds other sites' raw numbers) and
prints its path. In the page, pick or fix the numbers per place and source, watch the traveler score preview update, then
"Save to is.json" (Chrome or Edge keep the file handle, so every save overwrites the same file, like the photo review page).
Finally run `python tools/content/build_score.py is` to write the scores into sights.yaml.

The preview uses the same formula as build_score.py (method v1). Ranks are kept for reference and are not part of the score.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_score import METHOD, ROOT, SHRINK, inputs_path, read  # noqa: E402

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Rating inputs · __CC__</title>
<style>
:root{--ink:#153235;--muted:#5d706e;--paper:#f3f0e8;--card:#fffdf8;--line:rgba(21,50,53,.18);--accent:#173d42;--gold:#e4b85c;--bad:#b3261e;--warn:#b26a00;--ok:#2f6b3a}
@media (prefers-color-scheme:dark){:root{--ink:#e8efee;--muted:#9fb3b0;--paper:#0f1e21;--card:#162a2e;--line:rgba(232,239,238,.18);--accent:#4fa3a5;--gold:#e4b85c}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.45 system-ui,Segoe UI,sans-serif}
header{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:10px 16px;background:var(--card);border-bottom:1px solid var(--line)}
header h1{font-size:1rem;margin:0 auto 0 0}header .sub{color:var(--muted);font-size:.8rem}
button,select,input{font:inherit;color:inherit}
button{padding:6px 12px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}
button.alt{background:transparent;color:var(--ink);border-color:var(--line)}button.on{background:var(--accent);color:#fff}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 16px}
.bar input[type=search]{padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);min-width:200px}
main{padding:0 16px 60px}
table{border-collapse:collapse;width:100%;min-width:1080px;background:var(--card);border:1px solid var(--line);border-radius:10px}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
thead th{position:sticky;top:49px;background:var(--card);z-index:3;font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
th.src,td.src{border-left:2px solid var(--line)}
td input{width:100%;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:transparent}
td input::placeholder{color:var(--muted);opacity:.45;font-size:.78rem}td input.rate{width:62px}td input.cnt{width:84px}td input.rank{width:62px}td input.of{width:170px}
td input.bad{border-color:var(--bad);background:rgba(179,38,30,.08)}td input.warn{border-color:var(--warn)}
.name{font-weight:600}.region{color:var(--muted);font-size:.78rem}
.score{font-weight:800;font-size:1.05rem;color:var(--ok)}.score.none{color:var(--muted);font-weight:400}
.flag{display:inline-block;margin-top:2px;font-size:.72rem;color:var(--warn)}
.note{width:100%;min-width:150px}
tr.attn td:first-child{box-shadow:inset 3px 0 var(--warn)}
#state{color:var(--muted);font-size:.8rem}
</style></head><body>
<header><h1>Rating inputs · __CC__ <span class="sub">stars out of 5 · number of reviews · place in the ranking</span></h1>
<span id="state"></span>
<button id="open" class="alt" type="button">Open is.json</button><button id="save" type="button">Save to is.json</button><button id="dl" class="alt" type="button">Download copy</button></header>
<div class="bar"><input id="q" type="search" placeholder="Search places">
<button class="alt on" data-f="all" type="button">All</button><button class="alt" data-f="attn" type="button">Needs attention</button><button class="alt" data-f="missing" type="button">Missing a source</button>
<span style="margin-left:auto">Sort <select id="sort"><option value="score">Score</option><option value="name">Name</option><option value="region">Region</option><option value="data">Original order</option></select></span>
<span id="count" class="sub"></span></div>
<main><table><thead><tr><th>Place</th>
<th class="src">TripAdvisor stars</th><th># reviews</th><th>Place # in ranking</th><th>Ranking list</th><th class="src">Google stars</th><th># reviews</th><th>Place #</th><th class="src">Score /10 (preview)</th><th>Note</th></tr></thead><tbody id="rows"></tbody></table></main>
<script>
const DATA = __DATA__;
const SHRINK = __SHRINK__;
const SOURCES = ["tripadvisor", "google"];
let inputs = DATA.inputs, filter = "all";
const num = v => (v === "" || v == null || isNaN(Number(v))) ? null : Number(v);
const okRating = v => { const n = num(v); return n != null && n >= 1 && n <= 5 ? n : null; };

function blend() {
  const mean = {};
  for (const s of SOURCES) {
    const r = Object.values(inputs.places).map(p => okRating(p[s]?.rating)).filter(v => v != null);
    mean[s] = r.length ? r.reduce((a, b) => a + b, 0) / r.length : 0;
  }
  const out = {};
  for (const [id, p] of Object.entries(inputs.places)) {
    let t = 0, w = 0, used = 0;
    for (const s of SOURCES) {
      const r = okRating(p[s]?.rating), n = num(p[s]?.reviews);
      if (r == null || !n || n < 0) continue;
      t += Math.log10(1 + n) * ((n * r + SHRINK * mean[s]) / (n + SHRINK)); w += Math.log10(1 + n); used++;
    }
    if (used) out[id] = { value: Math.round(t / w * 2 * 100) / 100, sources: used };
  }
  return out;
}

function flags(p) {
  const f = [];
  for (const s of SOURCES) {
    const e = p[s] || {}, r = num(e.rating), n = num(e.reviews);
    if (r != null && !n) f.push(s + ": rating without a review count (not scored)");
    if (r == null && n) f.push(s + ": review count without a rating");
    if (n != null && n > 0 && n < 30) f.push(s + ": only " + n + " reviews");
  }
  const a = num(p.tripadvisor?.rating), b = num(p.google?.rating);
  if (a != null && b != null && Math.abs(a - b) >= 0.5) f.push("sources differ by " + Math.abs(a - b).toFixed(1));
  return f;
}
const hasBoth = p => SOURCES.every(s => num(p[s]?.rating) != null && num(p[s]?.reviews));

function field(id, s, key, cls, extra = "") {
  const v = inputs.places[id]?.[s]?.[key];
  return `<input class="${cls}" data-id="${id}" data-s="${s}" data-k="${key}" value="${v == null ? "" : String(v).replace(/"/g, "&quot;")}" ${extra}>`;
}

function render() {
  const scores = blend(), q = document.getElementById("q").value.trim().toLowerCase();
  let rows = DATA.places.filter(pl => !q || (pl.name + " " + pl.region).toLowerCase().includes(q));
  rows = rows.filter(pl => { const p = inputs.places[pl.id] || {}; const fl = flags(p);
    return filter === "all" || (filter === "attn" && (fl.length || !scores[pl.id])) || (filter === "missing" && !hasBoth(p)); });
  const by = document.getElementById("sort").value;
  rows.sort((a, b) => by === "name" ? a.name.localeCompare(b.name) : by === "region" ? a.region.localeCompare(b.region) || a.name.localeCompare(b.name)
    : by === "data" ? a.i - b.i : (scores[b.id]?.value ?? -1) - (scores[a.id]?.value ?? -1) || a.i - b.i);
  document.getElementById("rows").innerHTML = rows.map(pl => {
    const p = inputs.places[pl.id] || {}, sc = scores[pl.id], fl = flags(p);
    return `<tr class="${fl.length || !sc ? "attn" : ""}" data-row="${pl.id}"><td><div class="name">${pl.name}</div><div class="region">${pl.region}</div>${fl.map(x => `<div class="flag">⚠ ${x}</div>`).join("")}</td>
      <td class="src">${field(pl.id, "tripadvisor", "rating", "rate", 'inputmode="decimal" placeholder="stars"')}</td>
      <td>${field(pl.id, "tripadvisor", "reviews", "cnt", 'inputmode="numeric" placeholder="reviews"')}</td>
      <td>${field(pl.id, "tripadvisor", "rank", "rank", 'inputmode="numeric" placeholder="#"')}</td>
      <td>${field(pl.id, "tripadvisor", "of", "of", 'placeholder="e.g. 158 things to do in Reykjavik"')}</td>
      <td class="src">${field(pl.id, "google", "rating", "rate", 'inputmode="decimal" placeholder="stars"')}</td>
      <td>${field(pl.id, "google", "reviews", "cnt", 'inputmode="numeric" placeholder="reviews"')}</td>
      <td>${field(pl.id, "google", "rank", "rank", 'inputmode="numeric" placeholder="#"')}</td>
      <td class="src"><span class="score ${sc ? "" : "none"}" data-score="${pl.id}">${sc ? sc.value.toFixed(1) + " <small>(" + sc.sources + " src)</small>" : "not scored"}</span></td>
      <td><input class="note" data-id="${pl.id}" data-s="tripadvisor" data-k="note" value="${(p.tripadvisor?.note || "").replace(/"/g, "&quot;")}"></td></tr>`;
  }).join("");
  document.getElementById("count").textContent = `${rows.length} of ${DATA.places.length} places · ${Object.keys(scores).length} scored`;
  validate();
}

function validate() {
  document.querySelectorAll("#rows input").forEach(inp => {
    const k = inp.dataset.k, v = inp.value.trim(); let bad = false, warn = false;
    if (v !== "") {
      if (k === "rating") bad = !(Number(v) >= 1 && Number(v) <= 5);
      if (k === "reviews" || k === "rank") bad = !(Number.isInteger(Number(v)) && Number(v) >= 0);
      if (k === "reviews" && !bad && Number(v) > 0 && Number(v) < 30) warn = true;
    }
    inp.classList.toggle("bad", bad); inp.classList.toggle("warn", warn);
  });
}

function setValue(id, s, k, raw) {
  const p = (inputs.places[id] = inputs.places[id] || {});
  const e = (p[s] = p[s] || {});
  const v = raw.trim();
  if (v === "") delete e[k];
  else if (k === "rating" || k === "reviews" || k === "rank") e[k] = num(v.replace(/[, ]/g, "")) ?? v;
  else e[k] = v;
  if (!Object.keys(e).length) delete p[s];
}

document.getElementById("rows").addEventListener("input", ev => {
  const t = ev.target; if (!t.dataset.id) return;
  setValue(t.dataset.id, t.dataset.s, t.dataset.k, t.value); dirty(true);
  const scores = blend(), sc = scores[t.dataset.id], el = document.querySelector(`[data-score="${t.dataset.id}"]`);
  if (el) { el.className = "score " + (sc ? "" : "none"); el.innerHTML = sc ? sc.value.toFixed(1) + " <small>(" + sc.sources + " src)</small>" : "not scored"; }
  validate();
  document.getElementById("count").textContent = `${document.querySelectorAll("#rows tr").length} shown · ${Object.keys(scores).length} scored (re-sort to refresh order)`;
});
document.getElementById("q").addEventListener("input", render);
document.getElementById("sort").addEventListener("change", render);
document.querySelectorAll("[data-f]").forEach(b => b.onclick = () => { filter = b.dataset.f; document.querySelectorAll("[data-f]").forEach(x => x.classList.toggle("on", x === b)); render(); });

// ---- save / open: one file, kept as a handle (Chrome/Edge); other browsers download a copy ----
const state = m => document.getElementById("state").textContent = m;
const dirty = d => { if (d) state("Unsaved changes"); };
const doc = () => { const out = JSON.parse(JSON.stringify(inputs)); out.editedAt = new Date().toISOString().slice(0, 10); return JSON.stringify(out, null, 1); };
const hasPicker = "showSaveFilePicker" in window;
const idb = () => new Promise((res, rej) => { const r = indexedDB.open("mfv-ratings", 1); r.onupgradeneeded = () => r.result.createObjectStore("h"); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
const putH = async h => { try { (await idb()).transaction("h", "readwrite").objectStore("h").put(h, "inputs"); } catch (e) {} };
const getH = async () => { try { const db = await idb(); return await new Promise(res => { const q = db.transaction("h").objectStore("h").get("inputs"); q.onsuccess = () => res(q.result); q.onerror = () => res(null); }); } catch (e) { return null; } };
const TYPES = [{ description: "Rating inputs JSON", accept: { "application/json": [".json"] } }];
const writable = async h => (await h.queryPermission({ mode: "readwrite" })) === "granted" || (await h.requestPermission({ mode: "readwrite" })) === "granted";
function download() { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([doc()], { type: "application/json" })); a.download = "__CC__.json"; a.click(); }
document.getElementById("dl").onclick = download;
document.getElementById("save").onclick = async () => {
  if (!hasPicker) { download(); state("This browser cannot save into a file; downloaded a copy."); return; }
  try {
    let h = await getH();
    if (!h || !(await writable(h))) { h = await window.showSaveFilePicker({ suggestedName: "__CC__.json", types: TYPES }); await putH(h); }
    const w = await h.createWritable(); await w.write(doc()); await w.close();
    state(`Saved into ${h.name} at ${new Date().toLocaleTimeString()}. Now run build_score.py.`);
  } catch (e) { if (e.name !== "AbortError") state("Could not save: " + e.message); }
};
document.getElementById("open").onclick = async () => {
  if (!("showOpenFilePicker" in window)) { state("This browser cannot open a file here; edit what is shown and download a copy."); return; }
  try {
    const [h] = await window.showOpenFilePicker({ types: TYPES });
    const loaded = JSON.parse(await (await h.getFile()).text());
    if (!loaded.places) throw new Error("not a rating inputs file");
    inputs = loaded; await putH(h); render(); state(`Loaded ${h.name}; saving will overwrite it`);
  } catch (e) { if (e.name !== "AbortError") state("Could not open: " + e.message); }
};
window.addEventListener("beforeunload", e => { if (document.getElementById("state").textContent === "Unsaved changes") { e.preventDefault(); e.returnValue = ""; } });
render();
</script></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    args = ap.parse_args()
    sights = read(ROOT / "content" / args.country / "sights.yaml")
    path = inputs_path(args.country)
    inputs = read(path) if path.exists() else {"asOf": "", "places": {}}
    places = [{"id": it["id"], "name": it["name"], "region": it.get("region", ""), "i": i} for i, it in enumerate(sights["items"])]
    for place in places:
        inputs["places"].setdefault(place["id"], {})
    data = {"places": places, "inputs": inputs}
    html = (PAGE.replace("__CC__", args.country).replace("__SHRINK__", str(SHRINK))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    out = path.with_name(f"edit-{args.country}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"{out}\nOpen it in Chrome or Edge. Inputs file it saves to: {path} (score method {METHOD})")
    if args.open:
        webbrowser.open(out.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
