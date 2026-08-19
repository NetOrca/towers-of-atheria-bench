#!/usr/bin/env python3
"""
Towers of Atheria - PLACEHOLDER sprite generator.

BASELINE, not final art. The point is to establish the slot, the loader and
the sizing NOW, so real hand-drawn 32x32 sprites drop into exactly the same
place later and nothing in the layout shifts. That is what stops visual drift
between this bench and the finished game.

Each card gets an ARCHETYPE silhouette tinted by its Dweller Type. Procedural
art cannot produce "a white rabbit with a red eye" - it can produce a readable
beast shape in forest green, which is enough to feel the game.

    python3 build_sprites.py   ->  injects <script id="sprites"> into index.html

REPLACING WITH REAL ART: drop 32x32 PNGs named <card id>.png into a sprites/
folder next to this script. Any file found there wins over the generated shape,
so you can replace them one at a time without touching code.
"""
import base64, io, json, os, re, sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow required:  pip install pillow")

HERE = os.path.dirname(os.path.abspath(__file__))
PX = 32
HAND_DRAWN = os.path.join(HERE, "sprites")

PAL = {
    "dungeon": {"main": (198, 200, 192), "dark": (88, 92, 100),  "accent": (122, 204, 192)},
    "lava":    {"main": (234, 140, 62),  "dark": (104, 42, 28),  "accent": (255, 216, 96)},
    "honor":   {"main": (240, 234, 212), "dark": (138, 120, 64), "accent": (242, 210, 98)},
    "forest":  {"main": (128, 178, 98),  "dark": (56, 80, 44),   "accent": (208, 178, 96)},
}

# ---------------------------------------------------------------- archetype
BEAST = ("hound", "rat", "rodent", "bat", "skink", "wolf", "bear", "tiger",
         "stalker", "caiman", "rabbit", "fox", "buck", "doe", "squirrel",
         "mare", "dog", "jack rabbit", "drake", "gargoyle", "lavagoyle")
FLIER = ("bat", "wisp", "drake", "dancer", "wraith")
UNDEAD = ("skeleton", "skeletal", "zombie", "ghoul", "wraith", "bone", "lich",
          "undead", "corpse", "charnel", "ossuary", "sepulcher", "crypt")
STRUCTURE = ("wall", "tower", "cave", "door", "grave", "maple", "bog", "field",
             "ashlands", "spire", "minefield", "pyre", "watchtower")
SIEGE = ("catapult", "ballista", "mine")

def archetype(c):
    n = c["name"].lower()
    if c["tier"] == 4:                       return "boss"
    if any(k in n for k in SIEGE):           return "siege"
    if any(k in n for k in STRUCTURE) or not c["movable"]: return "structure"
    if any(k in n for k in FLIER):           return "flier"
    if any(k in n for k in UNDEAD):          return "undead"
    if any(k in n for k in BEAST):           return "beast"
    return "humanoid"

# ------------------------------------------------------------------ shapes
def sprite(kind, dweller, ranged):
    p = PAL.get(dweller, PAL["dungeon"])
    im = Image.new("RGBA", (PX, PX), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    M, K, A = p["main"], p["dark"], p["accent"]

    if kind == "humanoid":
        d.rectangle([13, 5, 18, 11], fill=M)            # head
        d.rectangle([11, 12, 20, 24], fill=M)           # torso
        d.rectangle([11, 12, 20, 15], fill=K)           # shoulders
        d.rectangle([12, 25, 14, 30], fill=K)           # legs
        d.rectangle([17, 25, 19, 30], fill=K)
        if ranged: d.line([22, 8, 22, 22], fill=A, width=2)      # bow stave
        else:      d.line([22, 6, 22, 20], fill=A, width=2)      # blade

    elif kind == "beast":
        d.ellipse([7, 14, 25, 25], fill=M)              # body
        d.ellipse([20, 10, 28, 18], fill=M)             # head
        d.rectangle([9, 24, 11, 29], fill=K)            # legs
        d.rectangle([14, 24, 16, 29], fill=K)
        d.rectangle([20, 24, 22, 29], fill=K)
        d.line([7, 16, 3, 11], fill=K, width=2)         # tail
        d.point((25, 13), fill=A)                       # eye

    elif kind == "flier":
        d.ellipse([13, 13, 19, 21], fill=M)             # body
        d.polygon([(13, 15), (3, 9), (5, 19)], fill=K)  # wings
        d.polygon([(19, 15), (29, 9), (27, 19)], fill=K)
        d.point((15, 16), fill=A); d.point((17, 16), fill=A)

    elif kind == "undead":
        d.rectangle([13, 5, 18, 11], fill=M)
        d.point((14, 8), fill=(20, 20, 20)); d.point((17, 8), fill=(20, 20, 20))
        for y in (14, 17, 20, 23):                       # ribs
            d.line([12, y, 19, y], fill=M, width=1)
        d.line([15, 13, 15, 24], fill=K, width=2)        # spine
        d.rectangle([12, 25, 14, 30], fill=M)
        d.rectangle([17, 25, 19, 30], fill=M)
        if ranged: d.line([23, 9, 23, 23], fill=A, width=2)

    elif kind == "structure":
        d.rectangle([5, 12, 26, 30], fill=K)
        for x in range(6, 26, 5):                        # blocks
            d.line([x, 12, x, 30], fill=M, width=1)
        d.line([5, 18, 26, 18], fill=M, width=1)
        d.line([5, 24, 26, 24], fill=M, width=1)
        d.polygon([(5, 12), (15, 5), (26, 12)], fill=M)  # cap
        d.rectangle([13, 22, 18, 30], fill=A)            # opening

    elif kind == "siege":
        d.rectangle([6, 20, 26, 24], fill=K)             # frame
        d.ellipse([7, 23, 13, 29], fill=M)               # wheels
        d.ellipse([19, 23, 25, 29], fill=M)
        d.line([10, 20, 22, 7], fill=M, width=3)         # arm
        d.ellipse([20, 4, 26, 10], fill=A)               # payload

    else:  # boss
        d.polygon([(16, 2), (23, 9), (16, 13), (9, 9)], fill=A)   # crown
        d.rectangle([12, 12, 20, 16], fill=M)                     # head
        d.rectangle([9, 17, 23, 27], fill=M)                      # body
        d.rectangle([9, 17, 23, 20], fill=K)                      # pauldrons
        d.polygon([(9, 19), (3, 15), (5, 25)], fill=K)            # mantle
        d.polygon([(23, 19), (29, 15), (27, 25)], fill=K)
        d.rectangle([11, 28, 14, 31], fill=K)
        d.rectangle([18, 28, 21, 31], fill=K)

    return im

def png_b64(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()

# -------------------------------------------------------------------- main
def main():
    cards = json.load(open(os.path.join(HERE, "toa_catalog.json"), encoding="utf-8"))
    out, cache, hand_used, counts = {}, {}, 0, {}

    for c in cards:
        real = os.path.join(HAND_DRAWN, c["id"] + ".png")
        if os.path.exists(real):
            out[c["id"]] = png_b64(Image.open(real).convert("RGBA").resize((PX, PX), Image.NEAREST))
            hand_used += 1
            continue
        kind = archetype(c)
        counts[kind] = counts.get(kind, 0) + 1
        key = (kind, c["dweller"], c["attack"] == "ranged")
        if key not in cache:
            cache[key] = png_b64(sprite(*key))
        out[c["id"]] = cache[key]

    for k in sorted(counts):
        print(f"  {k:<10} {counts[k]:>3} cards")
    if hand_used:
        print(f"  hand-drawn overrides used: {hand_used}")

    payload = ('<script id="sprites">/* GENERATED by build_sprites.py - do not edit */\n'
               "window.TOA_SPRITES=" + json.dumps(out, separators=(",", ":")) + ";\n</script>")
    idx = os.path.join(HERE, "index.html")
    html = open(idx, encoding="utf-8").read()
    new, n = re.subn(r'<script id="sprites">.*?</script>', payload, html, flags=re.S)
    if not n:
        sys.exit('index.html has no <script id="sprites"> marker')
    open(idx, "w", encoding="utf-8").write(new)
    print(f"\n  {len(out)} sprites mapped from {len(cache)} unique shapes"
          f"  ({len(payload)//1024} KB inline)")

if __name__ == "__main__":
    main()
