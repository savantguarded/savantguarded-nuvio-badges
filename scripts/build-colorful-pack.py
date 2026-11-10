"""Build the 'colorful' pack: the mono pack with skoruppa's colourful icons swapped in.

Starts from public/badges-mono.json (same filters, ids and order, minus the combos below). For every
filter the skoruppa pack also covers, the image is replaced with skoruppa's icon (white
glyph, rendered from its SVG to an 80 px PNG) and the chip takes skoruppa's fill colour.
Filters skoruppa has no icon for (576p, 360p, HDRip, SCR, DTS-ES and the edition tags) keep
their mono image and white chip. The DV / Atmos / DTS:X combo badges are removed; their
single badges show side by side instead (e.g. Dolby Vision + HDR10).

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

json.dump(pack, open(os.path.join(pub, "badges-colorful.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"{done} of {len(pack['filters'])} filters swapped -> public/badges-colorful.json")
