#!/usr/bin/env python3
"""Generate apps/hub/index.html — the tabbed launcher for this repo.

Everything the page shows is read from files that are already the source of
truth:

    apps/hub/engines.json  registry of engines/apps (one tab each)
    hack/species.json      Evolved starter data (Species tab)
    VERSION                project version
    engines/VENDOR.md      pinned upstream commit for gen1recomp

The data is inlined into the generated HTML rather than fetched at runtime.
That is deliberate: the page has to work when opened straight off disk as a
file:// URL, and browsers block fetch() of local JSON under that scheme.

Usage:  python3 apps/hub/build_hub.py
"""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / "apps" / "hub"

TYPE_COLORS = {
    "GRASS": "#4ade80", "POISON": "#c084fc", "FIRE": "#fb923c",
    "FLYING": "#93c5fd", "WATER": "#38bdf8", "STEEL": "#94a3b8",
    "DRAGON": "#818cf8",
}
LINE_ACCENT = {"grass": "#4ade80", "fire": "#fb923c", "water": "#38bdf8"}
STATUS_LABEL = {
    "playable": ("Playable now", "ok"),
    "buildable": ("Builds a ROM", "warn"),
    "planned": ("Planned", "idle"),
    "in progress": ("In progress", "warn"),
}


def e(v) -> str:
    """Escape a value for HTML text/attribute content."""
    return html.escape(str(v), quote=True)


def read_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def pinned_commit(vendor_md: Path) -> str:
    """Pull the pinned gen1recomp commit out of engines/VENDOR.md."""
    if not vendor_md.exists():
        return "unknown"
    m = re.search(r"\*\*Pinned commit:\*\*\s*`([0-9a-f]{7,40})`", vendor_md.read_text(encoding="utf-8"))
    return m.group(1) if m else "unknown"


# --------------------------------------------------------------- fragments

def tw(table_html: str) -> str:
    """Wrap a table so it scrolls inside its own box instead of widening the page.

    Long content (SHA-1 hashes, shell commands) cannot wrap usefully, so on a
    phone the table has to scroll horizontally on its own. Without this the
    table sets a floor on the page width and the whole body scrolls sideways.
    """
    return f'<div class="tablewrap">{table_html}</div>'


def status_pill(status: str) -> str:
    label, cls = STATUS_LABEL.get(status, (status, "idle"))
    return f'<span class="pill {cls}">{e(label)}</span>'


def type_chips(types) -> str:
    if not types:
        return ""
    # A mono-typed species is stored with its type repeated; show it once.
    seen, uniq = set(), []
    for t in types:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    return "".join(
        f'<span class="type" style="--t:{TYPE_COLORS.get(t, "#8b9bc0")}">{e(t.title())}</span>'
        for t in uniq
    )


def trigger_text(mon: dict) -> str:
    method, param = mon.get("method"), mon.get("param")
    if method == "LEVEL":
        return f"Lv {param}"
    if method == "ITEM":
        return str(param).replace("_", " ").title()
    return str(param or "")


def stage_card(name: str, sub: str, extra: str = "", accent: str | None = None) -> str:
    style = f' style="--accent:{accent}"' if accent else ""
    return (
        f'<div class="stage"{style}>'
        f'<div class="stage-name">{e(name.title())}</div>'
        f'<div class="stage-sub">{e(sub)}</div>'
        f'{extra}</div>'
    )


def chain_html(vanilla, branch, accent) -> str:
    parts = [stage_card(n, "base", accent=accent) for n in vanilla]
    for mon in branch:
        parts.append(stage_card(
            mon["name"], trigger_text(mon),
            f'<div class="types">{type_chips(mon.get("types"))}</div>'
            f'<div class="ability">{e(str(mon.get("ability", "")).replace("_", " ").title())}</div>',
            accent,
        ))
    return '<div class="chain">' + '<span class="arrow">&rsaquo;</span>'.join(parts) + '</div>'


def species_tab(species: dict) -> str:
    vanilla = species.get("vanilla_starters", {})
    official = species.get("official", {})
    diy = species.get("diy", {})
    meta = species.get("meta", {})

    total = sum(len(v) for v in official.values()) + sum(len(v) for v in diy.values())

    out = [
        '<p class="lead">Every species below is generated from '
        '<code>hack/species.json</code>, the single source of truth shared by the '
        'Emerald build scripts and this page. '
        f'<strong>{total}</strong> new forms across '
        f'<strong>{len(official)}</strong> starter lines.</p>',
        '<div class="legend">'
        '<span class="key official">Official — Pokémon Evolved</span>'
        '<span class="key diy">DIY — our alternate branches</span>'
        '</div>',
    ]

    for line in ("grass", "fire", "water"):
        if line not in vanilla:
            continue
        accent = LINE_ACCENT.get(line, "#8b9bc0")
        out.append(f'<section class="line-card" style="--accent:{accent}">')
        out.append(f'<h3 class="line-title">{e(line.title())} line</h3>')

        if official.get(line):
            out.append('<div class="branch-label official">Official — level-up path</div>')
            out.append(chain_html(vanilla[line], official[line], accent))
        if diy.get(line):
            out.append('<div class="branch-label diy">DIY — stone divergence</div>')
            out.append(chain_html(vanilla[line], diy[line], accent))
            notes = [m["note"] for m in diy[line] if m.get("note")]
            if notes:
                out.append(f'<p class="note">{e(notes[0])}</p>')
        out.append('</section>')

    if meta:
        rows = "".join(
            f'<tr><th>{e(k.replace("_", " ").title())}</th><td>{e(v)}</td></tr>'
            for k, v in meta.items()
        )
        out.append(tw(f'<table class="meta"><caption>Data provenance</caption>{rows}</table>'))

    return "\n".join(out)


def rom_block(rom: dict | None) -> str:
    if not rom:
        return ""
    rows = "".join(
        f'<tr><td>{e(h["label"])}</td><td><code>{e(h["sha1"])}</code></td></tr>'
        for h in rom.get("hashes", [])
    )
    return (
        '<div class="rom">'
        '<h4>You supply the game content</h4>'
        f'<p>{e(rom.get("note", ""))}</p>'
        + tw(f'<table class="hashes"><tr><th>ROM</th><th>SHA-1</th></tr>{rows}</table>')
        + '</div>'
    )


def app_tab(app: dict) -> str:
    out = [
        f'<div class="tab-head"><h2>{e(app["title"])}</h2>{status_pill(app["status"])}</div>',
        f'<p class="lead">{e(app["summary"])}</p>',
        '<dl class="facts">'
        f'<dt>Engine</dt><dd>{e(app["engine"])}</dd>'
        + (f'<dt>Location</dt><dd><code>{e(app["path"])}</code></dd>' if app.get("path") else "")
        + '</dl>',
    ]

    if app.get("launch"):
        rows = "".join(
            f'<tr><td>{e(l["os"])}</td><td><code>{e(l["cmd"])}</code></td>'
            f'<td class="muted">{e(l.get("note", ""))}</td></tr>'
            for l in app["launch"]
        )
        out.append('<h4>Launch</h4>' + tw(f'<table class="launch">{rows}</table>'))

    if app.get("steps"):
        items = "".join(f'<li><code>{e(s)}</code></li>' if "  " not in s and (
            s.startswith(("python3", "make", "cd", "./")) or " — " in s
        ) else f"<li>{e(s)}</li>" for s in app["steps"])
        out.append(f'<h4>Steps</h4><ol class="steps">{items}</ol>')

    out.append(rom_block(app.get("rom")))

    if app.get("links"):
        links = "".join(
            f'<a class="link" href="{e(l["href"])}">{e(l["label"])}</a>' for l in app["links"]
        )
        out.append(f'<h4>Links</h4><div class="links">{links}</div>')

    return "\n".join(out)


def roadmap_tab(intro: dict | None, roadmap: list) -> str:
    out = []
    if intro:
        out.append(f'<div class="tab-head"><h2>{e(intro["title"])}</h2>{status_pill(intro["status"])}</div>')
        out.append(f'<p class="lead">{e(intro["summary"])}</p>')
    for item in roadmap:
        out.append(
            '<section class="road">'
            f'<div class="road-head"><h3>{e(item["title"])}</h3>{status_pill(item["status"])}</div>'
            f'<p>{e(item["detail"])}</p>'
            + (f'<p class="ref"><code>{e(item["reference"])}</code></p>' if item.get("reference") else "")
            + '</section>'
        )
    return "\n".join(out)


def home_tab(apps: list, version: str, commit: str) -> str:
    cards = []
    for app in apps:
        cards.append(
            f'<button class="card" data-goto="{e(app["id"])}" style="--accent:{LINE_ACCENT.get("water") if app["id"] == "gen1" else LINE_ACCENT.get("fire") if app["id"] == "emerald" else "#a78bfa"}">'
            f'<div class="card-head"><span class="card-gen">{"Gen " + str(app["gen"]) if app.get("gen") else "Next"}</span>{status_pill(app["status"])}</div>'
            f'<h3>{e(app["title"])}</h3>'
            f'<p>{e(app["summary"][:180])}{"…" if len(app["summary"]) > 180 else ""}</p>'
            f'<span class="card-cta">Open tab &rarr;</span>'
            '</button>'
        )
    return f"""
<p class="lead">One repository, three tracks: the Gen 1 engine you can play right
now, the Emerald ROM hack this project started as, and the Evolved species data
shared between them. Each has its own tab — nothing was overwritten to fit them
together.</p>

<div class="cards">{''.join(cards)}</div>

<section class="callout">
  <h4>No ROMs are included here — by design</h4>
  <p>Both engines require game content you already own. gen1recomp verifies your
  Red/Blue/Yellow cartridge dump by SHA-1 at import time and releases it from
  memory afterwards; the Emerald decomp builds against your own Emerald ROM.
  Nothing in this repository ships game data.</p>
</section>

<section class="callout">
  <h4>How the merge is laid out</h4>
  <p>The repo root stays a clean pokeemerald decompilation — the Emerald build is
  untouched. gen1recomp is vendored under <code>engines/gen1recomp</code> rather
  than flattened into the root, because both projects define
  <code>src/</code>, <code>tools/</code>, <code>data/</code> and
  <code>assets/</code> with incompatible contents; overlaying them would break
  the Emerald build outright. See <a href="../../engines/VENDOR.md">engines/VENDOR.md</a>.</p>
</section>

<dl class="facts">
  <dt>Project version</dt><dd><code>{e(version)}</code></dd>
  <dt>gen1recomp pinned at</dt><dd><code>{e(commit[:12])}</code></dd>
  <dt>Page generated</dt><dd>{e(date.today().isoformat())}</dd>
</dl>
"""


# ------------------------------------------------------------------ page

CSS = """
:root{--bg:#0a0e1a;--panel:#121a2e;--panel2:#0d1324;--line:#2a3858;--text:#e8edf8;
--muted:#8b9bc0;--dim:#5c6b8a;--official:#fbbf24;--diy:#a78bfa;--ok:#4ade80;--warn:#fb923c}
*{box-sizing:border-box;margin:0;padding:0;min-width:0}
html{-webkit-text-size-adjust:100%}
body{font-family:"Segoe UI",system-ui,-apple-system,sans-serif;
background:radial-gradient(ellipse at top,#1a2540 0%,var(--bg) 55%) no-repeat;
background-color:var(--bg);color:var(--text);line-height:1.6;min-height:100vh;
overflow-wrap:break-word}
.wrap{max-width:1100px;margin:0 auto;padding:0 1rem 4rem}
header{text-align:center;padding:2.5rem 1rem 1.5rem}
header h1{font-size:clamp(1.35rem,5.5vw,2.4rem);letter-spacing:-.02em}
header p{color:var(--muted);max-width:720px;margin:.6rem auto 0}
/* Nav is a scrollable strip rather than a wrapping block: at phone widths the
   five tabs wrapped to a second row and clipped the last label. */
nav{position:sticky;top:0;z-index:10;display:flex;gap:.35rem;flex-wrap:nowrap;
justify-content:flex-start;padding:.6rem .75rem;background:rgba(10,14,26,.92);
backdrop-filter:blur(8px);border-bottom:1px solid var(--line);margin-bottom:1.75rem;
overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;
scroll-snap-type:x proximity}
nav::-webkit-scrollbar{display:none}
nav button{background:transparent;border:1px solid transparent;color:var(--muted);
padding:.55rem 1rem;border-radius:999px;cursor:pointer;font-size:.88rem;font-family:inherit;
flex:0 0 auto;white-space:nowrap;scroll-snap-align:center;min-height:44px}
@media(min-width:720px){nav{justify-content:center;flex-wrap:wrap;overflow-x:visible}}
nav button:hover{color:var(--text);background:#1a2540}
nav button[aria-selected=true]{background:#1e2a47;border-color:var(--line);color:var(--text);font-weight:600}
.panel[hidden]{display:none}
.tab-head{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap;margin-bottom:.5rem}
h2{font-size:1.35rem}h3{font-size:1.02rem}h4{font-size:.95rem;margin:1.5rem 0 .5rem;color:var(--muted)}
.lead{color:var(--muted);margin-bottom:1.25rem;max-width:75ch}
code{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-size:.85em;
background:#1a2540;padding:.12em .4em;border-radius:4px;color:#bfd4ff;word-break:break-word}
a{color:#7dd3fc}
.pill{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;
padding:.2rem .6rem;border-radius:999px;white-space:nowrap}
.pill.ok{background:#052e16;color:var(--ok)}
.pill.warn{background:#422006;color:var(--warn)}
.pill.idle{background:#1e293b;color:var(--muted)}
.cards{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));margin-bottom:1.75rem}
.card{text-align:left;font-family:inherit;background:var(--panel);border:1px solid var(--line);
border-top:3px solid var(--accent);border-radius:12px;padding:1.1rem;cursor:pointer;color:var(--text)}
.card:hover{background:#182444;transform:translateY(-2px);transition:.15s}
.card-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem}
.card-gen{font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);font-weight:700}
.card h3{margin-bottom:.4rem}
.card p{font-size:.85rem;color:var(--muted)}
.card-cta{display:inline-block;margin-top:.7rem;font-size:.8rem;color:var(--accent)}
.callout{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--diy);
border-radius:10px;padding:1rem 1.15rem;margin-bottom:1rem}
.callout h4{margin:0 0 .35rem;color:var(--text)}
.callout p{font-size:.88rem;color:var(--muted)}
.facts{display:grid;grid-template-columns:auto 1fr;gap:.35rem 1rem;font-size:.88rem;margin:1rem 0}
.facts dt{color:var(--dim)}
.tablewrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:.5rem 0 1rem;
border-radius:8px}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th,td{border:1px solid var(--line);padding:.45rem .6rem;text-align:left;vertical-align:top}
th{background:#1a2540;color:var(--muted);font-weight:600}
caption{text-align:left;color:var(--dim);font-size:.8rem;padding-bottom:.35rem}
/* SHA-1s and shell commands cannot wrap at word boundaries; let them break so a
   narrow screen scrolls the table box instead of the whole page. */
.hashes td code{word-break:break-all}
.launch code{white-space:nowrap}
.muted{color:var(--dim)}
.steps{margin:.5rem 0 1rem 1.2rem;font-size:.88rem;color:var(--muted)}
.steps li{margin:.3rem 0}
.rom{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:1rem;margin:1.25rem 0}
.rom h4{margin:0 0 .4rem;color:var(--text)}
.rom p{font-size:.86rem;color:var(--muted)}
.hashes code{font-size:.76em}
.links{display:flex;flex-wrap:wrap;gap:.5rem}
.link{background:#1a2540;border:1px solid var(--line);padding:.4rem .8rem;border-radius:8px;
font-size:.83rem;text-decoration:none;color:#bfd4ff}
.link:hover{background:#22325a}
.legend{display:flex;gap:1rem;flex-wrap:wrap;font-size:.78rem;margin-bottom:1.25rem}
.key{padding:.2rem .7rem;border-radius:999px}
.key.official{background:#422006;color:var(--official)}
.key.diy{background:#2e1065;color:var(--diy)}
.line-card{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:12px;padding:1.1rem;margin-bottom:1.1rem}
.line-title{color:var(--accent);margin-bottom:.5rem}
.branch-label{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin:.9rem 0 .4rem}
.branch-label.official{color:var(--official)}
.branch-label.diy{color:var(--diy)}
.chain{display:flex;align-items:stretch;flex-wrap:wrap;gap:.4rem}
/* Stages grow to share the row and wrap onto the next one. Fixed-width cards
   pushed a 6-stage line past the card edge on a phone. */
.stage{background:var(--panel2);border:1px solid var(--line);border-radius:9px;
padding:.55rem .7rem;flex:1 1 130px;max-width:100%}
.stage-name{font-size:.83rem;font-weight:600}
.stage-sub{font-size:.7rem;color:var(--dim)}
.types{display:flex;gap:.25rem;flex-wrap:wrap;margin-top:.3rem}
.type{font-size:.62rem;padding:.08rem .4rem;border-radius:999px;background:color-mix(in srgb,var(--t) 18%,transparent);
color:var(--t);border:1px solid color-mix(in srgb,var(--t) 35%,transparent)}
.ability{font-size:.66rem;color:var(--dim);margin-top:.25rem}
.arrow{align-self:center;color:#4a5a7a;font-size:1.1rem;padding:0 .1rem}
.note{font-size:.8rem;color:var(--dim);margin-top:.6rem;font-style:italic}
.road{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:1rem 1.15rem;margin-bottom:.9rem}
/* Wraps because the pill is nowrap: a long title plus "In progress" could not
   share one line at 320px and pushed the page 2px wide. */
.road-head{display:flex;justify-content:space-between;align-items:center;gap:.5rem .75rem;
margin-bottom:.4rem;flex-wrap:wrap}
.card-head{flex-wrap:wrap}
.road p{font-size:.88rem;color:var(--muted)}
.ref{margin-top:.5rem}
footer{text-align:center;padding:2rem 1rem;color:var(--dim);font-size:.78rem;border-top:1px solid #243049;margin-top:2rem}

/* ---- phones ---- */
@media(max-width:560px){
  .facts{grid-template-columns:1fr;gap:.15rem}
  .facts dt{margin-top:.5rem}
  header{padding:1.6rem .9rem 1rem}
  header p{font-size:.92rem}
  .wrap{padding:0 .9rem 3rem}
  h2{font-size:1.2rem}
  .lead{font-size:.93rem}
  /* One card per row; 270px minimums caused a sideways scroll at 360px. */
  .cards{grid-template-columns:1fr;gap:.75rem}
  .callout,.road,.line-card,.rom{padding:.85rem .9rem}
  .legend{gap:.4rem}
  .legend .key{font-size:.72rem}
  /* Tap targets: links and pills were under the 44px touch minimum. */
  .link{padding:.6rem .9rem;min-height:44px;display:inline-flex;align-items:center}
  .card{padding:1rem}
  .arrow{display:none}
  .stage{flex:1 1 calc(50% - .4rem)}
  .steps{margin-left:1.1rem}
  footer{padding:1.5rem .9rem}
}
@media(max-width:360px){
  .stage{flex:1 1 100%}
}
"""

JS = """
(function(){
  var tabs = Array.prototype.slice.call(document.querySelectorAll('nav button'));
  var panels = Array.prototype.slice.call(document.querySelectorAll('.panel'));

  function show(id, push){
    tabs.forEach(function(t){ t.setAttribute('aria-selected', String(t.dataset.tab === id)); });
    panels.forEach(function(p){ p.hidden = (p.id !== 'panel-' + id); });
    if (push && location.hash !== '#' + id) history.replaceState(null, '', '#' + id);
    window.scrollTo(0, 0);
  }

  tabs.forEach(function(t){
    t.addEventListener('click', function(){ show(t.dataset.tab, true); });
  });

  // Home cards jump to their tab.
  document.querySelectorAll('[data-goto]').forEach(function(c){
    c.addEventListener('click', function(){ show(c.dataset.goto, true); });
  });

  var initial = location.hash.replace('#', '');
  show(tabs.some(function(t){ return t.dataset.tab === initial; }) ? initial : tabs[0].dataset.tab, false);
})();
"""


def build() -> Path:
    registry = read_json(HUB / "engines.json")
    species = read_json(ROOT / "hack" / "species.json")
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    commit = pinned_commit(ROOT / "engines" / "VENDOR.md")

    apps = registry["apps"]
    playable = [a for a in apps if a["id"] != "next"]
    intro = next((a for a in apps if a["id"] == "next"), None)

    tabs = [("home", "Home")]
    tabs += [(a["id"], a["tab"]) for a in playable]
    tabs += [("species", "Species"), ("roadmap", "Roadmap")]

    nav = "".join(
        f'<button role="tab" data-tab="{e(tid)}" aria-selected="false">{e(label)}</button>'
        for tid, label in tabs
    )

    panels = [f'<div class="panel" id="panel-home" role="tabpanel">{home_tab(apps, version, commit)}</div>']
    for a in playable:
        panels.append(f'<div class="panel" id="panel-{e(a["id"])}" role="tabpanel" hidden>{app_tab(a)}</div>')
    panels.append(f'<div class="panel" id="panel-species" role="tabpanel" hidden>'
                  f'<div class="tab-head"><h2>Evolved species</h2></div>{species_tab(species)}</div>')
    panels.append(f'<div class="panel" id="panel-roadmap" role="tabpanel" hidden>'
                  f'{roadmap_tab(intro, registry.get("roadmap", []))}</div>')

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Pokémon Evolved Hub</title>
<!-- GENERATED FILE - do not edit by hand.
     Regenerate with: python3 apps/hub/build_hub.py
     Sources: apps/hub/engines.json, hack/species.json, VERSION, engines/VENDOR.md -->
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>Pokémon Evolved Hub</h1>
  <p>Gen 1 engine, the Emerald ROM hack, and the Evolved species data — in one
  place, each on its own tab.</p>
</header>

<nav role="tablist">{nav}</nav>

<div class="wrap">
{chr(10).join(panels)}
</div>

<footer>
  <p>Pokémon Evolved Hub · v{e(version)} · generated from
  <code>apps/hub/engines.json</code> + <code>hack/species.json</code></p>
  <p>gen1recomp by <a href="https://github.com/bryanthaboi/gen1recomp">bryanthaboi</a> (MIT) ·
  decompilation base <a href="https://github.com/pret/pokeemerald">pret/pokeemerald</a> ·
  Pokémon Evolved by AtSign8877 &amp; team</p>
  <p>No ROMs are distributed. Pokémon is a trademark of Nintendo / Creatures Inc. / GAME FREAK Inc.
  This is an unaffiliated fan project.</p>
</footer>

<script>{JS}</script>
</body>
</html>
"""
    out = HUB / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    path = build()
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")
