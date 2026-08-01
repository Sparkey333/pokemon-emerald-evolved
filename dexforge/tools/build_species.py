#!/usr/bin/env python3
"""Build data/species.js (window.DEX) for Indigo Dexforge.

Merges three sources:
  1. Kanto 151  — PokeAPI CSVs in data/ (names, types, base stats, evolution methods)
  2. Evolved    — Pokemon Evolved ROM hack new species; seed list below, overridden by
                  data/evolved-species.json when the recon/pull drops a fuller list
  3. DIY        — Brandon's original alt-branch species from research/pokemon-evolved-official-vs-diy.html
"""
import csv, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def title(ident):
    return re.sub(r"(^|-)([a-z])", lambda m: (" " if m.group(1) else "") + m.group(2).upper(), ident)

# ── Kanto 151 from PokeAPI CSVs ─────────────────────────────────────────────
type_names = {r["id"]: r["identifier"] for r in rows("types.csv")}
stat_names = {r["id"]: r["identifier"] for r in rows("stats.csv")}
item_names = {r["id"]: title(r["identifier"]) for r in rows("items.csv")}
trigger_names = {r["id"]: r["identifier"] for r in rows("evolution_triggers.csv")}

species = {r["id"]: r for r in rows("pokemon_species.csv") if int(r["id"]) <= 151}
ptypes, pstats = {}, {}
for r in rows("pokemon_types.csv"):
    if int(r["pokemon_id"]) <= 151:
        ptypes.setdefault(r["pokemon_id"], []).append((int(r["slot"]), type_names[r["type_id"]]))
for r in rows("pokemon_stats.csv"):
    if int(r["pokemon_id"]) <= 151 and stat_names[r["stat_id"]] in (
        "hp", "attack", "defense", "special-attack", "special-defense", "speed"):
        pstats.setdefault(r["pokemon_id"], {})[stat_names[r["stat_id"]]] = int(r["base_stat"])

def evo_label(r):
    trig = trigger_names.get(r["evolution_trigger_id"], "")
    if trig == "level-up":
        if r["minimum_level"]: return "Lv " + r["minimum_level"]
        if r["minimum_happiness"]: return "Friendship"
        return "Level up"
    if trig == "use-item": return item_names.get(r["trigger_item_id"], "Stone")
    if trig == "trade": return "Trade"
    return title(trig) if trig else "?"

evo_into = {}   # species_id -> list of (child_id, label)
for r in rows("pokemon_evolution.csv"):
    child = r["evolved_species_id"]
    if child in species:
        parent = species[child]["evolves_from_species_id"]
        if parent:
            evo_into.setdefault(parent, [])
            lbl = evo_label(r)
            if not any(c == child for c, _ in evo_into[parent]):
                evo_into[parent].append((child, lbl))

kanto = []
for sid in sorted(species, key=int):
    s = species[sid]
    name = title(s["identifier"])
    kanto.append({
        "dex": int(sid),
        "slug": s["identifier"],
        "name": name,
        "types": [t for _, t in sorted(ptypes.get(sid, []))],
        "stats": pstats.get(sid, {}),
        "evolvesFrom": int(s["evolves_from_species_id"]) if s["evolves_from_species_id"] else None,
        "evolvesInto": [{"dex": int(c), "method": l} for c, l in evo_into.get(sid, [])],
        "section": "kanto",
        "sprites": {k: f"vault/kanto-151/{k}/{sid}.png" for k in ("front", "back", "shiny", "back-shiny")},
        "credit": "Game Freak / Nintendo — FRLG sprites via PokeAPI (local reference only)",
    })

# ── Pokemon Evolved new species (seed; recon JSON overrides) ────────────────
EVOLVED_SEED = [
    # slug, name, types, base line, evolves-from name, method, hackdex guess
    ("ecosaur",    "Ecosaur",    ["grass", "poison"], "Bulbasaur",  "Venusaur",   "Lv 41"),
    ("terarisaur", "Terarisaur", ["grass", "poison"], "Bulbasaur",  "Ecosaur",    "Lv 52"),
    ("symbisaur",  "Symbisaur",  ["grass", "poison"], "Bulbasaur",  "Terarisaur", "Lv 65"),
    ("chariguana", "Chariguana", ["fire", "flying"],  "Charmander", "Charizard",  "Lv 41"),
    ("chariana",   "Chariana",   ["fire", "water"],   "Charmander", "Chariguana", "Lv 52"),
    ("chariathan", "Chariathan", ["fire", "water"],   "Charmander", "Chariana",   "Lv 65"),
    ("ferrapin",   "Ferrapin",   ["water"],           "Squirtle",   "Blastoise",  "Lv 41"),
    ("fortoise",   "Fortoise",   ["water", "steel"],  "Squirtle",   "Ferrapin",   "Lv 52"),
    ("turtillery", "Turtillery", ["water", "steel"],  "Squirtle",   "Fortoise",   "Lv 65"),
    ("butteflare", "Butteflare", ["bug", "fire"],     "Caterpie",   "Butterfree", "Lv 36"),
    ("beebrute",   "Beebrute",   ["bug", "fighting"], "Weedle",     "Beedrill",   "Lv 36"),
    ("hydrados",   "Hydrados",   ["water", "dragon"], "Magikarp",   "Gyarados",   "Lv 44"),
]
def norm(n):
    n = n.replace("♀", " f").replace("♂", " m")
    return re.sub(r"[^a-z0-9]", "", n.lower())

KANTO_BY_NORM = {norm(k["name"]): k for k in kanto}

def load_evolved_from_csv():
    """Full new-species list from the community Stats/Pokedex sheet (JuicyBlucy):
    354 hack-dex rows ordered by family; a NEW species' parent is the previous row."""
    out, prev_display = [], None
    for r in rows("evolved-stats.csv"):
        raw = (r["NAME"] or "").strip()
        if not raw:
            continue
        cleaned = raw.replace("♀", " F").replace("♂", " M")
        display = title(re.sub(r"[^A-Za-z0-9' .-]", "", cleaned).strip().lower().replace(" ", "-"))
        k = KANTO_BY_NORM.get(norm(raw))
        if k:
            k["hackDex"] = int(r["#"])
            prev_display = k["name"]
            continue
        lvl = (r.get("lvl") or "").strip()
        types = [t.strip().lower() for t in (r.get("Type1", ""), r.get("Type2", ""))
                 if t.strip() and t.strip() != "-"]
        abilities = [a.strip().title() for a in (r.get("ability1", ""), r.get("ability2", ""))
                     if a.strip() and not set(a.strip()) <= {"-"}]
        out.append({
            "slug": re.sub(r"[^a-z0-9]", "", raw.lower()),
            "name": display,
            "hackDex": int(r["#"]),
            "types": types,
            "abilities": abilities,
            "stats": {"hp": int(r["HP"]), "attack": int(r["Atk"]), "defense": int(r["Def"]),
                      "special-attack": int(r["SpA"]), "special-defense": int(r["SpD"]),
                      "speed": int(r["Spe"])},
            "bst": int(r["BST"]),
            "evolvesFromName": prev_display,
            "method": ("Lv " + lvl) if lvl.isdigit() else "Stone/other",
        })
        prev_display = display
    return out

evolved = []
override = os.path.join(DATA, "evolved-species.json")
if os.path.exists(os.path.join(DATA, "evolved-stats.csv")):
    evolved = load_evolved_from_csv()
elif os.path.exists(override):
    with open(override, encoding="utf-8") as f:
        evolved = json.load(f)
else:
    for slug, name, types, line, frm, method in EVOLVED_SEED:
        evolved.append({"slug": slug, "name": name, "types": types, "line": line,
                        "evolvesFromName": frm, "method": method})
# Hand-made montage-cell -> species assignments from the dashboard mapper.
# (The montage's own dex labels are unreadable, so this is the only honest mapping.)
montage_map = {}
mm = os.path.join(DATA, "montage-map.json")
if os.path.exists(mm):
    with open(mm, encoding="utf-8") as f:
        montage_map = json.load(f)

for e in evolved:
    e.setdefault("slug", e["name"].lower())
    e["section"] = "evolved"
    e.setdefault("credit", "Pokemon Evolved ROM hack — art by calicorn, katten, jordanos, xiapher & team (AtSign8877); local reference only")
    sp = {}
    for k in ("front", "back", "shiny"):
        p = f"vault/evolved/{k}/{e['slug']}.png"
        if os.path.exists(os.path.join(ROOT, p)):
            sp[k] = p
    cell = montage_map.get(e["slug"])
    if cell:
        for key, suffix in (("front", "normal"), ("shiny", "shiny")):
            p = f"vault/evolved/montage/{cell}-{suffix}.png"
            if key not in sp and os.path.exists(os.path.join(ROOT, p)):
                sp[key] = p
        e["montageCell"] = cell
    e["sprites"] = sp

# ── DIY originals (canonical: research/pokemon-evolved-official-vs-diy.html) ─
DIY = [
    {"slug": "florasaur",    "name": "Florasaur",    "types": ["grass", "poison"], "line": "Bulbasaur",
     "evolvesFromName": "Venusaur",   "method": "Leaf Stone", "theme": "oversized floral bloom"},
    {"slug": "verdantaur",   "name": "Verdantaur",   "types": ["grass", "poison"], "line": "Bulbasaur",
     "evolvesFromName": "Florasaur",  "method": "Lv 52", "theme": "walking garden colossus"},
    {"slug": "charblaze",    "name": "Charblaze",    "types": ["fire"],            "line": "Charmander",
     "evolvesFromName": "Charizard",  "method": "Fire Stone", "theme": "blast-furnace wyvern"},
    {"slug": "infernodrake", "name": "Infernodrake", "types": ["fire", "dragon"],  "line": "Charmander",
     "evolvesFromName": "Charblaze",  "method": "Lv 52", "theme": "aerial fire dragon",
     "altNames": ["Inferdrake"]},
    {"slug": "torrentoise",  "name": "Torrentoise",  "types": ["water"],           "line": "Squirtle",
     "evolvesFromName": "Blastoise",  "method": "Water Stone", "theme": "tidal siege turtle"},
    {"slug": "tsunamoise",   "name": "Tsunamoise",   "types": ["water"],           "line": "Squirtle",
     "evolvesFromName": "Torrentoise", "method": "Lv 52", "theme": "living tsunami fortress"},
]
for d in DIY:
    d["section"] = "diy"
    d["credit"] = "DarkHearts original — pokemon-emerald-evolved DIY branch"
    sp = {}
    for k in ("front", "back", "shiny", "back-shiny", "rotation", "actions"):
        p = f"vault/diy/{d['slug']}/{k}.png"
        if os.path.exists(os.path.join(ROOT, p)):
            sp[k] = p
    d["sprites"] = sp

# ── Forge: species created from the dashboard's prompt box ──────────────────
forge = []
custom = os.path.join(DATA, "custom-species.json")
if os.path.exists(custom):
    with open(custom, encoding="utf-8") as f:
        forge = json.load(f)
for c in forge:
    c.setdefault("slug", re.sub(r"[^a-z0-9]", "", c["name"].lower()))
    c["section"] = "forge"
    c.setdefault("credit", "DarkHearts original — forged in Indigo Dexforge")
    sp = {}
    for k in ("front", "back", "shiny", "back-shiny"):
        p = f"vault/forge/{c['slug']}/{k}.png"
        if os.path.exists(os.path.join(ROOT, p)):
            sp[k] = p
    c["sprites"] = sp

dex = {"kanto": kanto, "evolved": evolved, "diy": DIY, "forge": forge,
       "built": "build_species.py",
       "counts": {"kanto": len(kanto), "evolved": len(evolved),
                  "diy": len(DIY), "forge": len(forge)}}

with open(os.path.join(DATA, "species.json"), "w", encoding="utf-8") as f:
    json.dump(dex, f, indent=1)
with open(os.path.join(DATA, "species.js"), "w", encoding="utf-8") as f:
    f.write("window.DEX = ")
    json.dump(dex, f)
    f.write(";\n")
print("species.js built:", dex["counts"])
