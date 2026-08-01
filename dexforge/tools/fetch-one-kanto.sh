#!/bin/bash
# Fetch one dex id's FRLG sprite set (front/back/shiny/back-shiny). Called by pull-kanto-151.sh.
i="$1"
BASE="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen"
DEST="$(cd "$(dirname "$0")/.." && pwd)/vault/kanto-151"
[ -s "$DEST/front/$i.png" ]      || curl -sf "$BASE/$i.png"            -o "$DEST/front/$i.png"
[ -s "$DEST/back/$i.png" ]       || curl -sf "$BASE/back/$i.png"       -o "$DEST/back/$i.png"
[ -s "$DEST/shiny/$i.png" ]      || curl -sf "$BASE/shiny/$i.png"      -o "$DEST/shiny/$i.png"
[ -s "$DEST/back-shiny/$i.png" ] || curl -sf "$BASE/back/shiny/$i.png" -o "$DEST/back-shiny/$i.png"
