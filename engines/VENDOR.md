# Vendored engines

Third-party game engines live here as **subtrees**, not as a flat merge into the
repo root.

## Why not a flat merge

The repo root is a [pret/pokeemerald](https://github.com/pret/pokeemerald)
decompilation. `gen1recomp` is a LÖVE2D (Lua) engine. Both projects define
`src/`, `tools/`, `data/`, `docs/`, `assets/` and `.github/`, with completely
incompatible contents:

| Path | At repo root (pokeemerald) | In gen1recomp |
|------|----------------------------|---------------|
| `src/` | C source for the GBA ROM | Lua engine modules |
| `tools/` | `gbagfx`, `preproc`, `scaninc`, … — the `Makefile` depends on these | Python ROM importers / build helpers |
| `data/` | GBA assembly + map JSON | Lua game data |
| `assets/` | *(n/a)* | fonts, logos, touch controls |

Overlaying them would break the Emerald build outright. Vendoring under
`engines/<name>/` keeps both trees intact and buildable, which is the whole
point: the Emerald work is preserved exactly as it was.

---

## engines/gen1recomp

- **Upstream:** <https://github.com/bryanthaboi/gen1recomp>
- **Pinned commit:** `cab62ff7b340ba29ee212487fd9944fa636974a8`
- **License:** MIT — Copyright 2026 BOIS CLUB GAMES, LLC.
  The full text is preserved verbatim at `engines/gen1recomp/LICENSE.MD` and
  must stay there; MIT requires the copyright and permission notice to travel
  with the code.

### Local modifications

Exactly one file in the subtree is not from upstream:

- `engines/gen1recomp/.gitattributes` — added to *prevent* modification. The
  root `.gitattributes` normalizes line endings for the decomp tree
  (`*.ps1` → CRLF, `*.c`/`*.h`/`*.md`/`*.json` → LF); left unchecked it would
  rewrite ~1200 upstream files and make every re-vendor show whitespace-only
  diffs. `* -text` restores git's default so the subtree stays byte-identical
  to the pinned commit.

The root `.gitignore` also carries a scoped `!engines/gen1recomp/**` negation.
The decomp's patterns (`*.bat`, `*.js`, `*.a`, `*.map`, `build/`, …) are far too
broad for a vendored engine and would silently swallow real upstream sources
such as `Play-Windows.bat`, `mobile/android/gradlew.bat` and
`test/switch-nro-ota.spec.test.js`. `engines/gen1recomp/.gitignore` is deeper in
the tree, so upstream's own ignore rules still take precedence over that
negation and genuine build artifacts stay ignored.

### Deliberately excluded upstream paths

Two upstream directories are **not** vendored. They are third-party
redistributions totalling ~186 MB — more than eight times the size of the rest
of the project — and neither is needed to build, play, or modify the game on
desktop:

| Path | Size | What it is | Needed for |
|------|------|-----------|------------|
| `mobile/android/love/src/jni/` | 164 MB | Upstream's vendored copies of LÖVE, SDL2, LuaJIT and oboe (C/C++ sources) | Compiling an Android APK |
| `ports/uwp/third_party/` | 22 MB | Prebuilt Windows binaries — ANGLE `libGLESv2.dll`, `d3dcompiler_47.dll`, `love.dll`, `SDL2.dll`, `OpenAL32.dll` | Packaging an Xbox/UWP build |

Everything else is vendored in full: the complete Lua engine (`src/`), all
assets, game data, mods, tools, tests, docs, the desktop launchers, the iOS and
Switch port sources, and the Android app's own sources.

**Nothing about desktop play is affected by these exclusions.** They matter only
if you want to produce an Android or Xbox build.

### Restoring the excluded paths

```bash
engines/restore-gen1recomp-blobs.sh
```

This fetches the pinned upstream commit and drops both directories back into
place.

Upstream *tracks* both directories, so its own `.gitignore` does not cover
them. The root `.gitignore` therefore carries explicit rules for the two paths
(placed after the `!engines/gen1recomp/**` negation so they win), which keeps a
restore from dirtying the working tree or committing 186 MB back into this
repo.

### Re-vendoring a newer upstream

```bash
git clone https://github.com/bryanthaboi/gen1recomp.git /tmp/gen1recomp
cd /tmp/gen1recomp && git archive --format=tar HEAD | tar -x -C /path/to/engines/gen1recomp
rm -rf /path/to/engines/gen1recomp/mobile/android/love/src/jni \
       /path/to/engines/gen1recomp/ports/uwp/third_party
```

Then restore `engines/gen1recomp/.gitattributes` (upstream does not ship one)
and update the pinned commit at the top of this file.

---

## Game content

No ROM is included here, and none ever should be. Both engines require the user
to supply their own legally obtained cartridge dump:

- **gen1recomp** verifies a US Red / Blue / Yellow `.gb` by SHA-1 at import time.
- **The Emerald decomp** builds against a US Emerald `.gba` (see `rom.sha1`).
