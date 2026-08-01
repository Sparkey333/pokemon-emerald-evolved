#!/usr/bin/env python3
"""BYOK-generate the 6 DarkHearts DIY original species (front + back sprites).

Nano Banana (gemini-2.5-flash-image) per the spritez skill; key from ~/GameAssets.
Post-processing is local/$0: chroma-key the solid-green bg, downscale to 64px
nearest, quantize; shiny variants are a free PIL hue-shift. Masters are copied to
~/GameAssets/library/sprites with spritez naming. Re-run build_species.py +
gen_sheets.py afterward and the DIY sheets pick these up automatically.
"""
import base64, colorsys, json, os, shutil, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = os.path.expanduser("~")

def load_key():
    for p in (f"{HOME}/GameAssets/.env", f"{HOME}/GameAssets/GameAssets.env"):
        if os.path.exists(p):
            for line in open(p):
                if line.strip().startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1].strip().strip('"')
    return None

KEY = load_key()
if not KEY:
    sys.exit("no GEMINI_API_KEY found in ~/GameAssets")

STYLE = ("16-bit GBA Pokemon FireRed battle-sprite style pixel art, chunky pixels, "
         "dark outlines, limited palette of deep jewel tones (never pastel or neon), "
         "full body, single creature, centered, plain solid pure green background "
         "(#00ff00) filling the whole frame, no text, no watermark, no border")

SPECIES = {
    "florasaur": "Florasaur, an original fan-designed stone-evolution of a bulky quadruped "
        "plant dinosaur: massive body nearly hidden under an OVERSIZED blooming flower garden "
        "on its back — huge magenta and violet petals, emerald leaves, thick vines curling "
        "around its legs. Grass/poison type feel.",
    "verdantaur": "Verdantaur, an original fan-designed final evolution: a walking-garden "
        "colossus dinosaur — tree-sized canopy of layered blooms and hanging vines on its back, "
        "mossy armored hide, glowing amber pollen motes. Grass/poison type feel.",
    "charblaze": "Charblaze, an original fan-designed stone-evolution of a fire wyvern: "
        "blast-furnace themed — cracked obsidian-orange armor plates venting embers, twin "
        "furnace chest grilles glowing, wings of layered flame. Pure fire type feel.",
    "infernodrake": "Infernodrake, an original fan-designed final evolution: an aerial fire "
        "dragon — long serpentine body, vast ragged wings, magma-glow underbelly seams, horns "
        "swept back, trailing cinders. Fire/dragon type feel.",
    "torrentoise": "Torrentoise, an original fan-designed stone-evolution of a giant war "
        "turtle: tidal siege theme — sapphire shell crested like a breaking wave, four heavy "
        "water cannons at the shell rim, barnacle armor. Pure water type feel.",
    "tsunamoise": "Tsunamoise, an original fan-designed final evolution: a living tsunami "
        "fortress turtle — colossal shell shaped as a cresting wave frozen mid-break, water "
        "constantly spouting from turrets, deep teal and indigo palette. Pure water type feel.",
}

URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
       "gemini-2.5-flash-image:generateContent?key=" + KEY)

def gen(parts, tries=3):
    body = json.dumps({"contents": [{"parts": parts}]}).encode()
    for t in range(tries):
        try:
            req = urllib.request.Request(URL, data=body,
                                         headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
            for c in resp.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    if "inlineData" in p:
                        return base64.b64decode(p["inlineData"]["data"])
        except Exception as e:
            print("   retry after error:", str(e)[:120])
            time.sleep(4 * (t + 1))
    return None

# ── local post-processing ───────────────────────────────────────────────────
from PIL import Image

def chroma_key(im, tol=70):
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    # sample actual bg color from corners (model greens vary)
    corners = [px[0, 0], px[w-1, 0], px[0, h-1], px[w-1, h-1]]
    bg = max(set(c[:3] for c in corners), key=[c[:3] for c in corners].count)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if abs(r-bg[0]) + abs(g-bg[1]) + abs(b-bg[2]) < tol and g > r and g > b:
                px[x, y] = (0, 0, 0, 0)
    return im

def to_sprite(raw):
    im = chroma_key(Image.open(__import__("io").BytesIO(raw)))
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    im.thumbnail((58, 58), Image.LANCZOS)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.paste(im, ((64 - im.width) // 2, 64 - im.height))
    q = canvas.convert("RGB").quantize(48).convert("RGBA")
    q.putalpha(canvas.split()[3])
    return q

def hue_shift(im, dh=0.38):
    out = im.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                hh, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
                r2, g2, b2 = colorsys.hls_to_rgb((hh + dh) % 1, l, s)
                px[x, y] = (int(r2*255), int(g2*255), int(b2*255), a)
    return out

LIB = os.path.join(HOME, "GameAssets", "library", "sprites")
os.makedirs(LIB, exist_ok=True)
made, cost_calls = [], 0

for slug, brief in SPECIES.items():
    d = os.path.join(ROOT, "vault", "diy", slug)
    os.makedirs(d, exist_ok=True)
    if os.path.exists(os.path.join(d, "front.png")) and os.path.exists(os.path.join(d, "back.png")):
        print(slug, "already generated — skipping")
        continue
    print("generating", slug, "front…")
    raw_front = gen([{"text": f"{brief} {STYLE}. Front-facing battle pose (facing the viewer)."}])
    cost_calls += 1
    if not raw_front:
        print("  !! front failed for", slug)
        continue
    front = to_sprite(raw_front)
    front.save(os.path.join(d, "front.png"))
    Image.open(__import__("io").BytesIO(raw_front)).save(os.path.join(d, "front-master.png"))

    print("generating", slug, "back…")
    raw_back = gen([
        {"inlineData": {"mimeType": "image/png",
                        "data": base64.b64encode(raw_front).decode()}},
        {"text": "Same exact creature, same palette and pixel-art style, but seen FROM BEHIND "
                 "(back battle sprite as in GBA Pokemon battles, slightly larger crop). "
                 + STYLE}])
    cost_calls += 1
    if raw_back:
        to_sprite(raw_back).save(os.path.join(d, "back.png"))
        Image.open(__import__("io").BytesIO(raw_back)).save(os.path.join(d, "back-master.png"))

    hue_shift(front).save(os.path.join(d, "shiny.png"))
    if os.path.exists(os.path.join(d, "back.png")):
        hue_shift(Image.open(os.path.join(d, "back.png"))).save(os.path.join(d, "back-shiny.png"))

    for k in ("front", "back"):
        src = os.path.join(d, f"{k}-master.png")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(LIB, f"pokemon-emerald-evolved__sprites__{slug}-{k}__v01.png"))
    made.append(slug)
    print("  ok:", slug)

print(f"done: {made} | API calls: {cost_calls} (~${cost_calls*0.039:.2f} at Nano Banana rates)")
