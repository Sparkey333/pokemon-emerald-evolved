# ◆ Indigo Dexforge

Pokémon Evolved ROM-hack **sheet forge**: pulls real reference assets, generates a
**character full sheet** + **3D sprite action sheet** for every species, and lets you
**forge brand-new species from a prompt** — art, sheets and dex entry in one step.

Covers the original Kanto 151, all **203 new species** from the *Pokémon Evolved* hack,
the 6 DarkHearts **DIY originals**, and everything you forge.

## Run it

```bash
node tools/forge-server.mjs 8642      # then open http://localhost:8642
```

The dashboard is the front door (`dashboard.html`). Without the server it still opens
read-only; with it, the mapper and forge can write.

| Tab | What it does |
|-----|--------------|
| **Overview** | Coverage per section, what each source gives you, recently forged |
| **Species** | All 360+ species, searchable/filterable → character & action sheets |
| **Montage Mapper** | Assign one of the 136 real hack creature designs to a species |
| **Forge** | Prompt → new species (art + sheets + dex), with a 20-concept preset library |
| **Vault & Rules** | Guardrails, credits, artist reveal gallery |

`index.html` is the older, simpler browser — kept because it embeds the two original
research artifacts.

## Layout
```
data/     PokeAPI CSVs · hack stats/evolution CSVs · species.js (built)
          montage-map.json (your cell→species assignments)
          custom-species.json (forged species) · forge-presets.js
vault/    kanto-151/     front|back|shiny|back-shiny (FRLG 64px)
          evolved/montage/     136 creature designs sliced from calicorn's sheet
          evolved/reveal-art/  54 artist images + attribution manifest
          diy/ · forge/        your originals (front/back/shiny + masters)
tools/    pull-kanto-151.sh · pull_evolved_art.py · slice_montage.py
          build_species.py · gen_sheets.py · spritegen.py · forge_species.py
          gen_diy_byok.py · export_to_decomp.py · forge-server.mjs
sheets/   <section>/<id>/character.png + action.png
research/ the two original research artifacts (official-vs-DIY is canonical)
```

## Rebuild
```bash
python3 tools/build_species.py                 # CSVs + maps -> data/species.js
python3 tools/gen_sheets.py                    # all sheets
python3 tools/gen_sheets.py --slug ecosaur     # just one (merges into manifest)
```

## The two projects
**Indigo Dexforge** is the forge — research, assets, sheets, new species.
**`~/Projects/pokemon-emerald-evolved`** is the build target — a pret/pokeemerald
decomp whose `hack/species.json` holds the same DIY branch.

`tools/export_to_decomp.py` copies **only species we own** (`vault/diy`, `vault/forge`)
into the decomp's `graphics/pokemon/<slug>/` with `.pal` files, and reports drift
between the two species tables. Run `--dry-run` first. It never exports Kanto or
Evolved art.

## Why the montage mapping is manual
The hack's in-game sprites live only inside its `evolutions.ips` — no public PNG set
exists (the GitHub repo is README + patch; pkmnevolved.com hosts none). calicorn's
public montage recovers 136 designs, but its per-cell dex numbers are ~3px tall and
destroyed by Tumblr's downscale (`s640x960` is the largest stored size; bigger 404s).
No automatic mapping would be honest, so the dashboard gives you a two-click assign
instead. For the full set, use the own-dump path: patch **your own** LeafGreen dump,
extract with GBA tools, drop PNGs into `vault/evolved/{front,back,shiny}/<slug>.png`.

## Sources & credit
- **Kanto 151** — FRLG sprites + species CSVs via PokeAPI. © Nintendo / Game Freak / Creatures.
- **Pokémon Evolved** — hack by **AtSign8877**, commissioned by **PointCrow**. Sprite art by
  **calicorn** (lead), **kattenkg**, **jordanosart**, **xiapher** & team. Species data from
  **JuicyBlucy** (Stats/Pokédex sheet) and **PotatoLeon** (Master Doc).
- **DIY + forged originals** — DarkHearts, BYOK-generated; masters synced to
  `~/GameAssets/library/sprites/`.

## Guardrails — standing doctrine, do not relax
- `vault/kanto-151`, `vault/evolved/montage` and `vault/evolved/reveal-art` are a
  **local personal reference vault only** — never bundle, re-host, sell, or ship them.
- **No ROMs, no patches, no links to either** live in this repo.
- Only `vault/diy` and `vault/forge` are original and shippable.
- Forge naming rule (enforced by the server): no colour / jewel / gemstone / mineral names.

## Open design forks (DIY branch)
- Naming: **Infernodrake** (canonical) vs *Inferdrake* (earlier showcase).
- Branch mechanic: stone-branch alts (canonical) vs straight level-ups (earlier showcase).
