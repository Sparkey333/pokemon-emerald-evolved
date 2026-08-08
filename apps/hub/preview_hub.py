#!/usr/bin/env python3
"""Render apps/hub/index.html at several device sizes and check it for overflow.

The failure mode this catches is the one that actually ruins a page on a phone:
some element (a wide table, a nav row, a fixed-width card) sets a floor on the
page width, so the whole body scrolls sideways and text gets clipped off the
right edge. Eyeballing a screenshot is unreliable for this — a page can look
fine down the left column while being 60px too wide — so each viewport is
measured in the browser instead.

For every preset this reports:
    scrollWidth vs clientWidth   -> horizontal page scroll (must be equal)
    any element wider than the viewport, by CSS selector

Usage:
    python3 apps/hub/preview_hub.py                 # check all presets
    python3 apps/hub/preview_hub.py --shots         # also write PNGs
    python3 apps/hub/preview_hub.py --tab species   # focus one tab
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / "apps" / "hub" / "index.html"

# width, height, label
DEVICES = [
    (320, 568, "iPhone SE (1st gen) — narrowest realistic"),
    (390, 844, "iPhone 14 / 15"),
    (414, 896, "iPhone 11 Pro Max"),
    (360, 800, "Android (Pixel-class)"),
    (768, 1024, "iPad portrait"),
    (1200, 900, "desktop"),
]

# A harness page that loads the hub in a fixed-width iframe and measures inside
# it. Chrome's --window-size does NOT affect the viewport used by --dump-dom
# (every size reported the same ~500px width), so measuring the top-level
# document silently produced identical results for every device. An iframe has
# a viewport width we control exactly, and media queries inside it evaluate
# against that width, so this measures what a phone would really render.
HARNESS = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{margin:0;padding:0}iframe{border:0;display:block}
</style></head><body>
<iframe id="f" src="__SRC__" width="__W__" height="__H__"></iframe>
<div id="__probe" style="display:none"></div>
<script>
(function(){
  function sel(el){
    if(!el) return '?';
    var s = el.tagName.toLowerCase();
    if(el.id) return s + '#' + el.id;
    if(el.className && typeof el.className === 'string'){
      var c = el.className.trim().split(/\\s+/).slice(0,2).join('.');
      if(c) s += '.' + c;
    }
    return s;
  }
  function run(){
    var f = document.getElementById('f');
    var d = f.contentDocument, de = d.documentElement;
    var vw = de.clientWidth;
    var wide = [];
    var all = d.querySelectorAll('body *');
    for (var i = 0; i < all.length; i++){
      var el = all[i];
      if (el.offsetParent === null && el.tagName !== 'NAV') continue;
      var r = el.getBoundingClientRect();
      if (r.width > vw + 1 || r.right > vw + 1){
        // Sitting inside a scroll container is the fix, not the bug: the nav
        // strip and table wrappers are meant to scroll their own content, so
        // walk up and ignore anything already contained by one.
        var contained = false;
        for (var p = el; p && p !== d.body; p = p.parentElement){
          var ov = f.contentWindow.getComputedStyle(p).overflowX;
          if (ov === 'auto' || ov === 'scroll'){ contained = true; break; }
        }
        if (contained) continue;
        wide.push({sel: sel(el), w: Math.round(r.width), right: Math.round(r.right)});
      }
    }
    document.getElementById('__probe').textContent = JSON.stringify({
      scrollWidth: de.scrollWidth, clientWidth: vw,
      overflow: de.scrollWidth - vw, wide: wide.slice(0, 8)
    });
  }
  var f = document.getElementById('f');
  if (f.contentDocument && f.contentDocument.readyState === 'complete') setTimeout(run, 50);
  else f.addEventListener('load', function(){ setTimeout(run, 50); });
})();
</script></body></html>
"""



def find_chrome() -> str:
    for c in ("/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
              "/opt/pw-browsers/chromium/chrome-linux/chrome"):
        if Path(c).exists():
            return c
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    hits = list(Path("/opt/pw-browsers").glob("chromium*/chrome-linux/chrome"))
    if hits:
        return str(hits[0])
    sys.exit("error: no chromium binary found")


def probe(chrome: str, tmp: Path, w: int, h: int, tab: str) -> dict:
    """Measure the hub as rendered in a `w`-wide iframe."""
    harness = (HARNESS
               .replace("__SRC__", f"file://{HUB}#{tab}")
               .replace("__W__", str(w))
               .replace("__H__", str(h)))
    page = tmp / f"harness-{w}x{h}.html"
    page.write_text(harness, encoding="utf-8")

    cmd = [chrome, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
           # Same-origin access to the iframe's document is required to measure
           # inside it, and file:// documents are opaque origins without this.
           "--allow-file-access-from-files",
           f"--window-size={max(w, 1000)},{h}", "--virtual-time-budget=4000",
           "--dump-dom", f"file://{page}"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=90).stdout
    m = re.search(r'id="__probe"[^>]*>(\{.*?\})</div>', out, re.S)
    if not m:
        return {}
    return json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))


def shoot(chrome: str, tmp: Path, outdir: Path, w: int, tab: str, tall: int = 1600) -> Path:
    """Screenshot the hub as it renders at a true `w`-wide viewport.

    Screenshotting the page directly does NOT work: Chrome lays it out at its
    own default width (~500px) and then crops the image to --window-size, which
    silently produces a picture of a 500px layout with the right side chopped
    off. It looks exactly like a responsive bug that isn't there. Rendering
    inside a width-pinned iframe gives a genuine viewport, and cropping the
    outer page just past the iframe captures all of it.
    """
    harness = (HARNESS
               .replace("__SRC__", f"file://{HUB}#{tab}")
               .replace("__W__", str(w))
               .replace("__H__", str(tall)))
    page = tmp / f"shot-{w}.html"
    page.write_text(harness, encoding="utf-8")

    shot = outdir / f"hub-{tab}-{w}w.png"
    subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                    "--hide-scrollbars", "--allow-file-access-from-files",
                    # A little wider than the iframe so the full frame is inside
                    # the crop, whatever width Chrome decides to lay out at.
                    f"--window-size={w + 12},{tall}",
                    "--force-device-scale-factor=1", "--virtual-time-budget=4000",
                    f"--screenshot={shot}", f"file://{page}"],
                   capture_output=True, timeout=90)
    return shot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", action="store_true", help="also write PNG screenshots")
    ap.add_argument("--tab", default="home", help="tab hash to load (default: home)")
    ap.add_argument("--outdir", default=None, help="where to write screenshots")
    args = ap.parse_args()

    if not HUB.exists():
        sys.exit("error: apps/hub/index.html missing — run build_hub.py first")

    chrome = find_chrome()

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        outdir = Path(args.outdir) if args.outdir else tmp
        if args.shots:
            outdir.mkdir(parents=True, exist_ok=True)

        print(f"tab: #{args.tab}\n")
        print(f"{'viewport':<12}{'device':<34}{'page w':>9}{'overflow':>10}  result")
        failures = 0
        for w, h, label in DEVICES:
            r = probe(chrome, tmp, w, h, args.tab)
            if not r:
                print(f"{f'{w}x{h}':<12}{label:<34}{'?':>9}{'?':>10}  PROBE FAILED")
                failures += 1
                continue
            over = r["overflow"]
            ok = over <= 0
            status = "ok" if ok else f"OVERFLOW +{over}px"
            if not ok:
                failures += 1
            print(f"{f'{w}x{h}':<12}{label:<34}{r['scrollWidth']:>9}{over:>10}  {status}")
            for el in r.get("wide", []):
                print(f"{'':>12}  -> {el['sel']} is {el['w']}px (right edge {el['right']})")

            if args.shots:
                shoot(chrome, tmp, outdir, w, args.tab)

        print()
        if failures:
            print(f"FAIL — {failures} viewport(s) with horizontal overflow")
        else:
            print("PASS — no horizontal page scroll at any viewport")
        if args.shots:
            print(f"screenshots: {outdir}")
        return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
