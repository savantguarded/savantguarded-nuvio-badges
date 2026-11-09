"""Build the 'solid' variant of the badge pack (kingsizew solid style).

Keeps the filters, ids and patterns of public/badges.json untouched, and takes
imageURL + tagStyle + tagColor + borderColor + textColor from kingsizew's
solid_badges_v2.json (matched by pattern). Images are black on transparent, resized to
80 px tall, written to public/img/solid-*.png (covered by the immutable cache header).

usage: python3 -I scripts/build-solid-pack.py <kingsizew/badges checkout> [base url]
"""
import io, json, os, sys
from PIL import Image

TARGET_H = 80  # same as the main pack
ks = sys.argv[1].rstrip("/")
base = (sys.argv[2] if len(sys.argv) > 2 else "https://savantguarded-nuvio-badges.vercel.app").rstrip("/")
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_dir = os.path.join(root, "public")
os.makedirs(os.path.join(out_dir, "img"), exist_ok=True)

mine = json.load(open(os.path.join(out_dir, "badges.json"), encoding="utf-8"))
solid = json.load(open(os.path.join(ks, "solid_badges_v2.json"), encoding="utf-8"))
by_pattern = {f["pattern"]: f for f in solid["filters"]}

total_before = total_after = 0
for f in mine["filters"]:
    s = by_pattern.get(f["pattern"])
    if s is None:
        sys.exit(f"no solid match for {f['id']} ({f['name']})")
    rel = s["imageURL"].split("/badge-images/", 1)[1].split("?", 1)[0]  # e.g. audio/dts-black.png
    raw = open(os.path.join(ks, "badge-images", rel), "rb").read()
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    if im.height > TARGET_H:
        im = im.resize((max(1, round(im.width * TARGET_H / im.height)), TARGET_H), Image.LANCZOS)
    name = "solid-" + rel.replace("/", "-").replace("-black", "")
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    open(os.path.join(out_dir, "img", name), "wb").write(buf.getvalue())
    total_before += len(raw); total_after += len(buf.getvalue())
    f["imageURL"] = f"{base}/img/{name}"
    for k in ("tagStyle", "tagColor", "borderColor", "textColor"):
        f[k] = s[k]

json.dump(mine, open(os.path.join(out_dir, "badges-solid.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"{len(mine['filters'])} filters, images {total_before/1024:.0f} KB -> {total_after/1024:.0f} KB")
