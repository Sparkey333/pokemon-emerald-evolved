#!/usr/bin/env python3
"""Indigo Dexforge sheet generator.

For every species in data/species.json, composes two PNGs into sheets/<section>/<id>/:
  character.png — full character sheet: hero sprite, views, palette, stats, evolution line
  action.png    — "3D sprite" action sheet: Y-rotation row + idle/attack/hit/faint/shiny strips

$0 / fully offline: everything is composed from vault sprites with PIL transforms
(side views are squash-and-shade approximations, GBA-battle-style animation frames).
Species with no vault sprite yet get a silhouette placeholder sheet so the pipeline
is complete end-to-end; re-run after new art lands in vault/ to upgrade them.

Usage: gen_sheets.py [--only kanto|evolved|diy] [--limit N]
"""
import json, os, sys
from collections import Counter
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BG, PANEL, PANEL2 = "#0a0e1a", "#121a2e", "#0d1324"
LINE, TEXT, MUTED, DIM = "#2a3858", "#e8edf8", "#8b9bc0", "#5c6b8a"
SECTION_ACCENT = {"kanto": "#fbbf24", "evolved": "#38bdf8", "diy": "#a78bfa", "forge": "#34d399"}
SECTION_TAG = {"kanto": "KANTO ORIGINAL", "evolved": "POKEMON EVOLVED",
               "diy": "DIY ORIGINAL — DARKHEARTS", "forge": "FORGED ORIGINAL"}
SHIPPABLE = ("diy", "forge")
TYPE_COLORS = {
    "normal": "#9ca3af", "fire": "#f97316", "water": "#0ea5e9", "electric": "#eab308",
    "grass": "#22c55e", "ice": "#67e8f9", "fighting": "#dc2626", "poison": "#a855f7",
    "ground": "#d97706", "flying": "#818cf8", "psychic": "#ec4899", "bug": "#84cc16",
    "rock": "#b45309", "ghost": "#7c3aed", "dragon": "#6366f1", "dark": "#525252",
    "steel": "#94a3b8", "fairy": "#f472b6",
}
STAT_ORDER = [("hp", "HP"), ("attack", "ATK"), ("defense", "DEF"),
              ("special-attack", "SPA"), ("special-defense", "SPD"), ("speed", "SPE")]

def font(size, bold=False):
    for path, idx in ((f"/System/Library/Fonts/Menlo.ttc", 1 if bold else 0),
                      ("/System/Library/Fonts/Supplemental/Arial%s.ttf" % (" Bold" if bold else ""), 0)):
        try:
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    return ImageFont.load_default()

F_BIG, F_MED, F_LAB, F_SM = font(30, True), font(15, True), font(12, True), font(11)

# ── sprite helpers (all operate on 64x64-ish RGBA) ──────────────────────────
def load_sprite(rel):
    if not rel:
        return None
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGBA")
    if im.size != (64, 64):
        canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        im.thumbnail((64, 64), Image.NEAREST)
        canvas.paste(im, ((64 - im.width) // 2, 64 - im.height))
        im = canvas
    return im

def placeholder_sprite(accent="#8b9bc0"):
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i in range(4, 60, 8):
        d.line([(i, 4), (i + 4, 4)], fill=accent, width=1)
        d.line([(i, 59), (i + 4, 59)], fill=accent, width=1)
        d.line([(4, i), (4, i + 4)], fill=accent, width=1)
        d.line([(59, i), (59, i + 4)], fill=accent, width=1)
    d.text((32, 30), "?", font=font(28, True), fill=accent, anchor="mm")
    return im

def squash(im, wr):
    w = max(1, int(64 * wr))
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    out.paste(im.resize((w, 64), Image.NEAREST), ((64 - w) // 2, 0))
    return out

def vsquash(im, hr):
    h = max(1, int(64 * hr))
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    out.paste(im.resize((64, h), Image.NEAREST), (0, 64 - h))
    return out

def shade(im, f):
    r, g, b, a = im.split()
    rgb = Image.merge("RGB", (r, g, b)).point(lambda v: int(v * f))
    return Image.merge("RGBA", (*rgb.split(), a))

def tint(im, color, strength):
    solid = Image.new("RGBA", im.size, color)
    rgb = Image.blend(im.convert("RGB"), solid.convert("RGB"), strength)
    return Image.merge("RGBA", (*rgb.split(), im.split()[3]))

def ghost(im, af):
    r, g, b, a = im.split()
    return Image.merge("RGBA", (r, g, b, a.point(lambda v: int(v * af))))

def shift(im, dx, dy):
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    out.paste(im, (dx, dy), im)
    return out

def side_views(front, back):
    right = shade(squash(front, 0.45), 0.85)
    left = shade(ImageOps.mirror(squash(back if back else front, 0.45)), 0.8)
    return right, left

# ── canvas helpers ──────────────────────────────────────────────────────────
def new_canvas(w, h):
    im = Image.new("RGB", (w, h), BG)
    return im, ImageDraw.Draw(im)

def cell(canvas, d, x, y, size, sprite, label=None, accent=LINE):
    d.rounded_rectangle([x, y, x + size, y + size], 8, fill=PANEL2, outline=accent, width=1)
    if sprite:
        s = sprite.resize((size - 24, size - 24), Image.NEAREST)
        canvas.paste(s, (x + 12, y + 12), s)
    if label:
        d.text((x + size // 2, y + size + 10), label, font=F_SM, fill=DIM, anchor="ma")

def chip(d, x, y, text, color):
    w = int(d.textlength(text, font=F_LAB)) + 20
    d.rounded_rectangle([x, y, x + w, y + 24], 12, fill=PANEL2, outline=color, width=1)
    d.text((x + w // 2, y + 12), text, font=F_LAB, fill=color, anchor="mm")
    return w

def wrap(d, text, font, max_w):
    """Greedy word-wrap to a pixel width."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and d.textlength(trial, font=font) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def palette_of(front, n=6):
    if not front:
        return []
    px = [p[:3] for p in front.getdata() if p[3] > 128]
    px = [(r // 16 * 16, g // 16 * 16, b // 16 * 16) for r, g, b in px]
    return [c for c, _ in Counter(px).most_common(n + 2)
            if not (c[0] < 24 and c[1] < 24 and c[2] < 24)][:n]

# ── data / chain resolution ─────────────────────────────────────────────────
with open(os.path.join(ROOT, "data", "species.json"), encoding="utf-8") as f:
    DEX = json.load(f)
ALL = DEX["kanto"] + DEX["evolved"] + DEX["diy"] + DEX.get("forge", [])
BY_NAME = {e["name"]: e for e in ALL}
BY_DEX = {e["dex"]: e for e in DEX["kanto"]}

def parent_of(e):
    if e.get("evolvesFrom"):
        return BY_DEX.get(e["evolvesFrom"])
    if e.get("evolvesFromName"):
        return BY_NAME.get(e["evolvesFromName"])
    return None

CHILDREN = {}
for e in ALL:
    p = parent_of(e)
    if p:
        m = e.get("method") or next((c["method"] for c in p.get("evolvesInto", [])
                                     if BY_DEX.get(c["dex"]) is e), "?")
        CHILDREN.setdefault(p["name"], []).append((e, m))

def chain_of(e):
    """Full main-line path through this species (ascend to root, descend via
    same-section-preferred children), capped at 7. Returns (path, method_fn, branches)."""
    path, seen, cur = [e], {e["name"]}, e
    while True:
        p = parent_of(cur)
        if not p or p["name"] in seen:
            break
        path.insert(0, p)
        seen.add(p["name"])
        cur = p
    cur = e
    while len(path) < 7:
        kids = [k for k in CHILDREN.get(cur["name"], []) if k[0]["name"] not in seen]
        if not kids:
            break
        kids.sort(key=lambda cm: 0 if cm[0]["section"] == e["section"] else 1)
        child = kids[0][0]
        path.append(child)
        seen.add(child["name"])
        cur = child

    def method_between(a, b):
        return next((m for c, m in CHILDREN.get(a["name"], []) if c is b), "?")

    branches = {n["name"]: max(0, len(CHILDREN.get(n["name"], [])) - 1) for n in path}
    return path, method_between, branches

def front_of(e):
    return load_sprite(e.get("sprites", {}).get("front"))

# ── character sheet ─────────────────────────────────────────────────────────
def character_sheet(e, out):
    accent = SECTION_ACCENT[e["section"]]
    W = 780
    path, method_between, branches = chain_of(e)
    H = 700 + (146 if len(path) > 1 else 0)
    im, d = new_canvas(W, H)
    front = front_of(e)
    ph = front is None
    if ph:
        front = placeholder_sprite(accent)

    # header
    d.rounded_rectangle([16, 16, W - 16, 104], 12, fill=PANEL, outline=LINE, width=1)
    dexno = "#%03d " % e["dex"] if e.get("dex") else ""
    d.text((36, 40), dexno + e["name"].upper(), font=F_BIG, fill=TEXT, anchor="lm")
    x = 36
    for t in e.get("types", []):
        x += chip(d, x, 60, t.upper(), TYPE_COLORS.get(t, MUTED)) + 8
    tw = int(d.textlength(SECTION_TAG[e["section"]], font=F_LAB)) + 20
    chip(d, W - 36 - tw, 60, SECTION_TAG[e["section"]], accent)
    d.text((W - 36, 40), "CHARACTER SHEET", font=F_MED, fill=DIM, anchor="rm")

    # hero
    d.rounded_rectangle([16, 120, 336, 440], 12, fill=PANEL, outline=accent, width=2)
    hero = front.resize((256, 256), Image.NEAREST)
    im.paste(hero, (48, 152), hero)
    d.text((176, 420), "FRONT — GBA battle scale x4" + (" (placeholder)" if ph else ""),
           font=F_SM, fill=DIM, anchor="mm")

    # views strip
    d.rounded_rectangle([352, 120, W - 16, 296], 12, fill=PANEL, outline=LINE, width=1)
    d.text((372, 140), "VIEWS", font=F_MED, fill=MUTED)
    views = [("back", "BACK"), ("shiny", "SHINY"), ("back-shiny", "SHINY BACK")]
    vx = 372
    for key, lab in views:
        s = load_sprite(e.get("sprites", {}).get(key))
        cell(im, d, vx, 160, 96, s if s else placeholder_sprite(DIM), lab)
        vx += 118

    # palette
    d.rounded_rectangle([352, 312, W - 16, 440], 12, fill=PANEL, outline=LINE, width=1)
    d.text((372, 330), "PALETTE", font=F_MED, fill=MUTED)
    for i, c in enumerate(palette_of(front)):
        sx = 372 + i * 64
        d.rounded_rectangle([sx, 356, sx + 52, 396], 6, fill=c, outline=LINE)
        d.text((sx + 26, 406), "#%02x%02x%02x" % c, font=F_SM, fill=DIM, anchor="ma")

    # stats / theme
    d.rounded_rectangle([16, 456, W - 16, 616], 12, fill=PANEL, outline=LINE, width=1)
    d.text((36, 476), "BASE STATS", font=F_MED, fill=MUTED)
    stats = e.get("stats") or {}
    if stats:
        for i, (key, lab) in enumerate(STAT_ORDER):
            sy = 506 + i * 18
            v = stats.get(key, 0)
            d.text((36, sy), lab, font=F_SM, fill=MUTED)
            d.text((84, sy), str(v), font=F_SM, fill=TEXT)
            d.rectangle([120, sy + 2, 120 + 600, sy + 10], fill=PANEL2)
            d.rectangle([120, sy + 2, 120 + int(600 * min(v, 160) / 160), sy + 10],
                        fill=TYPE_COLORS.get((e.get("types") or ["normal"])[0], accent))
    else:
        d.text((36, 516), "Stats: TBD — balance pass pending for %s branch." % SECTION_TAG[e["section"]].title(),
               font=F_MED, fill=DIM)
        y = 546
        if e.get("theme"):
            for i, ln in enumerate(wrap(d, "Design theme: " + e["theme"], F_MED, W - 90)[:2]):
                d.text((36, y), ln, font=F_MED, fill=TEXT)
                y += 22
        if e.get("altNames"):
            d.text((36, y + 6), "Open naming fork: also considered " + " / ".join(e["altNames"]),
                   font=F_SM, fill="#fbbf24")

    # evolution line
    y0 = 632
    if len(path) > 1:
        d.rounded_rectangle([16, y0, W - 16, y0 + 130], 12, fill=PANEL, outline=LINE, width=1)
        d.text((36, y0 + 16), "EVOLUTION LINE", font=F_MED, fill=MUTED)
        ex = 36
        for i, se in enumerate(path):
            s = front_of(se) or placeholder_sprite(DIM)
            cell(im, d, ex, y0 + 34, 64, s, se["name"][:10], accent if se is e else LINE)
            ex += 76
            if i < len(path) - 1:
                m = str(method_between(se, path[i + 1]))
                d.text((ex + 13, y0 + 58), "→", font=F_MED, fill=DIM, anchor="mm")
                d.text((ex + 13, y0 + 76), m[:8], font=F_SM, fill=DIM, anchor="mm")
                if branches.get(se["name"]):
                    d.text((ex + 13, y0 + 90), "+%d alt" % branches[se["name"]],
                           font=F_SM, fill="#fbbf24", anchor="mm")
                ex += 30
        y0 += 146

    credit = e.get("credit", "")
    d.text((36, H - 52), credit[:88] + ("…" if len(credit) > 88 else ""), font=F_SM, fill=DIM)
    ship = e["section"] in SHIPPABLE
    note = "ORIGINAL SPECIES — shippable" if ship else "LOCAL REFERENCE VAULT ONLY — do not ship"
    d.text((36, H - 30), note, font=F_SM, fill="#4ade80" if ship else "#f87171")
    im.save(out)

# ── action sheet ────────────────────────────────────────────────────────────
def action_frames(front, back, shiny, back_shiny):
    right, left = side_views(front, back)
    rows = [
        ("ROTATE Y", [front, right, back or shade(ImageOps.mirror(front), 0.7), left],
         ["FRONT", "RIGHT", "BACK", "LEFT"]),
        ("IDLE", [front, shift(vsquash(front, 0.97), 0, 0), front, shift(front, 0, -1)], None),
        ("ATTACK", [shift(front, -3, 0), shift(front, 6, -1),
                    shift(tint(front, "#ffffff", 0.55), 12, -2), shift(front, 4, 0)], None),
        ("HIT", [tint(front, "#ef4444", 0.4), shift(ghost(front, 0.45), -7, 0),
                 shift(tint(front, "#ef4444", 0.2), -3, 0), front], None),
        ("FAINT", [front, ghost(vsquash(front, 0.7), 0.85),
                   ghost(vsquash(front, 0.45), 0.55), ghost(vsquash(front, 0.22), 0.25)], None),
    ]
    if shiny:
        s_right, s_left = side_views(shiny, back_shiny)
        rows.append(("SHINY", [shiny, s_right,
                               back_shiny or shade(ImageOps.mirror(shiny), 0.7), s_left],
                     ["FRONT", "RIGHT", "BACK", "LEFT"]))
    return rows

def action_sheet(e, out):
    accent = SECTION_ACCENT[e["section"]]
    front = front_of(e)
    ph = front is None
    if ph:
        front = placeholder_sprite(accent)
    back = load_sprite(e.get("sprites", {}).get("back"))
    shiny = load_sprite(e.get("sprites", {}).get("shiny"))
    back_shiny = load_sprite(e.get("sprites", {}).get("back-shiny"))
    rows = action_frames(front, back, shiny, back_shiny)

    CS, GAP, GUT = 140, 12, 128
    W = GUT + 4 * (CS + GAP) + 28
    H = 96 + len(rows) * (CS + GAP + 22) + 48
    im, d = new_canvas(W, H)
    d.rounded_rectangle([16, 14, W - 16, 80], 12, fill=PANEL, outline=LINE, width=1)
    dexno = "#%03d " % e["dex"] if e.get("dex") else ""
    d.text((32, 34), dexno + e["name"].upper(), font=font(24, True), fill=TEXT, anchor="lm")
    d.text((32, 60), "3D SPRITE ACTION SHEET — 4-frame strips, GBA 64px @2x, nearest",
           font=F_SM, fill=DIM, anchor="lm")
    tw = int(d.textlength(SECTION_TAG[e["section"]], font=F_LAB)) + 20
    chip(d, W - 32 - tw, 28, SECTION_TAG[e["section"]], accent)

    y = 96
    for label, frames, sub in rows:
        d.text((24, y + CS // 2), label, font=F_MED, fill=accent if label == "ROTATE Y" else MUTED,
               anchor="lm")
        for i, fr in enumerate(frames):
            x = GUT + i * (CS + GAP)
            cell(im, d, x, y, CS, fr, (sub[i] if sub else "F%d" % (i + 1)))
        y += CS + GAP + 22

    note = "sides are squash-shade approximations — regenerate with BYOK art for true 3/4 views"
    d.text((24, H - 30), ("placeholder — no vault sprite yet. " if ph else "") + note,
           font=F_SM, fill=DIM)
    im.save(out)

# ── main ────────────────────────────────────────────────────────────────────
def out_dir(e):
    key = "%03d-%s" % (e["dex"], e["slug"]) if e.get("dex") else e["slug"]
    p = os.path.join(ROOT, "sheets", e["section"], key)
    os.makedirs(p, exist_ok=True)
    return p, "sheets/%s/%s" % (e["section"], key)

def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    slug = sys.argv[sys.argv.index("--slug") + 1] if "--slug" in sys.argv else None
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None

    todo = [e for e in ALL if (not only or e["section"] == only)
            and (not slug or e["slug"] == slug)]
    if limit:
        todo = todo[:limit]

    # A filtered run must MERGE into the manifest, never replace it — otherwise
    # regenerating one species would drop every other species from the index.
    path = os.path.join(ROOT, "sheets", "manifest.json")
    manifest = []
    if (only or slug or limit) and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    by_name = {m["name"]: m for m in manifest}

    for e in todo:
        p, rel = out_dir(e)
        character_sheet(e, os.path.join(p, "character.png"))
        action_sheet(e, os.path.join(p, "action.png"))
        by_name[e["name"]] = {"name": e["name"], "section": e["section"],
                              "character": rel + "/character.png",
                              "action": rel + "/action.png"}

    order = {s: i for i, s in enumerate(("kanto", "evolved", "diy", "forge"))}
    merged = sorted(by_name.values(), key=lambda m: (order.get(m["section"], 9), m["name"]))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=1)
    print("generated %d species x 2 sheets (manifest now %d)" % (len(todo), len(merged)))

if __name__ == "__main__":
    main()
