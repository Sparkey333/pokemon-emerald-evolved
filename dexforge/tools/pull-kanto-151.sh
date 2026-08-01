#!/bin/bash
# Pull Gen-III FireRed/LeafGreen sprites for the original 151 from PokeAPI's public sprites repo,
# plus species/type/stat CSVs. LOCAL REFERENCE VAULT ONLY — Nintendo/Game Freak/Creatures IP;
# never ship these files inside any distributed build (see README guardrails).
set -u
BASE="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/vault/kanto-151"
mkdir -p "$DEST/front" "$DEST/back" "$DEST/shiny" "$DEST/back-shiny"

# macOS/BSD xargs caps -I replacement commands at 255 bytes, so the per-id work
# lives in fetch-one-kanto.sh and ids are passed as plain args.
seq 1 151 | xargs -n 1 -P 12 "$ROOT/tools/fetch-one-kanto.sh"

DATA="$ROOT/data"
mkdir -p "$DATA"
CSV="https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv"
for f in pokemon.csv pokemon_types.csv types.csv pokemon_stats.csv stats.csv pokemon_species.csv; do
  [ -s "$DATA/$f" ] || curl -sf "$CSV/$f" -o "$DATA/$f"
done

echo "counts — front: $(ls "$DEST/front" 2>/dev/null | wc -l | tr -d ' '), back: $(ls "$DEST/back" 2>/dev/null | wc -l | tr -d ' '), shiny: $(ls "$DEST/shiny" 2>/dev/null | wc -l | tr -d ' '), back-shiny: $(ls "$DEST/back-shiny" 2>/dev/null | wc -l | tr -d ' ')"
# spritez rule: verify downloads are real images (HTML output = failed/auth)
file "$DEST/front/1.png" "$DEST/front/151.png" "$DEST/back/25.png" 2>/dev/null
ls -la "$DATA" | tail -8
