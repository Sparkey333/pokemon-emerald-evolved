# Pokémon Evolved

Two engines and one shared species dataset, in one repository:

| Track | What it is | State |
|-------|-----------|-------|
| **Gen 1 — Red / Blue / Yellow** | [gen1recomp](https://github.com/bryanthaboi/gen1recomp), a native LÖVE2D recreation, vendored at `engines/gen1recomp` | **Playable now** |
| **Gen 3 — Emerald: Evolved Starters** | The original work here: an Emerald ROM hack on [pret/pokeemerald](https://github.com/pret/pokeemerald) | Builds a `.gba` |
| **Evolved species data** | `hack/species.json` — official Pokémon Evolved lines plus our DIY branches | Shared by both |

## Start here

```bash
./Play.sh            # open the hub — a tabbed launcher for everything below
./Play.sh gen1       # play Gen 1 Red/Blue/Yellow (asks for your own ROM)
./Play.sh emerald    # open the Emerald evolution showcase
```

Windows: `Play.bat`, same subcommands. macOS: double-click `Play-Mac.command`.

The hub (`apps/hub/index.html`) is a self-contained page with a tab per track —
Home, Gen 1, Emerald, Species and Roadmap. It is generated from
`apps/hub/engines.json` and `hack/species.json`, so adding a future generation
is a data edit rather than a code change:

```bash
./Play.sh build-hub   # regenerate after editing either file
```

The hub is responsive down to 320px. To check it after a change:

```bash
python3 apps/hub/preview_hub.py                    # measure every viewport
python3 apps/hub/preview_hub.py --tab species --shots --outdir /tmp/shots
```

It renders the page at each device width and asserts the body never scrolls
sideways, naming any element that is too wide. Both the measurement and the
screenshots go through a width-pinned iframe on purpose: Chrome's
`--window-size` does not set the viewport in headless mode, so screenshotting
the page directly produces a wide layout cropped to phone width — which looks
exactly like a responsive bug that isn't there.

> **No ROMs are included, and none ever will be.** Gen 1 asks for your own
> legally obtained `.gb`/`.gbc` and verifies it by SHA-1 before importing; the
> Emerald build links against your own Emerald `.gba`.

---

## Emerald Realms — our own game

`apps/realms` is an original monster-collector that runs in any browser with
no ROM and no dependencies, including as a Claude artifact. It is the track
that can be published, because nothing in it belongs to anyone else:

- **36 original creatures** across five realms. The three starter lines grow
  from the DIY designs (Florasaur, Charblaze, Torrentoise and their evolutions)
  with new original base forms and no Kanto ancestry. The rest are designed
  from the genre's first-two-generation principles — type-triangle starters,
  the early bug, the route bird, the regional pest, one legend at the end —
  which are ideas, not property. The Codex tab lists each rule openly.
- **Five realms to walk between**, wild encounters in tall grass, turn-based
  battles with a 12-type chart, catching, levelling, evolution, and a guardian
  at the far shrine.
- **Saves**: three slots in the browser, each copyable to another slot or out
  as text and back in anywhere. (Artifacts can't start downloads, so copy-as-
  text is the transfer mechanism by design.)
- **Hack Lab**: duplicate the base game and rewrite any creature's stats,
  typing or evolution level, plus wild-level, catch-rate and XP multipliers.
  Hacks are shareable as text. A new journey starts on whichever hack is
  active — "original hacks" means mods of our own game.
- **Sprites are procedural**: each creature is drawn from a body plan on a
  32×32 grid with a three-tone palette, outline and shading, seeded from its
  name. A deliberate pixel style rather than hand-drawn art.

```bash
./Play.sh realms                 # open it
python3 apps/realms/build.py     # rebuild index.html after editing apps/realms/src/
```

The page is assembled from `apps/realms/src/` (`data.js` roster and maps,
`sprites.js`, `engine.js` rules, `ui.js`, `style.css`, `shell.html`) so each
part stays readable; `index.html` is generated and self-contained.

---

## Gen 3 — Emerald: Evolved Starters

Emerald ROM hack built on [pret/pokeemerald](https://github.com/pret/pokeemerald). Extends the three Kanto starter lines with **official Pokémon Evolved** expansion names/data **plus** our **DIY alternate branches**.

## Downloads (v0.1.0)

| Platform | File | Link |
|----------|------|------|
| **macOS** · Apple Silicon | `Pokemon-Emerald-Evolved_0.1.0_macOS_aarch64.dmg` | **[⬇ Download macOS DMG](https://github.com/Sparkey333/pokemon-emerald-evolved/releases/download/v0.1.0/Pokemon-Emerald-Evolved_0.1.0_macOS_aarch64.dmg)** |
| **Windows** · playable zip | `Pokemon-Emerald-Evolved_0.1.0_Windows.zip` | **[⬇ Download Windows ZIP](https://github.com/Sparkey333/pokemon-emerald-evolved/releases/download/v0.1.0/Pokemon-Emerald-Evolved_0.1.0_Windows.zip)** |
| **Source code** | `Pokemon-Emerald-Evolved_0.1.0_source.zip` | **[⬇ Download source ZIP](https://github.com/Sparkey333/pokemon-emerald-evolved/releases/download/v0.1.0/Pokemon-Emerald-Evolved_0.1.0_source.zip)** |

Full release: **https://github.com/Sparkey333/pokemon-emerald-evolved/releases/tag/v0.1.0**

**Windows:** unzip → `Play-Windows.bat` (opens the Official vs DIY showcase in your browser).  
**macOS:** open DMG → open `Official-vs-DIY-Showcase.html`. If blocked: System Settings → Privacy & Security → Open Anyway, or `xattr -dr com.apple.quarantine "/path/to/folder"`.

> Players who only want the evolution showcase need **only the DMG or Windows ZIP** — not the source tree. Building a `.gba` still needs pret tools + a legal Emerald ROM base (we do not distribute ROMs).

## Starter evolution paths

### Official (Pokémon Evolved — level-up path)

| Line | Chain | Levels |
|------|-------|--------|
| Grass | Bulbasaur → Ivysaur → Venusaur → **Ecosaur** → **Terarisaur** → **Symbisaur** | 16 / 32 / 41 / 52 / 65 |
| Fire | Charmander → Charmeleon → Charizard → **Chariguana** → **Chariana** → **Chariathan** | 16 / 36 / 41 / 52 / 65 |
| Water | Squirtle → Wartortle → Blastoise → **Ferrapin** → **Fortoise** → **Turtillery** | 16 / 36 / 41 / 52 / 65 |

Source: Pokémon Evolved v1.0 community guide (Scribd), [PokeHarbor screenshots](https://www.pokeharbor.com/2025/04/pokemon-evolved/), [GBAtemp thread](https://gbatemp.net/threads/pokemon-evolved-rom-hack-shows-a-fresh-take-on-kantos-original-151-species.669494/).

### DIY alternate branches (stone divergence)

| Line | Chain | Trigger |
|------|-------|---------|
| Grass | Venusaur → **Florasaur** → **Verdantaur** | Leaf Stone @ Venusaur, then Lv 52 |
| Fire | Charizard → **Charblaze** → **Infernodrake** | Fire Stone @ Charizard, then Lv 52 |
| Water | Blastoise → **Torrentoise** → **Tsunamoise** | Water Stone @ Blastoise, then Lv 52 |

DIY forms differ from official: no Fire/Water Chariana typing, no Water/Steel Fortoise line, grass branch emphasizes bloom over symbiosis.

## Quick start (build ROM)

```bash
# 1. Apply starter species + evolution patches (if not already applied)
python3 tools/bootstrap_evolved_starters.py

# 2. (Optional) Generate DIY canvas sprites
cd tools && npm init -y && npm install canvas && node generate_sprites.mjs

# 3. Build ROM (requires devkitARM + libpng for gbagfx)
# macOS Homebrew:
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig"
export CPPFLAGS="-I/opt/homebrew/include"
make tools -j$(sysctl -n hw.ncpu)
make -j$(sysctl -n hw.ncpu)
```

Output: `pokeemerald.gba`

---

## Gen 1 — Red / Blue / Yellow

`engines/gen1recomp` is a native LÖVE2D recreation: hand-written Lua, no
emulation and no ROM patching. Game data and graphics are decoded from a ROM you
supply, then cached — later launches never ask for it again.

```bash
./Play.sh gen1                          # first run imports a ROM, then plays
./Play.sh gen1 --rom /path/to/red.gb    # point the importer at a specific file
```

Only the canonical 1 MiB US ROMs are accepted, verified by SHA-1 at import time.
Red, Blue and Yellow can all be imported and played side by side.

It is vendored here for two reasons: so the original games are playable straight
from this repo, and as a working reference for eventually giving Emerald the
same treatment — a native engine reading a user-supplied ROM instead of patching
one. See the Roadmap tab in the hub.

---

## Project layout

```
apps/hub/                  # NEW — tabbed launcher app
  engines.json             #   registry: one entry per track, add future gens here
  build_hub.py             #   generator (inlines data so file:// works)
  preview_hub.py           #   responsive check + device screenshots
  index.html               #   generated page — do not edit by hand
engines/gen1recomp/        # vendored gen1recomp (MIT, upstream layout intact)
engines/VENDOR.md          # pinned commit, local changes, what was excluded
engines/restore-gen1recomp-blobs.sh
hack/species.json          # Official + DIY species metadata
hack/showcase/             # Interactive HTML evolution viewer
hack/assets/sprites/diy/   # Generated DIY PNG sprites
tools/bootstrap_evolved_starters.py
tools/generate_sprites.mjs
Play.sh / Play.bat / Play-Mac.command
```

The repo root remains an unmodified pokeemerald decompilation — `src/`,
`tools/`, `data/` and the `Makefile` are untouched, so the Emerald build works
exactly as before. gen1recomp is vendored under `engines/` rather than merged
into the root because both projects define `src/`, `tools/`, `data/` and
`assets/` with incompatible contents; overlaying them would break the Emerald
build outright. Details and the re-vendoring procedure are in
[`engines/VENDOR.md`](engines/VENDOR.md).

Two large upstream directories (~186 MB of third-party LÖVE/SDL2/LuaJIT sources
and prebuilt ANGLE/SDL2 DLLs) are not vendored — they are only needed for
Android and Xbox/UWP packaging. Restore them with
`engines/restore-gen1recomp-blobs.sh`.

## Credits

- **gen1recomp** by [bryanthaboi](https://github.com/bryanthaboi/gen1recomp) — the Gen 1 engine, MIT licensed, © BOIS CLUB GAMES, LLC (see `engines/gen1recomp/LICENSE.MD`)
- **Pokémon Evolved** ROM hack by AtSign8877 & team (LeafGreen) — evolution names and design inspiration
- **pret/pokeemerald** — decompilation base
- DIY sprites and Emerald port by this project

Pokémon is a trademark of Nintendo / Creatures Inc. / GAME FREAK Inc. This is an
unaffiliated fan project and distributes no game content.
