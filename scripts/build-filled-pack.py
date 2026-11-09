"""Filled mono badge set: render 49 badge images + a TV-scale preview sheet (nothing published).

Images: dark Geist SemiBold text on transparent, 80 px tall (= the 16 dp image slot), so Nuvio's
own chip draws the #DCDCDC fill around them. Every label uses the same text height; none is wider
than the 92 dp cap, so Nuvio never shrinks one.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

import sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, '.work')  # fonts, see README
FONT = f'{ROOT}/g/package/dist/fonts/geist-sans/Geist-SemiBold.ttf'
OUT = ROOT
IMG = f'{REPO}/public/img'

FILL = (0xDC, 0xDC, 0xDC); TEXT = (0x15, 0x15, 0x15)
CAP_DP = 7.5          # text cap height (OSD is 6.8 in a 14 dp chip; this keeps the same proportion feel in a 20 dp chip)
SLOT_DP = 16          # image slot height in Nuvio's chip
PAD_DP = 1.0          # baked side padding (chip adds 3 dp -> 4 dp, same as the OSD filled tile)
TRACK_EM = 0.021      # OSD letter spacing 0.2sp at 9.5sp
PX_PER_DP = 5         # 80 px tall images
SS = 4

LABELS = {
 'r-4k':'4K','r-1440p':'1440p','r-1080':'1080p','r-720':'720p','r-576p':'576p','r-480p':'480p','r-360p':'360p',
 'q-r':'REMUX','q-b':'BLURAY','q-w':'WEB-DL','src-webrip':'WEBRIP','src-hdrip':'HDRIP','src-dvdrip':'DVDRIP','src-hdtv':'HDTV','gq-scr':'SCR',
 'a-dv':'DOLBY VISION','v-hdr10p':'HDR10+','v-hdr10':'HDR10','v-hdr':'HDR','v-hlg':'HLG',
 'v-dv-hdr10p':'DV · HDR10+','v-dv-hdr10':'DV · HDR10','v-dv-hdr':'DV · HDR',
 'a-atmos-truehd':'ATMOS · TRUEHD','a-atmos-ddplus':'ATMOS · DD+','a-at':'DOLBY ATMOS',
 'a-dtsx-hdma':'DTS:X · HD MA','a-dtsx-hd':'DTS:X · HD','a-dtsx':'DTS:X','a-th':'TRUEHD','a-dtsma':'DTS-HD MA',
 'a-flac':'FLAC','a-dtshd':'DTS-HD','a-dp':'DD+','gv-dts-es':'DTS-ES','a-dts':'DTS','a-dd':'DD',
 'v-imax-e-2':'IMAX ENHANCED','v-imax-2':'IMAX',
 'seadex-release':'SEADEX','open-matte-edition':'OPEN MATTE','regraded-release':'REGRADED','edition-directors-cut':"DIRECTOR'S CUT",
 'edition-extended':'EXTENDED','uncut-edition':'UNCUT','uncensored-edition':'UNCENSORED','black-and-white':'BLACK & WHITE',
 'true-hue-edition':'TRUE-HUE','edition-theatrical':'THEATRICAL',
}

def font_for(cap_px):
    f = ImageFont.truetype(FONT, 100)
    l, t, r, b = f.getbbox('H')
    return ImageFont.truetype(FONT, round(100 * cap_px / (b - t)))

def text_image(label, color, px_per_dp, ss=SS, min_dp=34):
    """Text centred on its capitals in a SLOT_DP-tall transparent image."""
    s = px_per_dp * ss
    f = font_for(CAP_DP * s)
    track = TRACK_EM * f.size
    widths = [f.getlength(ch) for ch in label]
    tw = sum(widths) + track * (len(label) - 1)
    pad = PAD_DP * s
    W, H = int(round(max(tw + 2 * pad, min_dp * s))), int(SLOT_DP * s)
    W += (ss - W % ss) % ss
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    l, t, r, b = f.getbbox('H')
    y = (H - (b - t)) / 2 - t
    x = (W - tw) / 2
    for ch, w in zip(label, widths):
        d.text((x, y), ch, font=f, fill=color + (255,)); x += w + track
    return im.resize((W // ss, H // ss), Image.LANCZOS)

def slug(label):
    return ''.join(c if c.isalnum() else '-' for c in label.lower()).strip('-').replace('--', '-')

pack = json.load(open(f'{REPO}/public/badges.json', encoding='utf-8'))
ids = [f['id'] for f in pack['filters']]
missing = set(ids) - set(LABELS); assert not missing, missing
def group_min(gid):
    # resolution chips all share the widest resolution's width, so the group reads as one set
    if gid != 'gr': return 34
    return max(text_image(LABELS[f['id']], TEXT, PX_PER_DP).width for f in pack['filters'] if f['groupId'] == 'gr') / PX_PER_DP
rows = []
for f in pack['filters']:
    lab = LABELS[f['id']]
    im = text_image(lab, TEXT, PX_PER_DP, min_dp=group_min(f['groupId']))
    wdp = im.width / PX_PER_DP
    assert wdp <= 92, (lab, wdp)
    im.save(f"{IMG}/filled-v1-{f['id']}.png", optimize=True)
    rows.append((f['groupId'], lab, wdp, group_min(f['groupId'])))
print(len(rows), 'images; widest', max(rows, key=lambda r: r[2]))
print('tile tier (<34 dp -> 40 dp chips):', [r[1] for r in rows if r[2] < 34])

BASE = 'https://savantguarded-nuvio-badges.vercel.app/img/'
for f in pack['filters']:
    f['imageURL'] = f"{BASE}filled-v1-{f['id']}.png"
    f['tagStyle'] = 'filled'; f['tagColor'] = '#DCDCDC'; f['borderColor'] = '#DCDCDC'; f['textColor'] = '#151515'
json.dump(pack, open(f'{REPO}/public/badges-filled.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('wrote badges-filled.json')
