#!/usr/bin/env bash
# Restore the two large third-party directories that are deliberately not
# vendored into this repo. See engines/VENDOR.md for the rationale.
#
#   mobile/android/love/src/jni/  (164 MB) - LOVE/SDL2/LuaJIT/oboe sources, for APK builds
#   ports/uwp/third_party/        ( 22 MB) - prebuilt ANGLE/LOVE/SDL2/OpenAL DLLs, for UWP builds
#
# Neither is needed to play or modify the game on desktop.

set -euo pipefail

UPSTREAM="https://github.com/bryanthaboi/gen1recomp.git"
# Keep in sync with the pinned commit in engines/VENDOR.md.
COMMIT="cab62ff7b340ba29ee212487fd9944fa636974a8"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$HERE/gen1recomp"

PATHS=(
  "mobile/android/love/src/jni"
  "ports/uwp/third_party"
)

if [ ! -d "$DEST" ]; then
  echo "error: $DEST not found - run this from a checkout of the repo" >&2
  exit 1
fi

missing=0
for p in "${PATHS[@]}"; do
  [ -d "$DEST/$p" ] || missing=1
done
if [ "$missing" -eq 0 ]; then
  echo "Both directories are already present - nothing to do."
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "==> fetching gen1recomp @ ${COMMIT:0:12} (this pulls ~186 MB)"
git init -q "$TMP/upstream"
git -C "$TMP/upstream" remote add origin "$UPSTREAM"

# Try the cheap path first: a single-commit fetch. Some servers disallow
# fetching an arbitrary SHA, so fall back to a full clone.
if git -C "$TMP/upstream" fetch -q --depth 1 origin "$COMMIT" 2>/dev/null; then
  git -C "$TMP/upstream" checkout -q FETCH_HEAD
else
  echo "==> server refused a single-commit fetch, cloning instead"
  rm -rf "$TMP/upstream"
  git clone -q "$UPSTREAM" "$TMP/upstream"
  git -C "$TMP/upstream" checkout -q "$COMMIT"
fi

for p in "${PATHS[@]}"; do
  if [ -d "$DEST/$p" ]; then
    echo "==> skip $p (already present)"
    continue
  fi
  if [ ! -d "$TMP/upstream/$p" ]; then
    echo "warning: $p does not exist at this upstream commit - skipping" >&2
    continue
  fi
  echo "==> restoring $p"
  mkdir -p "$(dirname "$DEST/$p")"
  cp -R "$TMP/upstream/$p" "$DEST/$p"
done

echo
echo "Done. The root .gitignore lists both paths explicitly, so they stay out"
echo "of 'git status' and will not be committed back into this repo."
