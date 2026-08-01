#!/usr/bin/env python3
"""Export shippable original species into the pokeemerald decomp.

Indigo Dexforge is the FORGE (research, art, sheets); ~/Projects/pokemon-emerald-evolved
is the BUILD TARGET (pret/pokeemerald fork). This copies only species we own —
vault/diy and vault/forge — into the decomp's graphics layout:

    graphics/pokemon/<slug>/front.png
                            back.png
                            normal.pal
                            shiny.pal

Nothing from vault/kanto-151 or vault/evolved is ever exported: that art belongs to
Nintendo/Game Freak and to the Pokemon Evolved artists, and stays reference-only.

Also cross-checks the decomp's hack/species.json against Dexforge's data and reports
drift, so the two projects can't silently disagree.

Usage: export_to_decomp.py [--decomp PATH] [--dry-run]
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DECOMP = os.path.expanduser("~/Projects/pokemon-emerald-evolved")
SHIPPABLE = ("diy", "forge")


def pal_from(img, path):
    """Write a JASC-PAL palette next to the sprite (decomp expects 16 colours)."""
    from PIL import Image
    im = Image.open(img).convert("RGBA")
    seen, colours = set(), [(0, 0, 0)]          # index 0 = transparent key
    for px in im.getdata():
        if px[3] > 128 and px[:3] not in seen:
            seen.add(px[:3])
            colours.append(px[:3])
    colours = colours[:16] + [(0, 0, 0)] * max(0, 16 - len(colours))
    with open(path, "w") as f:
        f.write("JASC-PAL\n0100\n16\n")
        for c in colours[:16]:
            f.write("%d %d %d\n" % c)


def main():
    decomp = (sys.argv[sys.argv.index("--decomp") + 1]
              if "--decomp" in sys.argv else DEFAULT_DECOMP)
    dry = "--dry-run" in sys.argv
    if not os.path.isdir(os.path.join(decomp, "graphics", "pokemon")):
        sys.exit("not a pokeemerald decomp: %s" % decomp)

    with open(os.path.join(ROOT, "data", "species.json"), encoding="utf-8") as f:
        dex = json.load(f)

    import shutil
    exported, skipped = [], []
    for section in SHIPPABLE:
        for e in dex.get(section, []):
            src = os.path.join(ROOT, "vault", section, e["slug"])
            front = os.path.join(src, "front.png")
            if not os.path.exists(front):
                skipped.append(e["name"])
                continue
            dst = os.path.join(decomp, "graphics", "pokemon", e["slug"])
            if not dry:
                os.makedirs(dst, exist_ok=True)
                shutil.copy(front, os.path.join(dst, "front.png"))
                back = os.path.join(src, "back.png")
                if os.path.exists(back):
                    shutil.copy(back, os.path.join(dst, "back.png"))
                pal_from(front, os.path.join(dst, "normal.pal"))
                shiny = os.path.join(src, "shiny.png")
                if os.path.exists(shiny):
                    pal_from(shiny, os.path.join(dst, "shiny.pal"))
            exported.append(e["name"])

    print("%s %d species -> %s" % ("would export" if dry else "exported",
                                   len(exported), decomp))
    for n in exported:
        print("   +", n)
    if skipped:
        print("   (no art yet, skipped: %s)" % ", ".join(skipped))

    # ── drift check against the decomp's own species table ──────────────
    hack = os.path.join(decomp, "hack", "species.json")
    if os.path.exists(hack):
        with open(hack, encoding="utf-8") as f:
            h = json.load(f)
        theirs = {s["name"].lower()
                  for group in ("official", "diy")
                  for line in h.get(group, {}).values() for s in line}
        ours_diy = {e["name"].lower() for e in dex.get("diy", [])}
        ours_evolved = {e["name"].lower() for e in dex.get("evolved", [])}
        print("\ndrift vs decomp hack/species.json:")
        missing = sorted(ours_diy - theirs)
        extra = sorted(theirs - ours_diy - ours_evolved)
        print("   decomp is missing from our DIY branch: %s" % (missing or "nothing"))
        print("   decomp has, we don't track:            %s" % (extra or "nothing"))
        print("   decomp covers %d of our %d Evolved species"
              % (len(theirs & ours_evolved), len(ours_evolved)))


if __name__ == "__main__":
    main()
