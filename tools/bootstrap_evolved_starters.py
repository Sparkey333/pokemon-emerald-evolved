#!/usr/bin/env python3
"""Bootstrap Pokemon Evolved starter extensions into pokeemerald."""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HACK = ROOT / "hack"
SPECIES_JSON = json.loads((HACK / "species.json").read_text())

ITEM_MAP = {
    "LEAF_STONE": "ITEM_LEAF_STONE",
    "FIRE_STONE": "ITEM_FIRE_STONE",
    "WATER_STONE": "ITEM_WATER_STONE",
}

TYPE_MAP = {
    "GRASS": "TYPE_GRASS",
    "POISON": "TYPE_POISON",
    "FIRE": "TYPE_FIRE",
    "FLYING": "TYPE_FLYING",
    "WATER": "TYPE_WATER",
    "STEEL": "TYPE_STEEL",
    "DRAGON": "TYPE_DRAGON",
}

ABILITY_MAP = {
    "OVERGROW": "ABILITY_OVERGROW",
    "CHLOROPHYLL": "ABILITY_CHLOROPHYLL",
    "BLAZE": "ABILITY_BLAZE",
    "MARVEL_SCALE": "ABILITY_MARVEL_SCALE",
    "TORRENT": "ABILITY_TORRENT",
    "SHELL_ARMOR": "ABILITY_SHELL_ARMOR",
}

PARENT_GFX = {
    "ECOSAUR": "venusaur", "TERARISAUR": "venusaur", "SYMBISAUR": "venusaur",
    "FLORASAUR": "venusaur", "VERDANTAUR": "venusaur",
    "CHARIGUANA": "charizard", "CHARIANA": "charizard", "CHARIATHAN": "charizard",
    "CHARBLAZE": "charizard", "INFERNODRAKE": "charizard",
    "FERRAPIN": "blastoise", "FORTOISE": "blastoise", "TURTILLERY": "blastoise",
    "TORRENTOISE": "blastoise", "TSUNAMOISE": "blastoise",
}

PARENT_SPECIES = {
    "ECOSAUR": "VENUSAUR", "TERARISAUR": "VENUSAUR", "SYMBISAUR": "VENUSAUR",
    "FLORASAUR": "VENUSAUR", "VERDANTAUR": "VENUSAUR",
    "CHARIGUANA": "CHARIZARD", "CHARIANA": "CHARIZARD", "CHARIATHAN": "CHARIZARD",
    "CHARBLAZE": "CHARIZARD", "INFERNODRAKE": "CHARIZARD",
    "FERRAPIN": "BLASTOISE", "FORTOISE": "BLASTOISE", "TURTILLERY": "BLASTOISE",
    "TORRENTOISE": "BLASTOISE", "TSUNAMOISE": "BLASTOISE",
}

LEARNSET_PARENT = {
    "ECOSAUR": "VENUSAUR", "TERARISAUR": "VENUSAUR", "SYMBISAUR": "VENUSAUR",
    "FLORASAUR": "VENUSAUR", "VERDANTAUR": "VENUSAUR",
    "CHARIGUANA": "CHARIZARD", "CHARIANA": "CHARIZARD", "CHARIATHAN": "CHARIZARD",
    "CHARBLAZE": "CHARIZARD", "INFERNODRAKE": "CHARIZARD",
    "FERRAPIN": "BLASTOISE", "FORTOISE": "BLASTOISE", "TURTILLERY": "BLASTOISE",
    "TORRENTOISE": "BLASTOISE", "TSUNAMOISE": "BLASTOISE",
}


def all_new_species() -> list[dict]:
    out = []
    for group in ("official", "diy"):
        for line in SPECIES_JSON[group].values():
            for s in line:
                out.append({**s, "group": group})
    return out


def insert_before(path: Path, needle: str, block: str) -> None:
    text = path.read_text()
    if block.strip() in text:
        return
    if needle not in text:
        raise SystemExit(f"needle not found in {path}: {needle!r}")
    path.write_text(text.replace(needle, block + needle, 1))


def patch_species_h(species: list[dict]) -> None:
    path = ROOT / "include/constants/species.h"
    text = path.read_text()
    if "SPECIES_ECOSAUR" in text:
        print("species.h already patched")
        return
    lines = []
    base = 412
    for i, s in enumerate(species):
        lines.append(f"#define SPECIES_{s['id']} {base + i}")
    block = "\n".join(lines) + "\n"
    text = text.replace(
        "#define SPECIES_EGG 412",
        block + "#define SPECIES_EGG " + str(base + len(species)),
    )
    path.write_text(text)
    print(f"patched species.h (+{len(species)} species)")


def patch_evolution_h(species: list[dict]) -> None:
    path = ROOT / "src/data/pokemon/evolution.h"
    text = path.read_text()
    if "SPECIES_ECOSAUR" in text:
        print("evolution.h already patched")
        return

    # Extend vanilla finals with dual branches
    text = text.replace(
        "    [SPECIES_IVYSAUR]    = {{EVO_LEVEL, 32, SPECIES_VENUSAUR}},",
        "    [SPECIES_IVYSAUR]    = {{EVO_LEVEL, 32, SPECIES_VENUSAUR}},",
    )
    text = text.replace(
        "    [SPECIES_WARTORTLE]  = {{EVO_LEVEL, 36, SPECIES_BLASTOISE}},",
        "    [SPECIES_WARTORTLE]  = {{EVO_LEVEL, 36, SPECIES_BLASTOISE}},",
    )

    additions = []
    additions.append(
        "    [SPECIES_VENUSAUR]   = {{EVO_LEVEL, 41, SPECIES_ECOSAUR}, {EVO_ITEM, ITEM_LEAF_STONE, SPECIES_FLORASAUR}},"
    )
    additions.append(
        "    [SPECIES_CHARIZARD]  = {{EVO_LEVEL, 41, SPECIES_CHARIGUANA}, {EVO_ITEM, ITEM_FIRE_STONE, SPECIES_CHARBLAZE}},"
    )
    additions.append(
        "    [SPECIES_BLASTOISE]  = {{EVO_LEVEL, 41, SPECIES_FERRAPIN}, {EVO_ITEM, ITEM_WATER_STONE, SPECIES_TORRENTOISE}},"
    )

    skip_from = {"VENUSAUR", "CHARIZARD", "BLASTOISE"}
    for s in species:
        if s["from"] in skip_from:
            continue
        if s["method"] == "LEVEL":
            additions.append(
                f"    [SPECIES_{s['from']}] = {{{{EVO_LEVEL, {s['param']}, SPECIES_{s['id']}}}}},"
            )
        elif s["method"] == "ITEM":
            item = ITEM_MAP[s["param"]]
            additions.append(
                f"    [SPECIES_{s['from']}] = {{{{EVO_ITEM, {item}, SPECIES_{s['id']}}}}},"
            )

    block = "\n".join(additions) + "\n"
    insert_before(path, "    [SPECIES_CATERPIE]", block)
    print("patched evolution.h")


def extract_species_block(text: str, species_id: str) -> str:
    m = re.search(
        rf"\[SPECIES_{species_id}\]\s*=\s*\{{.*?\n\s*\}},",
        text,
        re.DOTALL,
    )
    if not m:
        raise SystemExit(f"could not find species block for {species_id}")
    return m.group(0)


def bump_stats(block: str, stage: int) -> str:
    def repl(m):
        val = int(m.group(2))
        return f".{m.group(1)} = {min(255, val + 8 + stage * 4)}"

    for field in ("baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack", "baseSpDefense"):
        block = re.sub(rf"(\.{field}\s*=\s*)(\d+)", repl, block)
    return block


def patch_species_info(species: list[dict]) -> None:
    path = ROOT / "src/data/pokemon/species_info.h"
    text = path.read_text()
    if "[SPECIES_ECOSAUR]" in text:
        print("species_info.h already patched")
        return

    blocks = []
    for i, s in enumerate(species):
        parent = PARENT_SPECIES[s["id"]]
        block = extract_species_block(text, parent)
        block = block.replace(f"[SPECIES_{parent}]", f"[SPECIES_{s['id']}]")
        block = bump_stats(block, i % 3)
        t0, t1 = TYPE_MAP[s["types"][0]], TYPE_MAP[s["types"][1]]
        block = re.sub(
            r"\.types = \{ TYPE_[A-Z_]+, TYPE_[A-Z_]+ \}",
            f".types = {{ {t0}, {t1} }}",
            block,
        )
        ab = ABILITY_MAP.get(s.get("ability", "NONE"), "ABILITY_NONE")
        block = re.sub(
            r"\.abilities = \{ABILITY_[A-Z_]+, ABILITY_[A-Z_]+\}",
            f".abilities = {{{ab}, ABILITY_NONE}}",
            block,
        )
        blocks.append(block)

    insert_before(path, "    [SPECIES_CHIMECHO] =\n    {", "\n\n" + "\n\n".join(blocks) + "\n")
    print("patched species_info.h")


def patch_species_names(species: list[dict]) -> None:
    path = ROOT / "src/data/text/species_names.h"
    lines = [f'    [SPECIES_{s["id"]}] = _("{s["name"]}"),' for s in species]
    insert_before(path, "    [SPECIES_CHIMECHO]", "\n".join(lines) + "\n")
    print("patched species_names.h")


def copy_graphics(species: list[dict]) -> None:
    for s in species:
        sid = s["id"].lower()
        parent = PARENT_GFX[s["id"]]
        src = ROOT / "graphics/pokemon" / parent
        dst = ROOT / "graphics/pokemon" / sid
        if dst.exists():
            continue
        shutil.copytree(src, dst)
        # overlay DIY png if present
        diy = HACK / "assets/sprites/diy" / f"{sid}.png"
        if diy.exists():
            shutil.copy(diy, dst / "front.png")
            shutil.copy(diy, dst / "anim_front.png")
    print("copied graphics folders")


def patch_graphics_tables(species: list[dict]) -> None:
    table_needles = [
        ("src/data/pokemon_graphics/front_pic_table.h", "SPECIES_SPRITE", "    SPECIES_SPRITE(CHIMECHO, gMonFrontPic_Chimecho),"),
        ("src/data/pokemon_graphics/back_pic_table.h", "SPECIES_SPRITE", "    SPECIES_SPRITE(CHIMECHO, gMonBackPic_Chimecho),"),
        ("src/data/pokemon_graphics/palette_table.h", "SPECIES_PAL", "    SPECIES_PAL(CHIMECHO, gMonPalette_Chimecho),"),
        ("src/data/pokemon_graphics/shiny_palette_table.h", "SPECIES_SHINY_PAL", "    SPECIES_SHINY_PAL(CHIMECHO, gMonShinyPalette_Chimecho),"),
        ("src/data/pokemon_graphics/still_front_pic_table.h", "SPECIES_SPRITE", "    SPECIES_SPRITE(CHIMECHO,      gMonStillFrontPic_Chimecho),"),
    ]
    for rel, kind, needle in table_needles:
        path = ROOT / rel
        if "SPECIES_ECOSAUR" in path.read_text():
            continue
        additions = []
        for s in species:
            sid = s["id"]
            camel = "".join(p.capitalize() for p in sid.lower().split("_"))
            if kind == "SPECIES_SPRITE":
                if "back_pic" in rel:
                    sym = f"gMonBackPic_{camel}"
                elif "still" in rel:
                    sym = f"gMonStillFrontPic_{camel}"
                else:
                    sym = f"gMonFrontPic_{camel}"
                additions.append(f"    SPECIES_SPRITE({sid}, {sym}),")
            elif kind == "SPECIES_PAL":
                additions.append(f"    SPECIES_PAL({sid}, gMonPalette_{camel}),")
            else:
                additions.append(f"    SPECIES_SHINY_PAL({sid}, gMonShinyPalette_{camel}),")
        insert_before(path, needle, "\n".join(additions) + "\n")
    print("patched graphics tables")


def patch_graphics_h(species: list[dict]) -> None:
    path = ROOT / "src/data/graphics/pokemon.h"
    text = path.read_text()
    additions = []
    for s in species:
        sid = s["id"].lower()
        camel = "".join(p.capitalize() for p in sid.lower().split("_"))
        if f"gMonFrontPic_{camel}" in text:
            continue
        additions.append(f'const u32 gMonFrontPic_{camel}[] = INCGFX_U32("graphics/pokemon/{sid}/anim_front.png", ".4bpp.lz");')
        additions.append(f'const u32 gMonPalette_{camel}[] = INCGFX_U32("graphics/pokemon/{sid}/normal.pal", ".gbapal.lz");')
        additions.append(f'const u32 gMonBackPic_{camel}[] = INCGFX_U32("graphics/pokemon/{sid}/back.png", ".4bpp.lz");')
        additions.append(f'const u32 gMonShinyPalette_{camel}[] = INCGFX_U32("graphics/pokemon/{sid}/shiny.pal", ".gbapal.lz");')
        additions.append(f'const u8 gMonIcon_{camel}[] = INCGFX_U8("graphics/pokemon/{sid}/icon.png", ".4bpp");')
    if additions:
        insert_before(path, "const u32 gMonStillFrontPic_Chimecho", "\n".join(additions) + "\n")
    print("patched src/data/graphics/pokemon.h")


def patch_anim_front_pics(species: list[dict]) -> None:
    path = ROOT / "src/anim_mon_front_pics.c"
    additions = []
    for s in species:
        sid = s["id"].lower()
        camel = "".join(p.capitalize() for p in sid.lower().split("_"))
        line = f'const u32 gMonFrontPic_{camel}[] = INCGFX_U32("graphics/pokemon/{sid}/anim_front.png", ".4bpp.lz");'
        if line not in path.read_text():
            additions.append(line)
    if additions:
        insert_before(path, "const u32 gMonFrontPic_Egg", "\n".join(additions) + "\n")
    print("patched anim_mon_front_pics.c")


def patch_icon_table(species: list[dict]) -> None:
    path = ROOT / "src/pokemon_icon.c"
    if "[SPECIES_ECOSAUR]" in path.read_text():
        print("pokemon_icon.c already patched")
        return
    additions = []
    for s in species:
        camel = "".join(p.capitalize() for p in s["id"].lower().split("_"))
        additions.append(f"    [SPECIES_{s['id']}] = gMonIcon_{camel},")
    insert_before(path, "    [SPECIES_CHIMECHO]", "\n".join(additions) + "\n")
    print("patched pokemon_icon.c")


def patch_learnsets(species: list[dict]) -> None:
    path = ROOT / "src/data/pokemon/level_up_learnset_pointers.h"
    additions = []
    for s in species:
        parent = LEARNSET_PARENT[s["id"]]
        p = parent.capitalize()
        additions.append(f"    [SPECIES_{s['id']}] = s{p}LevelUpLearnset,")
    insert_before(path, "    [SPECIES_CHIMECHO]", "\n".join(additions) + "\n")
    print("patched learnset pointers")


def patch_coordinates(species: list[dict]) -> None:
    for rel, parent_key in [
        ("src/data/pokemon_graphics/front_pic_coordinates.h", "front"),
        ("src/data/pokemon_graphics/back_pic_coordinates.h", "back"),
    ]:
        path = ROOT / rel
        text = path.read_text()
        additions = []
        for s in species:
            parent = PARENT_SPECIES[s["id"]]
            m = re.search(rf"\[SPECIES_{parent}\]\s*=\s*\{{[^}}]+\}},", text)
            if not m:
                continue
            line = m.group(0).replace(f"SPECIES_{parent}", f"SPECIES_{s['id']}")
            additions.append("    " + line)
        if additions:
            insert_before(path, f"    [SPECIES_CHIMECHO]", "\n".join(additions) + "\n")
    print("patched coordinate tables")


def main() -> None:
    species = all_new_species()
    print(f"Bootstrapping {len(species)} new species...")
    patch_species_h(species)
    patch_evolution_h(species)
    patch_species_info(species)
    patch_species_names(species)
    copy_graphics(species)
    patch_graphics_tables(species)
    patch_graphics_h(species)
    patch_anim_front_pics(species)
    patch_icon_table(species)
    patch_learnsets(species)
    patch_coordinates(species)
    print("Done. Run: make -j$(sysctl -n hw.ncpu)")


if __name__ == "__main__":
    main()
