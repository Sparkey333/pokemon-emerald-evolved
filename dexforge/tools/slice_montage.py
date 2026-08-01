#!/usr/bin/env python3
"""Slice calicorn's Pokemon Evolved sprite montage into per-creature PNGs.

Measured geometry: 406x960, 12 cols x 25 rows, cell 33.83 x 38.4, a ~9px label
chip at the top of each cell, and ADJACENT CELLS ARE NORMAL+SHINY PAIRS of the
same creature -> 272 filled cells = 136 creatures.

IMPORTANT — no dex mapping is invented here. The per-cell dex labels are ~3px
tall and destroyed by Tumblr's downscale (s640x960 is the largest stored size;
s1280/s2048 404), so they are genuinely unreadable. Cells are therefore emitted
in grid order as `cell-NNN` and mapped to species MANUALLY via the dashboard's
mapper (data/montage-map.json). Anything else would be a guess presented as data.

Local reference vault only — art by calicorn for PointCrow's Pokemon Evolved.
"""
import json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "vault/evolved/reveal-art/calicorn/pointcrow-dump-0.png")
DEST = os.path.join(ROOT, "vault/evolved/montage")
COLS, ROWS, CHIP = 12, 25, 9

def bg_of(im):
    """Most common colour in the sprite area = the flat green backdrop."""
    from collections import Counter
    w, h = im.size
    edge = [im.getpixel((x, y)) for x in range(w) for y in (CHIP + 1, h - 2)]
    return Counter(edge).most_common(1)[0][0]

def cut(im):
    """Drop the label chip + cell borders, chroma-key the green backdrop,
    trim, and centre on a 64x64 canvas."""
    im = im.crop((2, CHIP + 1, im.width - 1, im.height - 1))
    im = im.convert("RGBA")
    bg = bg_of(im.convert("RGB"))
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, _ = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) < 46:
                px[x, y] = (0, 0, 0, 0)
    bbox = im.getbbox()
    if not bbox:
        return None
    im = im.crop(bbox)
    if max(im.size) > 60:
        im.thumbnail((60, 60), Image.NEAREST)
    out = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    out.paste(im, ((64 - im.width) // 2, 64 - im.height), im)
    return out

def main():
    im = Image.open(SRC).convert("RGB")
    W, H = im.size
    cw, chh = W / COLS, H / ROWS
    os.makedirs(DEST, exist_ok=True)

    # collect filled cells in reading order
    cells = []
    for r in range(ROWS):
        for c in range(COLS):
            x0, y0 = int(c * cw), int(r * chh)
            x1, y1 = int((c + 1) * cw), int((r + 1) * chh)
            tile = im.crop((x0, y0, x1, y1))
            colours = set(tile.crop((1, CHIP + 1, tile.width - 1, tile.height - 1))
                          .resize((12, 12), Image.NEAREST).getdata())
            if len(colours) > 6:
                cells.append((r, c, tile))

    pairs, manifest = 0, []
    for i in range(0, len(cells) - 1, 2):
        (r, c, a), (r2, c2, b) = cells[i], cells[i + 1]
        if r != r2 or c2 != c + 1:      # pair must be side-by-side in one row
            continue
        normal, shiny = cut(a), cut(b)
        if not normal:
            continue
        key = "cell-%03d" % (pairs + 1)
        normal.save(os.path.join(DEST, key + "-normal.png"))
        if shiny:
            shiny.save(os.path.join(DEST, key + "-shiny.png"))
        manifest.append({"key": key, "row": r, "col": c,
                         "normal": "vault/evolved/montage/%s-normal.png" % key,
                         "shiny": "vault/evolved/montage/%s-shiny.png" % key})
        pairs += 1

    meta = {"note": "Sliced from calicorn's Pokemon Evolved sprite montage. Dex labels are "
                    "unreadable at the only available resolution, so cells are in grid order "
                    "and mapped to species by hand in the dashboard. Local reference only.",
            "credit": "calicorn (lead spriter) — Pokemon Evolved, commissioned by PointCrow",
            "source": "https://calicorn.tumblr.com/post/773847627888525312",
            "cells": manifest}
    with open(os.path.join(DEST, "montage-manifest.json"), "w") as f:
        json.dump(meta, f, indent=1)
    with open(os.path.join(ROOT, "data", "montage.js"), "w") as f:
        f.write("window.MONTAGE = ")
        json.dump(meta, f)
        f.write(";\n")
    print("sliced %d creature pairs from %d filled cells" % (pairs, len(cells)))

if __name__ == "__main__":
    main()
