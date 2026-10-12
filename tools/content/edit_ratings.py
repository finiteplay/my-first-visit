"""Make an HTML page for editing every place's aggregate stars and its place in our single ranking list.

    python tools/content/edit_ratings.py is [--open]

Writes ~/.finiteplay/score-inputs/edit-<cc>.html (outside the repository: it holds other sites' raw numbers as hints) and
prints its path. In the page:
  * one list for all places; drag a row by its handle (or type a new number in the # box, or use the arrows) to change its
    place. The numbers are always 1..N and only mean something for this website.
  * "Aggregate stars" is our own rating out of 5. It starts as a placeholder copied from a source site (marked "placeholder");
    editing it makes it yours. The grey "average" value is the plain average of the sources' ratings, as build_score.py computes it.
  * the radio buttons set each place's priority for a first visit (Must see, Worth a stop, If you have time).
  * "Save to is.json" overwrites the same file every time (Chrome and Edge keep the file handle).
Then run `python tools/content/build_score.py is` and `python local-site/build.py`.
"""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_score import METHOD, ROOT, inputs_path, load_inputs, read  # noqa: E402

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Ranking and aggregate stars · __CC__</title>
<style>
:root{--ink:#153235;--muted:#5d706e;--paper:#f3f0e8;--card:#fffdf8;--line:rgba(21,50,53,.18);--accent:#173d42;--gold:#e4b85c;--bad:#b3261e;--warn:#b26a00;--ok:#2f6b3a;--drop:#e4b85c}
@media (prefers-color-scheme:dark){:root{--ink:#e8efee;--muted:#9fb3b0;--paper:#0f1e21;--card:#162a2e;--line:rgba(232,239,238,.18);--accent:#4fa3a5}}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.45 system-ui,Segoe UI,sans-serif}
header{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:10px 16px;background:var(--card);border-bottom:1px solid var(--line)}
header h1{font-size:1rem;margin:0 auto 0 0}header .sub{color:var(--muted);font-size:.8rem;font-weight:400}
button,input{font:inherit;color:inherit}
button{padding:6px 12px;border-radius:8px;border:1px solid var(--accent);background:var(--accent);color:#fff;cursor:pointer}
button.alt{background:transparent;color:var(--ink);border-color:var(--line)}button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
button.mini{padding:1px 7px;font-size:.8rem}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:10px 16px}
.bar input[type=search]{padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);min-width:200px}
main{padding:0 16px 60px}
table{border-collapse:collapse;width:100%;min-width:900px;background:var(--card);border:1px solid var(--line)}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:middle}
thead th{position:sticky;top:49px;background:var(--card);z-index:3;font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
td.h{width:34px;text-align:center;cursor:grab;color:var(--muted);font-size:1.2rem;user-select:none}td.h:active{cursor:grabbing}
td.pos input{width:58px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:transparent;font-weight:700;text-align:center}
td input.stars{width:70px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;background:transparent;font-weight:700}
td input.stars.bad{border-color:var(--bad);background:rgba(179,38,30,.08)}
.tiers{display:flex;gap:12px;flex-wrap:nowrap}.tiers label{display:inline-flex;align-items:center;gap:4px;white-space:nowrap;cursor:pointer}
.tiers input{accent-color:var(--accent)}
.name{font-weight:600}.region{color:var(--muted);font-size:.78rem}
.tag{display:inline-block;margin-left:6px;padding:0 7px;border-radius:999px;border:1px solid var(--warn);color:var(--warn);font-size:.68rem;font-weight:600}
.sug{color:var(--muted);font-size:.78rem;white-space:nowrap}.sug button{margin-left:4px}
tr.dragging{opacity:.4}tr.over-top td{box-shadow:inset 0 3px 0 var(--drop)}tr.over-bottom td{box-shadow:inset 0 -3px 0 var(--drop)}
tr.ph td:first-child{box-shadow:inset 3px 0 var(--warn)}
#state{color:var(--muted);font-size:.8rem}.hint{color:var(--muted);padding:0 16px 8px;font-size:.8rem}
.moves{white-space:nowrap}
</style></head><body>
<header><h1>Ranking and aggregate stars · __CC__ <span class="sub">one list for all places · stars out of 5</span></h1>
<span id="state"></span>
<button id="open" class="alt" type="button">Open is.json</button><button id="save" type="button">Save to is.json</button><button id="dl" class="alt" type="button">Download copy</button></header>
<div class="bar"><input id="q" type="search" placeholder="Search places">
<button class="alt on" data-f="all" type="button">All</button><button class="alt" data-f="ph" type="button">Placeholders only</button>
<button class="alt" id="bystars" type="button" title="Re-order the whole list by stars, highest first (ties keep their current order)">Sort list by stars</button>
<button class="alt" id="useall" type="button" title="Replace every placeholder with its suggested value">Use suggestions for placeholders</button>
<span id="count" class="sub" style="margin-left:auto"></span></div>
<div class="hint" id="hint">Drag the ⠿ handle to move a place, type a new number in the # box, or use ▲ ▼. Dragging works in the full list (filters off).</div>
<main><table><thead><tr><th></th><th>#</th><th>Place</th><th>Aggregate stars</th><th>Average of sources</th><th>Priority for a first visit</th><th>Move</th></tr></thead><tbody id="rows"></tbody></table></main>
<script>
const DATA = __DATA__;
let inputs = DATA.inputs, filter = "all", dragId = null;
const names = Object.fromEntries(DATA.places.map(p => [p.id, p]));
const TIERS = [["must-see", "Must see"], ["worth-it", "Worth a stop"], ["if-you-have-time", "If you have time"]];
const num = v => (v === "" || v == null || isNaN(Number(v))) ? null : Number(v);
const okStars = v => { const n = num(v); return n != null && n >= 1 && n <= 5; };
const q = () => document.getElementById("q").value.trim().toLowerCase();
const canDrag = () => filter === "all" && !q();
const esc = s => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");

function suggestions() {   // same as build_score.suggest(): plain average of the sources' ratings
  const out = {};
  for (const [id, p] of Object.entries(inputs.places)) {
    const r = Object.values(p.sources || {}).map(v => v.rating).filter(v => v != null);
    if (r.length) out[id] = Math.round(r.reduce((a, b) => a + b, 0) / r.length * 100) / 100;
  }
  return out;
}
const round1 = x => Math.floor(x * 10 + 0.5 + 1e-9) / 10;

function render() {
  const sug = suggestions(), term = q();
  const rows = inputs.order.map((id, i) => ({ id, pos: i + 1 })).filter(r => {
    const pl = names[r.id], p = inputs.places[r.id] || {};
    return (!term || (pl.name + " " + pl.region).toLowerCase().includes(term)) && (filter === "all" || p.placeholder);
  });
  document.getElementById("rows").innerHTML = rows.map(r => {
    const pl = names[r.id], p = inputs.places[r.id] || {}, sg = sug[r.id];
    return `<tr data-id="${r.id}" class="${p.placeholder ? "ph" : ""}" draggable="false">
      <td class="h" title="${canDrag() ? "Drag to move" : "Turn off filters to drag"}">${canDrag() ? "⠿" : ""}</td>
      <td class="pos"><input data-pos="${r.id}" value="${r.pos}" inputmode="numeric" aria-label="Place in ranking for ${esc(pl.name)}"></td>
      <td><span class="name">${esc(pl.name)}</span>${p.placeholder ? '<span class="tag" title="Copied from a source site, not yet reviewed by you">placeholder</span>' : ""}<div class="region">${esc(pl.region)}</div></td>
      <td><input class="stars ${p.stars != null && !okStars(p.stars) ? "bad" : ""}" data-stars="${r.id}" value="${p.stars == null ? "" : p.stars}" inputmode="decimal" placeholder="1–5"></td>
      <td class="sug">${sg != null ? sg.toFixed(2) + ` <button class="alt mini" data-use="${r.id}" type="button" title="Use this value">use</button>` : "–"}</td>
      <td><div class="tiers" role="radiogroup" aria-label="Priority for ${esc(pl.name)}">${TIERS.map(([v, label]) => `<label><input type="radio" name="tier-${r.id}" data-tier="${r.id}" value="${v}" ${p.tier === v ? "checked" : ""}>${label}</label>`).join("")}</div></td>
      <td class="moves"><button class="alt mini" data-up="${r.id}" type="button" aria-label="Move up">▲</button> <button class="alt mini" data-down="${r.id}" type="button" aria-label="Move down">▼</button></td></tr>`;
  }).join("");
  document.getElementById("count").textContent = countText(rows.length);
  document.getElementById("hint").style.opacity = canDrag() ? 1 : .6;
}

function move(id, to) {          // to: 0-based target index in the single list
  const from = inputs.order.indexOf(id); if (from < 0) return;
  to = Math.max(0, Math.min(inputs.order.length - 1, to));
  inputs.order.splice(from, 1); inputs.order.splice(to, 0, id); dirty(); render();
  const el = document.querySelector(`tr[data-id="${id}"]`); if (el) el.scrollIntoView({ block: "nearest" });
}

const rows = document.getElementById("rows");
rows.addEventListener("input", ev => {
  const t = ev.target;
  if (t.dataset.stars) {
    const p = inputs.places[t.dataset.stars], v = t.value.trim();
    if (v === "") delete p.stars; else p.stars = num(v) ?? v;
    delete p.placeholder; t.classList.toggle("bad", v !== "" && !okStars(v));
    const tr = t.closest("tr"); tr.classList.remove("ph"); const tag = tr.querySelector(".tag"); if (tag) tag.remove();
    dirty(); updateCount();
  }
});
function countText(shown) {
  const tc = Object.fromEntries(TIERS.map(([v]) => [v, 0]));
  Object.values(inputs.places).forEach(p => { if (tc[p.tier] != null) tc[p.tier]++; });
  return `${shown} shown of ${inputs.order.length} · ` + TIERS.map(([v, l]) => `${l} ${tc[v]}`).join(" · ");
}
function updateCount() { const n = document.querySelectorAll("#rows tr").length; document.getElementById("count").textContent = countText(n); }
rows.addEventListener("change", ev => {
  const t = ev.target;
  if (t.dataset.tier) { inputs.places[t.dataset.tier].tier = t.value; dirty(); updateCount(); return; }
  if (t.dataset.pos) { const n = parseInt(t.value, 10); if (Number.isInteger(n)) move(t.dataset.pos, n - 1); else render(); }
});
rows.addEventListener("click", ev => {
  const b = ev.target.closest("button"); if (!b) return;
  if (b.dataset.up) move(b.dataset.up, inputs.order.indexOf(b.dataset.up) - 1);
  if (b.dataset.down) move(b.dataset.down, inputs.order.indexOf(b.dataset.down) + 1);
  if (b.dataset.use) { const p = inputs.places[b.dataset.use], s = suggestions()[b.dataset.use]; if (s != null) { p.stars = round1(s); delete p.placeholder; dirty(); render(); } }
});

// ---- drag and drop: grab the handle cell, drop on any row (upper half = before, lower half = after) ----
rows.addEventListener("mousedown", ev => { const h = ev.target.closest("td.h"); if (h && canDrag()) h.parentElement.draggable = true; });
rows.addEventListener("mouseup", () => rows.querySelectorAll("tr").forEach(r => r.draggable = false));
rows.addEventListener("dragstart", ev => { const tr = ev.target.closest("tr"); if (!tr || !canDrag()) { ev.preventDefault(); return; } dragId = tr.dataset.id; tr.classList.add("dragging"); ev.dataTransfer.effectAllowed = "move"; ev.dataTransfer.setData("text/plain", dragId); });
rows.addEventListener("dragover", ev => {
  if (!dragId) return; ev.preventDefault();
  const tr = ev.target.closest("tr"); rows.querySelectorAll(".over-top,.over-bottom").forEach(r => r.classList.remove("over-top", "over-bottom"));
  if (!tr || tr.dataset.id === dragId) return;
  const r = tr.getBoundingClientRect(); tr.classList.add(ev.clientY < r.top + r.height / 2 ? "over-top" : "over-bottom");
});
rows.addEventListener("drop", ev => {
  if (!dragId) return; ev.preventDefault();
  const tr = ev.target.closest("tr"); if (!tr || tr.dataset.id === dragId) { dragId = null; render(); return; }
  const r = tr.getBoundingClientRect(), after = ev.clientY >= r.top + r.height / 2;
  const moving = dragId; dragId = null;
  const without = inputs.order.filter(x => x !== moving), at = without.indexOf(tr.dataset.id) + (after ? 1 : 0);
  without.splice(at, 0, moving); inputs.order = without; dirty(); render();
});
rows.addEventListener("dragend", () => { if (dragId) { dragId = null; render(); } });
// keep the page scrolling while dragging near the top or bottom edge
document.addEventListener("dragover", ev => { if (!dragId) return; if (ev.clientY < 110) scrollBy(0, -18); else if (ev.clientY > innerHeight - 60) scrollBy(0, 18); });

document.getElementById("q").addEventListener("input", render);
document.querySelectorAll("[data-f]").forEach(b => b.onclick = () => { filter = b.dataset.f; document.querySelectorAll("[data-f]").forEach(x => x.classList.toggle("on", x === b)); render(); });
document.getElementById("bystars").onclick = () => {
  if (!confirm("Re-order the whole list by aggregate stars, highest first? Places with equal stars keep their current order.")) return;
  const idx = Object.fromEntries(inputs.order.map((id, i) => [id, i]));
  inputs.order.sort((a, b) => (num(inputs.places[b].stars) ?? -1) - (num(inputs.places[a].stars) ?? -1) || idx[a] - idx[b]); dirty(); render();
};
document.getElementById("useall").onclick = () => {
  const sg = suggestions(); let n = 0;
  for (const [id, p] of Object.entries(inputs.places)) if (p.placeholder && sg[id] != null) { p.stars = round1(sg[id]); delete p.placeholder; n++; }
  render(); state(`${n} placeholders replaced by suggestions. Unsaved changes`);
};

// ---- save / open: one file kept as a handle (Chrome/Edge); other browsers download a copy ----
const state = m => document.getElementById("state").textContent = m;
const dirty = () => state("Unsaved changes");
const doc = () => JSON.stringify(Object.assign({}, inputs, { editedAt: new Date().toISOString().slice(0, 10) }), null, 1);
const hasPicker = "showSaveFilePicker" in window;
const idb = () => new Promise((res, rej) => { const r = indexedDB.open("mfv-ranking", 1); r.onupgradeneeded = () => r.result.createObjectStore("h"); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
const putH = async h => { try { (await idb()).transaction("h", "readwrite").objectStore("h").put(h, "inputs"); } catch (e) {} };
const getH = async () => { try { const db = await idb(); return await new Promise(res => { const g = db.transaction("h").objectStore("h").get("inputs"); g.onsuccess = () => res(g.result); g.onerror = () => res(null); }); } catch (e) { return null; } };
const TYPES = [{ description: "Ranking inputs JSON", accept: { "application/json": [".json"] } }];
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
  if (!("showOpenFilePicker" in window)) { state("This browser cannot open a file here."); return; }
  try {
    const [h] = await window.showOpenFilePicker({ types: TYPES });
    const loaded = JSON.parse(await (await h.getFile()).text());
    if (loaded.schemaVersion !== 2 || !loaded.order) throw new Error("not a ranking inputs file (run edit_ratings.py to upgrade it)");
    inputs = loaded; await putH(h); render(); state(`Loaded ${h.name}; saving will overwrite it`);
  } catch (e) { if (e.name !== "AbortError") state("Could not open: " + e.message); }
};
window.addEventListener("beforeunload", e => { if (document.getElementById("state").textContent.includes("Unsaved")) { e.preventDefault(); e.returnValue = ""; } });
render();
</script></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("country")
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    args = ap.parse_args()
    sights = read(ROOT / "content" / args.country / "sights.yaml")
    ids = [it["id"] for it in sights["items"]]
    path = inputs_path(args.country)
    inputs = load_inputs(path, ids)
    for it in sights["items"]:  # the priority starts as the one already in sights.yaml
        inputs["places"][it["id"]].setdefault("tier", it.get("tier", "if-you-have-time"))
    places = [{"id": it["id"], "name": it["name"], "region": it.get("region", "")} for it in sights["items"]]
    data = {"places": places, "inputs": inputs}
    html = (PAGE.replace("__CC__", args.country)
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    out = path.with_name(f"edit-{args.country}.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    # also persist the upgraded inputs so a later Open/Save round-trips the same layout
    path.write_text(json.dumps(inputs, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{out}\nOpen it in Chrome or Edge. It saves to: {path} (method {METHOD}); then run build_score.py")
    if args.open:
        webbrowser.open(out.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
