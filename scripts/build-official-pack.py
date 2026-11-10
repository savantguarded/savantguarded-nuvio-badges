"""Build a Nuvio Official pack: the mono pack with the official Nuvio badge icons swapped in.

The official Nuvio badge generator (nuvio-badges.skoruppa.workers.dev) offers palettes such
as colorful, neon, stealth and gold; they share icons and differ only in colours. Output:
public/badges-nuvio-official-<palette>.json, images img/nuvio-<palette>-v1-*.png.

Starts from public/badges-mono.json (same filters, ids and order, minus the combos below). For every
filter the skoruppa pack also covers, the image is replaced with skoruppa's icon (white
glyph, rendered from its SVG to an 80 px PNG) and the chip takes that palette's fill, border and text colours.
Filters the official pack has no icon for (576p, 360p, HDRip, SCR, DTS-ES and the edition
tags) get text badges drawn the same way the official ones are: Roboto 700 glyph paths on a
14-unit-tall canvas, cap height 6.41, baseline 10.5, about 4 units of side padding, in the
palette's glyph colour, with the chip colours of the closest official badge (LEFTOVER below).
The DV / Atmos / DTS:X combo badges are removed; their single badges show side by side
instead (e.g. Dolby Vision + HDR10). Groups are ordered Resolution, Visual, Audio, Source,
IMAX, Special.

Source pack (save it first, <palette> = colorful / neon / stealth / gold):
  https://nuvio-badges.skoruppa.workers.dev/v1/badge.json?l=en&c=source&g=res,src,hdr,aud,ch,spc&x=p-61&s=filled&b=1&p=<palette>

usage: python3 -I scripts/build-official-pack.py <palette> <saved badge.json> <roboto 700 font>
needs: rsvg-convert, fontTools; font: npm pack @fontsource/roboto@5 ->
  files/roboto-latin-700-normal.woff
"""
import base64, json, os, subprocess, sys, tempfile

BASE_URL = "https://savantguarded-nuvio-badges.vercel.app/img/"
HEIGHT = 80
MAX_W = 460

# mono filter id -> skoruppa filter id
MAP = {
    "r-4k": "p-4k", "r-1440p": "p-1440p", "r-1080": "p-1080p", "r-720": "p-720p", "r-480p": "p-480p",
    "q-r": "p-remux", "q-b": "p-bluray", "q-w": "p-webdl", "src-webrip": "p-webrip",
    "src-dvdrip": "p-dvdrip", "src-hdtv": "p-hdtv",
    "a-dv": "p-dv", "v-hdr10p": "p-hdr10p", "v-hdr10": "p-hdr10", "v-hdr": "p-hdr", "v-hlg": "p-hlg",
    "a-at": "p-atmos", "a-th": "p-truehd", "a-dp": "p-ddp", "a-dd": "p-dd", "a-dtsx": "p-dtsx",
    "a-dtsma": "p-dtshdma", "a-dtshd": "p-dtshd", "a-dts": "p-dts", "a-flac": "p-flac",
    "v-imax-e-2": "p-imax-e", "v-imax-2": "p-imax",
    "seadex-release": "p-seadex",
}

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pub = os.path.join(root, "public")
img_dir = os.path.join(pub, "img")

palette = sys.argv[1]
PREFIX = f"nuvio-{palette}-v1-"
OUT = f"badges-nuvio-official-{palette}.json"
sk = {f["id"]: f for f in json.load(open(sys.argv[2], encoding="utf-8"))["filters"]}
pack = json.load(open(os.path.join(pub, "badges-mono.json"), encoding="utf-8"))

done = 0
with tempfile.TemporaryDirectory() as tmp:
    for f in pack["filters"]:
        sid = MAP.get(f["id"])
        if sid is None:
            continue
        s = sk.get(sid)
        if s is None:
            sys.exit(f"skoruppa pack has no {sid}")
        head, data = s["imageURL"].split(",", 1)
        svg = os.path.join(tmp, sid + ".svg")
        open(svg, "wb").write(base64.b64decode(data))
        name = PREFIX + sid[2:] + ".png"
        out = os.path.join(img_dir, name)
        subprocess.run(["rsvg-convert", "-h", str(HEIGHT), "-o", out, svg], check=True)
        w = int.from_bytes(open(out, "rb").read()[16:20], "big")
        if w > MAX_W:
            sys.exit(f"{name} is {w}px wide (max {MAX_W})")
        f["imageURL"] = BASE_URL + name
        for k in ("tagStyle", "tagColor", "borderColor", "textColor"):
            f[k] = s[k]
        done += 1

# Combos are dropped: their single badges show back to back instead. Each single filter hides
# itself when a combo would match; only those combo-driven exclusions are lifted, every other
# rule (HDR10+ over HDR10, TrueHD over DD+, the FLAC / DTS rules...) stays as it was.
def mk(bits):
    return "⁣" + "".join("‌" if b == "0" else "‍" for b in bits) + "⁤"

DV, P, H10, H = mk("00000001"), mk("00000010"), mk("00000011"), mk("00000100")
AT, TH, DP = mk("00001001"), mk("00010001"), mk("00001010")
X, MA, HD = mk("00001100"), mk("00001101"), mk("00001110")

COMBOS = ["v-dv-hdr10p", "v-dv-hdr10", "v-dv-hdr", "a-atmos-truehd", "a-atmos-ddplus", "a-dtsx-hdma", "a-dtsx-hd"]
LIFT = {
    "a-dv": [P, H10, H], "v-hdr10p": [DV], "v-hdr10": [DV], "v-hdr": [DV],
    "a-at": [TH, DP], "a-th": [AT], "a-dp": [AT],
    "a-dtsx": [MA, HD], "a-dtsma": [X], "a-dtshd": [X],
}

def lift(pattern, drop):
    # the first exclusion group after the positive lookahead: (?!.*(?:A|B|C))
    start = pattern.index("(?!.*(?:")
    end = pattern.index("))", start) + 2
    alts = [a for a in pattern[start + 8:end - 2].split("|") if a not in drop]
    if len(alts) == len(pattern[start + 8:end - 2].split("|")):
        sys.exit("nothing lifted")
    group = "(?!.*(?:" + "|".join(alts) + "))" if alts else ""
    return pattern[:start] + group + pattern[end:]

pack["filters"] = [f for f in pack["filters"] if f["id"] not in COMBOS]
for f in pack["filters"]:
    if f["id"] in LIFT:
        f["pattern"] = lift(f["pattern"], LIFT[f["id"]])
# The old Atmos DD+ and DTS:X HD combos ignored the multi-track FLAC rule, so the half that
# used to sit inside the combo skips that rule too when its partner is present.
SKIP = {"a-dp": AT, "a-dtshd": X}
for f in pack["filters"]:
    if f["id"] in SKIP:
        if f["pattern"].count("(?!(?=.*") != 1:
            sys.exit(f"unexpected FLAC rule in {f['id']}")
        f["pattern"] = f["pattern"].replace("(?!(?=.*", "(?!(?!.*" + SKIP[f["id"]] + ")(?=.*")

# Text badges for the filters the official pack has no icon for:
# mono id -> (label, official filter whose chip colours it borrows, borrow that filter's icon)
LEFTOVER = {
    "r-576p": ("576p", "p-480p", False), "r-360p": ("360p", "p-480p", False),
    "src-hdrip": ("HDRip", "p-webrip", True), "gq-scr": ("SCR", "p-cam", False),
    "gv-dts-es": ("DTS-ES", "p-dts", False),
    "open-matte-edition": ("Open Matte", "p-hdtv", False),
    "regraded-release": ("Regraded", "p-hdtv", False),
    "edition-directors-cut": ("Director\u2019s Cut", "p-hdtv", False),
    "edition-extended": ("Extended", "p-hdtv", False),
    "uncut-edition": ("Uncut", "p-hdtv", False),
    "uncensored-edition": ("Uncensored", "p-hdtv", False),
    "black-and-white": ("B&W", "p-hdtv", False),
    "true-hue-edition": ("True-Hue", "p-hdtv", False),
    "edition-theatrical": ("Theatrical", "p-hdtv", False),
}
import re
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
import math

font = TTFont(sys.argv[3])
gs, cmap = font.getGlyphSet(), font.getBestCmap()
SCALE = 6.41 / font["OS/2"].sCapHeight
BASE = 10.5

def svg_of(sid):
    return base64.b64decode(sk[sid]["imageURL"].split(",", 1)[1]).decode()

glyph_fill = re.search(r'fill="([^"]+)"', svg_of("p-hdr")).group(1)

def text_badge(label, icon_from):
    # Official layout: pen starts at x=4 (x=17 after a 10-unit icon), canvas width is the
    # text advance + 7 rounded up to an even number. Reproduces every official badge width.
    icon = ""
    x = 4.0
    if icon_from:
        icon = re.search(r"<g transform=\"translate\(4, 2\)\">.*?</g>", svg_of(icon_from), re.S).group(0)
        x = 17.0
    pen = SVGPathPen(gs)
    for ch in label:
        g = cmap[ord(ch)]
        gs[g].draw(TransformPen(pen, (SCALE, 0, 0, -SCALE, x, BASE)))
        x += gs[g].width * SCALE
    width = 2 * math.ceil((x + 3) / 2)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="14" viewBox="0 0 {width} 14">'
            f'{icon}<path d="{pen.getCommands()}" fill="{glyph_fill}"/></svg>')

with tempfile.TemporaryDirectory() as tmp:
    for f in pack["filters"]:
        if f["id"] not in LEFTOVER:
            continue
        label, colour_from, use_icon = LEFTOVER[f["id"]]
        svg = os.path.join(tmp, "t.svg")
        open(svg, "w").write(text_badge(label, colour_from if use_icon else None))
        name = PREFIX + "x-" + f["id"] + ".png"
        out = os.path.join(img_dir, name)
        subprocess.run(["rsvg-convert", "-h", str(HEIGHT), "-o", out, svg], check=True)
        w = int.from_bytes(open(out, "rb").read()[16:20], "big")
        if w > MAX_W:
            sys.exit(f"{name} is {w}px wide (max {MAX_W})")
        f["imageURL"] = BASE_URL + name
        for k in ("tagStyle", "tagColor", "borderColor", "textColor"):
            f[k] = sk[colour_from][k]
        done += 1

ORDER = ["gr", "gv", "ga", "gq", "imax", "gst"]
pack["groups"].sort(key=lambda g: ORDER.index(g["id"]))
pack["filters"].sort(key=lambda f: ORDER.index(f["groupId"]))  # stable: keeps order within groups

json.dump(pack, open(os.path.join(pub, OUT), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"{done} of {len(pack['filters'])} filters restyled -> public/{OUT}")
