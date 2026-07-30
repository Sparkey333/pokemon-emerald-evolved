# Pokémon Emerald: Evolved Starters

Emerald ROM hack built on [pret/pokeemerald](https://github.com/pret/pokeemerald). Extends the three Kanto starter lines with **official Pokémon Evolved** expansion names/data **plus** our **DIY alternate branches**.

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

## Quick start

```bash
# 1. Apply starter species + evolution patches
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

## Project layout

```
hack/species.json          # Official + DIY species metadata
hack/showcase/             # Interactive HTML evolution viewer
hack/assets/sprites/diy/   # Generated DIY PNG sprites
tools/bootstrap_evolved_starters.py
tools/generate_sprites.mjs
```

## Credits

- **Pokémon Evolved** ROM hack by AtSign8877 & team (LeafGreen) — evolution names and design inspiration
- **pret/pokeemerald** — decompilation base
- DIY sprites and Emerald port by this project
