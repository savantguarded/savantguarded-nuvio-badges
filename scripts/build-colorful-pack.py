"""Build the 'colorful' pack: the mono pack with skoruppa's colourful icons swapped in.

Starts from public/badges-mono.json (same 49 filters, ids, patterns and order). For every
filter the skoruppa pack also covers, the image is replaced with skoruppa's icon (white
glyph, rendered from its SVG to an 80 px PNG) and the chip takes skoruppa's fill colour.
Filters skoruppa has no icon for (576p, 360p, HDRip, SCR, the DV / Atmos / DTS:X combos,
DTS-ES and the edition tags) keep their mono image and white chip.

Source pack (save it first):
  https://nuvio-badges.skoruppa.workers.dev/v1/badge.json?l=en&c=source&g=res,src,hdr,aud,ch,spc&x=p-61&s=filled&b=1&p=colorful

usage: python3 -I scripts/build-colorful-pack.py <skoruppa badge.json>
needs: rsvg-convert
"""
import base64, json, os, subprocess, sys, tempfile

PREFIX = "colorful-v1-"
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

sk = {f["id"]: f for f in json.load(open(sys.argv[1], encoding="utf-8"))["filters"]}
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
        f["tagStyle"] = "filled"
        f["tagColor"] = f["borderColor"] = s["tagColor"]
        f["textColor"] = "#FFFFFF"
        done += 1

json.dump(pack, open(os.path.join(pub, "badges-colorful.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"{done} of {len(pack['filters'])} filters swapped -> public/badges-colorful.json")
