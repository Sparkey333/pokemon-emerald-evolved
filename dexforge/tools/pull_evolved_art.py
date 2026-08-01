#!/usr/bin/env python3
"""Pull Pokemon Evolved artist reveal art into vault/evolved/reveal-art/.

Sources (recon-verified, public APIs, no auth):
  - Bluesky: jordanosart, xiapher, kattenkg  (app.bsky.feed.getAuthorFeed -> cdn.bsky.app)
  - Tumblr:  calicorn's "sprites made for pointcrow's Pokemon Evolved" dump post

These are the artists' OWN design-reveal images (fan art for the hack) — kept as a local
reference vault with per-file attribution in reveal-manifest.json. Do not re-host or ship.
The canonical in-game 64px sprites exist only inside evolutions.ips; extracting those
requires patching your own LeafGreen dump (see README, own-dump doctrine).
"""
import json, os, re, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "vault", "evolved", "reveal-art")
UA = {"User-Agent": "Mozilla/5.0 (personal local reference vault; contact: local)"}

BSKY_ARTISTS = {
    "jordanosart": "did:plc:rtr3pxw7cx6xv5u4ijuxxe35",
    "xiapher": "did:plc:obqyrsxptsw5x4egjlsaw4lo",
    "kattenkg": "did:plc:qpggsvxbeesldvmhdazfkfmi",
}
KEYWORDS = re.compile(r"pokemon|evolved|pointcrow|sprite|line|starter|kanto", re.I)
TUMBLR_POST = "https://calicorn.tumblr.com/api/read/json?id=773847627888525312"

manifest = []

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()

def save(content, artist, key, ext, meta):
    adir = os.path.join(DEST, artist)
    os.makedirs(adir, exist_ok=True)
    name = re.sub(r"[^a-z0-9-]", "", key.lower())[:60] or "img"
    path = os.path.join(adir, f"{name}.{ext}")
    n = 1
    while os.path.exists(path):
        n += 1
        path = os.path.join(adir, f"{name}-{n}.{ext}")
    with open(path, "wb") as f:
        f.write(content)
    manifest.append({"file": os.path.relpath(path, ROOT), "artist": artist, **meta})
    return path

def pull_bsky(handle, did):
    cursor, pulled, pages = "", 0, 0
    while pages < 6:
        q = urllib.parse.urlencode({"actor": did, "limit": 100,
                                    "filter": "posts_with_media", **({"cursor": cursor} if cursor else {})})
        try:
            data = json.loads(get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?{q}"))
        except Exception as e:
            print(f"  ! {handle}: feed fetch failed: {e}")
            return
        for item in data.get("feed", []):
            post = item.get("post", {})
            rec = post.get("record", {})
            text = rec.get("text", "")
            if not KEYWORDS.search(text):
                continue
            images = (post.get("embed", {}) or {}).get("images", []) or []
            uri = post.get("uri", "")
            rkey = uri.rsplit("/", 1)[-1]
            for i, img in enumerate(images):
                full = img.get("fullsize")
                if not full:
                    continue
                try:
                    content = get(full)
                except Exception as e:
                    print(f"  ! {handle}/{rkey}#{i}: {e}")
                    continue
                ext = "png" if "png" in full else "jpg"
                save(content, handle, f"{rkey}-{i}", ext, {
                    "source": f"https://bsky.app/profile/{handle}.bsky.social/post/{rkey}",
                    "text": text[:200], "date": rec.get("createdAt", ""), "alt": img.get("alt", "")})
                pulled += 1
        cursor = data.get("cursor", "")
        pages += 1
        if not cursor:
            break
    print(f"  bsky {handle}: {pulled} images")

def pull_tumblr():
    try:
        raw = get(TUMBLR_POST).decode("utf-8", "replace")
        raw = raw[raw.index("{"): raw.rindex("}") + 1]
        data = json.loads(raw)
    except Exception as e:
        print(f"  ! calicorn tumblr: {e}")
        return
    pulled = 0
    for post in data.get("posts", []):
        body = post.get("regular-body", "") or ""
        caption = re.sub(r"<[^>]+>", " ", post.get("regular-title", "") or "")
        srcs = re.findall(r'<img[^>]+src="([^"]+media\.tumblr\.com[^"]+)"', body)
        photo_keys = [k for k in post if k.startswith("photo-url")]
        if photo_keys:
            srcs += [post[max(photo_keys)]]
        for i, src in enumerate(dict.fromkeys(srcs)):
            try:
                content = get(src)
            except Exception as e:
                print(f"  ! tumblr img: {e}")
                continue
            ext = "png" if ".png" in src else ("gif" if ".gif" in src else "jpg")
            save(content, "calicorn", f"pointcrow-dump-{i}", ext, {
                "source": post.get("url-with-slug", post.get("url", "")),
                "text": (caption or "pokemon evolved sprite dump")[:200],
                "date": post.get("date", "")})
            pulled += 1
    print(f"  tumblr calicorn: {pulled} images")

os.makedirs(DEST, exist_ok=True)
for h, d in BSKY_ARTISTS.items():
    pull_bsky(h, d)
pull_tumblr()
with open(os.path.join(DEST, "reveal-manifest.json"), "w", encoding="utf-8") as f:
    json.dump({"note": "Artist reveal art for Pokemon Evolved (PointCrow commission). "
                       "Local reference only — credit artists, never re-host/ship.",
               "items": manifest}, f, indent=1)
with open(os.path.join(ROOT, "data", "reveal-art.js"), "w", encoding="utf-8") as f:
    f.write("window.REVEAL_ART = ")
    json.dump(manifest, f)
    f.write(";\n")
print(f"total: {len(manifest)} images -> {DEST}")
