"""Build a self-hosted, resized copy of a Nuvio badge pack.

usage: python3 -I build_pack.py <pack.json> <downloads dir with urls.txt + img_N> <out dir> <base url>
"""
import io, json, re, sys, os
from urllib.parse import urlparse
from PIL import Image
import cairosvg

TARGET_H = 80  # Nuvio decodes badges at 64 px tall on a 1080p TV; 80 leaves headroom

src, dl, out, base = sys.argv[1:5]
base = base.rstrip("/")
os.makedirs(os.path.join(out, "img"), exist_ok=True)

urls = [u.strip() for u in open(os.path.join(dl, "urls.txt")) if u.strip()]
mapping, used, report = {}, set(), []
for i, u in enumerate(urls, 1):
    raw = open(os.path.join(dl, f"img_{i}"), "rb").read()
    if raw.lstrip().startswith(b"<?xml") or b"<svg" in raw[:400]:
        raw = cairosvg.svg2png(bytestring=raw, output_height=TARGET_H * 2)
    im = Image.open(io.BytesIO(raw))
    im = im.convert("RGBA")
    w, h = im.size
    if h > TARGET_H:
        im = im.resize((max(1, round(w * TARGET_H / h)), TARGET_H), Image.LANCZOS)
    p = urlparse(u).path
    parts = [x for x in p.split("/") if x]
    stem = re.sub(r"[^a-z0-9]+", "-", "-".join(parts[-2:]).lower().rsplit(".", 1)[0]).strip("-")
    name, n = stem + ".png", 2
    while name in used:
        name, n = f"{stem}-{n}.png", n + 1
    used.add(name)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    open(os.path.join(out, "img", name), "wb").write(buf.getvalue())
    mapping[u] = f"{base}/img/{name}"
    report.append((len(raw), len(buf.getvalue()), (w, h), im.size, name))

text = open(src, encoding="utf-8").read()
data = json.loads(text)
missing = 0
for f in data.get("filters", []):
    u = f.get("imageURL")
    if u:
        if u in mapping:
            f["imageURL"] = mapping[u]
        else:
            missing += 1
json.dump(data, open(os.path.join(out, "badges.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

before = sum(r[0] for r in report); after = sum(r[1] for r in report)
print(f"{len(report)} images, {before/1024:.0f} KB -> {after/1024:.0f} KB, unmapped URLs: {missing}")
for r in sorted(report, key=lambda r: -r[0])[:6]:
    print(f"  {r[4]}: {r[2]} {r[0]//1024} KB -> {r[3]} {r[1]//1024} KB")
