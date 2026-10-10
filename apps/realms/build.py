#!/usr/bin/env python3
"""Assemble apps/realms/index.html from the parts in apps/realms/src/.

The game is written as separate source files so each stays readable:

    shell.html   page markup; carries two markers where CSS and JS are spliced in
    style.css    all styling
    data.js      types, type chart, moves, species roster, realms, encounters
    sprites.js   procedural pixel-sprite generator
    engine.js    game rules: stats, battle, catching, evolution, saves, hacks
    ui.js        screens, input, rendering, boot

Everything is inlined into one file because the page has to run as a
self-contained artifact (and from file://) with no external requests.

Usage:  python3 apps/realms/build.py
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
OUT = HERE / "index.html"

JS_ORDER = ["data.js", "sprites.js", "engine.js", "ui.js"]


def build() -> Path:
    shell = (SRC / "shell.html").read_text(encoding="utf-8")
    css = (SRC / "style.css").read_text(encoding="utf-8")
    js = "\n\n".join(
        f"// ---- {name} ----\n" + (SRC / name).read_text(encoding="utf-8")
        for name in JS_ORDER
    )
    page = (shell
            .replace("/*__STYLE__*/", css)
            .replace("//__SCRIPT__", js))
    OUT.write_text(page, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    out = build()
    print(f"wrote {out.name} ({out.stat().st_size:,} bytes)")
