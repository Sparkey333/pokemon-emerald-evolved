#!/usr/bin/env python3
"""Shared BYOK sprite generation for Indigo Dexforge.

Nano Banana (gemini-2.5-flash-image) for art; every post-process step is local
and free (chroma-key, downscale, quantize, hue-shift shiny). Key comes from
~/GameAssets — never hardcoded, never bundled.
"""
import base64, colorsys, io, json, os, re, time, urllib.request

HOME = os.path.expanduser("~")

STYLE = ("16-bit GBA Pokemon FireRed battle-sprite style pixel art, chunky pixels, "
         "dark outlines, limited palette of deep jewel tones (never pastel or neon), "
         "full body, single creature, centered, plain solid pure green background "
         "(#00ff00) filling the whole frame, no text, no watermark, no border")


def load_key():
    for p in (f"{HOME}/GameAssets/.env", f"{HOME}/GameAssets/GameAssets.env"):
        if os.path.exists(p):
            for line in open(p):
                if line.strip().startswith("GEMINI_API_KEY="):
                    return line.strip().split("=", 1)[1].strip().strip('"')
    return None


def gen(parts, key=None, tries=3):
    """Call Nano Banana with a list of content parts; return raw image bytes."""
    key = key or load_key()
    if not key:
        raise RuntimeError("no GEMINI_API_KEY in ~/GameAssets")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "gemini-2.5-flash-image:generateContent?key=" + key)
    body = json.dumps({"contents": [{"parts": parts}]}).encode()
    last = None
    for t in range(tries):
        try:
            req = urllib.request.Request(url, data=body,
                                         headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
            for c in resp.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    if "inlineData" in p:
                        return base64.b64decode(p["inlineData"]["data"])
            last = "no image part in response"
        except Exception as e:
            last = str(e)[:160]
        time.sleep(4 * (t + 1))
    raise RuntimeError("generation failed: %s" % last)


# ── local, $0 post-processing ───────────────────────────────────────────────
from PIL import Image


def chroma_key(im, tol=70):
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    bg = max(set(c[:3] for c in corners), key=[c[:3] for c in corners].count)
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) < tol and g > r and g > b:
                px[x, y] = (0, 0, 0, 0)
    return im


def to_sprite(raw):
    """Raw model output -> 64x64 transparent, bottom-aligned, quantized sprite."""
    im = chroma_key(Image.open(io.BytesIO(raw)))
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
                hh, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
                r2, g2, b2 = colorsys.hls_to_rgb((hh + dh) % 1, l, s)
                px[x, y] = (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)
    return out


def slugify(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def make_species_art(brief, outdir, project="pokemon-emerald-evolved", sync_library=True):
    """Generate front + back + shinies for one species. Returns #API calls made."""
    import shutil
    os.makedirs(outdir, exist_ok=True)
    key = load_key()
    calls = 0

    raw_front = gen([{"text": f"{brief} {STYLE}. Front-facing battle pose (facing the viewer)."}], key)
    calls += 1
    front = to_sprite(raw_front)
    front.save(os.path.join(outdir, "front.png"))
    Image.open(io.BytesIO(raw_front)).save(os.path.join(outdir, "front-master.png"))

    try:
        raw_back = gen([
            {"inlineData": {"mimeType": "image/png",
                            "data": base64.b64encode(raw_front).decode()}},
            {"text": "Same exact creature, same palette and pixel-art style, but seen FROM "
                     "BEHIND (back battle sprite as in GBA Pokemon battles, slightly larger "
                     "crop). " + STYLE}], key)
        calls += 1
        to_sprite(raw_back).save(os.path.join(outdir, "back.png"))
        Image.open(io.BytesIO(raw_back)).save(os.path.join(outdir, "back-master.png"))
    except Exception as e:
        print("  back sprite failed (front kept):", str(e)[:120])

    hue_shift(front).save(os.path.join(outdir, "shiny.png"))
    back_p = os.path.join(outdir, "back.png")
    if os.path.exists(back_p):
        hue_shift(Image.open(back_p)).save(os.path.join(outdir, "back-shiny.png"))

    if sync_library:
        lib = os.path.join(HOME, "GameAssets", "library", "sprites")
        os.makedirs(lib, exist_ok=True)
        slug = os.path.basename(outdir.rstrip("/"))
        for k in ("front", "back"):
            src = os.path.join(outdir, f"{k}-master.png")
            if os.path.exists(src):
                shutil.copy(src, os.path.join(
                    lib, f"{project}__sprites__{slug}-{k}__v01.png"))
    return calls
