"""Build the 'tiered' filled pack (variant B2): quiet suffix after a hairline + greyscale tiers.

Same 49 filters, patterns and groups as public/badges.json. Images are 80 px tall
(16 dp slot), text baked in; Nuvio draws the chip fill per filter:
hero #F6F6F6, core #DCDCDC, quiet #8E8E8E, warn #141416 with a light outline.

Uses scripts/lib/variants.py (Geist + layout rules); fonts and icons in .work/, see README.
usage: python3 -I scripts/build-tiered-pack.py
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))
from variants import badge, S, GROUP_ORDER

repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pub = os.path.join(repo, 'public')
BASE = 'https://savantguarded-nuvio-badges.vercel.app/img/'
P = 5
hexc = lambda c: '#%02X%02X%02X' % c

pack = json.load(open(os.path.join(pub, 'badges.json'), encoding='utf-8'))
# B2: visual straight after resolution (Nuvio shows badges in pack order)
pos = {f['id']: i for i, f in enumerate(pack['filters'])}
pack['filters'].sort(key=lambda f: (GROUP_ORDER.index(f['groupId']), pos[f['id']]))
pack['groups'].sort(key=lambda g: GROUP_ORDER.index(g['id']))
widest = 0
for f in pack['filters']:
    im, fill, border, tier = badge(f['id'], 'B2', P)
    w = im.width / P; widest = max(widest, w)
    assert w <= 92, (f['id'], w)
    name = f"tiered-v2-{f['id']}.png"
    im.save(os.path.join(pub, 'img', name), optimize=True)
    f['imageURL'] = BASE + name
    f['tagStyle'] = 'filled'; f['tagColor'] = hexc(fill)
    f['borderColor'] = hexc(border) if border else hexc(fill)
    f['textColor'] = '#151515' if tier != 'warn' else '#F2F2F2'
json.dump(pack, open(os.path.join(pub, 'badges-tiered.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(len(pack['filters']), 'filters; widest', round(widest, 1), 'dp')
