#!/usr/bin/env bash
# Pokemon Evolved - one launcher for everything in this repo (macOS / Linux).
#
#   ./Play.sh                    open the hub (tabbed launcher) in your browser
#   ./Play.sh hub                same
#   ./Play.sh gen1               play Gen 1 (Red/Blue/Yellow) via engines/gen1recomp
#   ./Play.sh gen1 --rom FILE    ...pointing the importer at a specific ROM
#   ./Play.sh emerald            open the Emerald evolution showcase
#   ./Play.sh build-hub          regenerate apps/hub/index.html from source data
#
# No ROMs ship with this repository. Gen 1 asks for your own legally obtained
# .gb/.gbc on first run; the Emerald build needs your own Emerald .gba.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

say()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; }

open_file() { # open a local file in the default browser
  local target="$1"
  if [ ! -f "$target" ]; then
    err "not found: $target"
    return 1
  fi
  if command -v open >/dev/null 2>&1; then          # macOS
    open "$target"
  elif command -v xdg-open >/dev/null 2>&1; then    # Linux desktop
    xdg-open "$target" >/dev/null 2>&1
  else
    say "no browser opener found - open this file yourself:"
    printf '    %s\n' "$target"
  fi
}

usage() {
  # Print the header comment block: everything after the shebang up to the
  # first non-comment line. Beats a hardcoded line range, which drifts the
  # moment this file is edited.
  awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"
}

cmd="${1:-hub}"
[ "$#" -gt 0 ] && shift || true

case "$cmd" in
  hub)
    hub="$ROOT/apps/hub/index.html"
    # Regenerate if the page is missing or its sources are newer.
    if [ ! -f "$hub" ] && command -v python3 >/dev/null 2>&1; then
      say "generating the hub page"
      python3 "$ROOT/apps/hub/build_hub.py"
    fi
    say "opening the hub"
    open_file "$hub"
    ;;

  gen1|rby|red|blue|yellow)
    engine="$ROOT/engines/gen1recomp"
    if [ ! -f "$engine/main.lua" ]; then
      err "engines/gen1recomp is missing - see engines/VENDOR.md"
      exit 1
    fi
    say "starting Gen 1 (gen1recomp)"
    say "first run decodes a ROM you supply; later runs launch straight away"
    # play.sh = setup (ROM import + LOVE install) then run. Extra args such as
    # --rom /path/to/pokemon-red.gb are passed straight through.
    exec "$engine/scripts/play.sh" "$@"
    ;;

  emerald|gen3|showcase)
    say "opening the Emerald evolution showcase"
    open_file "$ROOT/hack/showcase/pokemon-evolved-official-vs-diy.html"
    ;;

  build-hub)
    command -v python3 >/dev/null 2>&1 || { err "python3 is required"; exit 1; }
    exec python3 "$ROOT/apps/hub/build_hub.py"
    ;;

  -h|--help|help)
    usage
    ;;

  *)
    err "unknown command: $cmd"
    echo
    usage
    exit 2
    ;;
esac
