#!/usr/bin/env python3
"""Generate art for forged species, then rebuild data + sheets.

Reads data/custom-species.json (written by the dashboard's forge panel) and
generates art for any species that doesn't have a front sprite yet. Safe to
re-run: it skips species already forged.

Usage: forge_species.py [--slug SLUG] [--all]
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import spritegen  # noqa: E402

DATA = os.path.join(ROOT, "data")
CUSTOM = os.path.join(DATA, "custom-species.json")


def brief_for(s):
    """Build the image brief from the species record."""
    if s.get("prompt"):
        body = s["prompt"]
    else:
        body = "%s, an original fan-designed creature. %s" % (
            s["name"], s.get("theme", ""))
    types = "/".join(s.get("types", [])) or "normal"
    extra = " %s type feel." % types
    if s.get("palette"):
        extra += " Palette: %s." % s["palette"]
    return body + extra


def main():
    only = sys.argv[sys.argv.index("--slug") + 1] if "--slug" in sys.argv else None
    if not os.path.exists(CUSTOM):
        print("no custom-species.json — nothing to forge")
        return
    with open(CUSTOM, encoding="utf-8") as f:
        species = json.load(f)

    calls, made = 0, []
    for s in species:
        slug = s.get("slug") or spritegen.slugify(s["name"])
        s["slug"] = slug
        if only and slug != only:
            continue
        outdir = os.path.join(ROOT, "vault", "forge", slug)
        if os.path.exists(os.path.join(outdir, "front.png")):
            print(slug, "already forged — skipping")
            continue
        print("forging", slug, "…")
        try:
            calls += spritegen.make_species_art(brief_for(s), outdir)
            made.append(slug)
            print("  ok:", slug)
        except Exception as e:
            print("  !! failed:", slug, str(e)[:160])

    with open(CUSTOM, "w", encoding="utf-8") as f:
        json.dump(species, f, indent=1)

    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_species.py")], check=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen_sheets.py"),
                    "--only", "forge"], check=True)
    print("forged %s | API calls: %d (~$%.2f)" % (made or "nothing", calls, calls * 0.039))


if __name__ == "__main__":
    main()
