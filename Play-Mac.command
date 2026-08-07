#!/bin/bash
# Double-clickable macOS entry point: opens the Pokemon Evolved hub.
# From the hub's Gen 1 tab you can start the playable Red/Blue/Yellow engine,
# or run `./Play.sh gen1` directly from a terminal.
cd "$(dirname "$0")" || exit 1
exec ./Play.sh hub
