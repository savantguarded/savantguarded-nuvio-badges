"""Build the 'mono white' variant of the badge pack (kingsizew mono white style).

kingsizew's mono white pack uses the exact same black-on-transparent logos as his solid pack,
only the tag colour differs (white fill instead of tier colours). So this reuses the images
already hosted for the solid pack (same URLs, so Nuvio's disk cache is shared when you swap
between the two) and only takes tagStyle / tagColor / borderColor / textColor from
mono_white_badges_v2.json, matched by pattern.

Run scripts/build-solid-pack.py first.

usage: python3 -I scripts/build-mono-pack.py <kingsizew/badges checkout>
"""
import json, os, sys

ks = sys.argv[1].rstrip("/")
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_dir = os.path.join(root, "public")

solid = json.load(open(os.path.join(out_dir, "badges-solid.json"), encoding="utf-8"))
mono = json.load(open(os.path.join(ks, "mono_white_badges_v2.json"), encoding="utf-8"))
by_pattern = {f["pattern"]: f for f in mono["filters"]}

for f in solid["filters"]:
    m = by_pattern.get(f["pattern"])
    if m is None:
        sys.exit(f"no mono white match for {f['id']} ({f['name']})")
    for k in ("tagStyle", "tagColor", "borderColor", "textColor"):
        f[k] = m[k]

json.dump(solid, open(os.path.join(out_dir, "badges-mono.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"{len(solid['filters'])} filters written to public/badges-mono.json")
