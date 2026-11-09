"""Preview of three filled-pack variants inside Nuvio's real sources chip. Nothing is published.
A  current (published): one label, one fill
B  quiet suffix after a hairline + greyscale tiers (hero / core / quiet / warn)
C  B + stacked DOLBY kicker + mono Tabler glyph on hero badges
"""
import os, subprocess, json, io
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.join(REPO, '.work')  # fonts + icons, see README
GD = f'{ROOT}/g/package/dist/fonts/geist-sans'
SEMI, MED = f'{GD}/Geist-SemiBold.ttf', f'{GD}/Geist-Medium.ttf'
TAB = f'{ROOT}/tabler/package/icons/outline'
SS = 4

TIERS = {  # chip fill, main text, suffix text, divider, border
    'hero':  ((0xF6, 0xF6, 0xF6), (0x12, 0x12, 0x12), (0x6E, 0x6E, 0x6E), (0xA8, 0xA8, 0xA8), None),
    'core':  ((0xDC, 0xDC, 0xDC), (0x15, 0x15, 0x15), (0x66, 0x66, 0x66), (0x9C, 0x9C, 0x9C), None),
    'quiet': ((0x8E, 0x8E, 0x8E), (0x14, 0x14, 0x14), (0x3C, 0x3C, 0x3C), (0x5E, 0x5E, 0x5E), None),
    'warn':  ((0x14, 0x14, 0x16), (0xF2, 0xF2, 0xF2), (0xA0, 0xA0, 0xA0), (0x70, 0x70, 0x70), (0xE6, 0xE6, 0xE6)),
}

# id: (plain label, main, suffix, kicker(main word under DOLBY) or None, tier, icon)
S = {
 'r-4k':('4K','4K','UHD',None,'hero','device-tv'),
 'r-1440p':('1440p','1440p','QHD',None,'core',None),
 'r-1080':('1080p','1080p','FHD',None,'core',None),
 'r-720':('720p','720p','HD',None,'core',None),
 'r-576p':('576p','576p','PAL',None,'quiet',None),
 'r-480p':('480p','480p','SD',None,'quiet',None),
 'r-360p':('360p','360p','LOW',None,'quiet',None),
 'q-r':('REMUX','REMUX',None,None,'hero','disc'),
 'q-b':('BLURAY','BLURAY',None,None,'core',None),
 'q-w':('WEB-DL','WEB-DL',None,None,'core',None),
 'src-webrip':('WEBRIP','WEBRIP',None,None,'core',None),
 'src-hdrip':('HDRIP','HDRIP',None,None,'quiet',None),
 'src-dvdrip':('DVDRIP','DVDRIP',None,None,'quiet',None),
 'src-hdtv':('HDTV','HDTV',None,None,'quiet',None),
 'gq-scr':('SCR','SCR','SCREENER',None,'warn',None),
 'a-dv':('DOLBY VISION','DOLBY VISION',None,'VISION','hero','circle-half-2'),
 'v-hdr10p':('HDR10+','HDR10+',None,None,'core',None),
 'v-hdr10':('HDR10','HDR10',None,None,'core',None),
 'v-hdr':('HDR','HDR',None,None,'core',None),
 'v-hlg':('HLG','HLG',None,None,'core',None),
 'v-dv-hdr10p':('DV · HDR10+','DV','HDR10+',None,'hero','circle-half-2'),
 'v-dv-hdr10':('DV · HDR10','DV','HDR10',None,'hero','circle-half-2'),
 'v-dv-hdr':('DV · HDR','DV','HDR',None,'hero','circle-half-2'),
 'a-atmos-truehd':('ATMOS · TRUEHD','ATMOS','TRUEHD',None,'hero','volume'),
 'a-atmos-ddplus':('ATMOS · DD+','ATMOS','DD+',None,'hero','volume'),
 'a-at':('DOLBY ATMOS','DOLBY ATMOS',None,'ATMOS','hero','volume'),
 'a-dtsx-hdma':('DTS:X · HD MA','DTS:X','HD MA',None,'hero','volume'),
 'a-dtsx-hd':('DTS:X · HD','DTS:X','HD',None,'hero','volume'),
 'a-dtsx':('DTS:X','DTS:X',None,None,'hero','volume'),
 'a-th':('TRUEHD','TRUEHD',None,'TRUEHD','core',None),
 'a-dtsma':('DTS-HD MA','DTS-HD','MA',None,'core',None),
 'a-flac':('FLAC','FLAC',None,None,'core',None),
 'a-dtshd':('DTS-HD','DTS-HD',None,None,'core',None),
 'a-dp':('DD+','DD+',None,'DIGITAL+','core',None),
 'gv-dts-es':('DTS-ES','DTS-ES',None,None,'core',None),
 'a-dts':('DTS','DTS',None,None,'core',None),
 'a-dd':('DD','DD',None,'DIGITAL','quiet',None),
 'v-imax-e-2':('IMAX ENHANCED','IMAX','ENHANCED',None,'hero','aspect-ratio'),
 'v-imax-2':('IMAX','IMAX',None,None,'hero','aspect-ratio'),
 'seadex-release':('SEADEX','SEADEX',None,None,'core',None),
 'open-matte-edition':('OPEN MATTE','OPEN MATTE',None,None,'core',None),
 'regraded-release':('REGRADED','REGRADED',None,None,'core',None),
 'edition-directors-cut':("DIRECTOR'S CUT","DIRECTOR'S CUT",None,None,'core',None),
 'edition-extended':('EXTENDED','EXTENDED',None,None,'core',None),
 'uncut-edition':('UNCUT','UNCUT',None,None,'core',None),
 'uncensored-edition':('UNCENSORED','UNCENSORED',None,None,'core',None),
 'black-and-white':('BLACK & WHITE','BLACK & WHITE',None,None,'core',None),
 'true-hue-edition':('TRUE-HUE','TRUE-HUE',None,None,'core',None),
 'edition-theatrical':('THEATRICAL','THEATRICAL',None,None,'core',None),
}

B2_FILL = {'hero': (0xFB, 0xFB, 0xFB), 'core': (0xD6, 0xD6, 0xD6), 'quiet': (0x8A, 0x8A, 0x8A)}
EDITIONS = {'seadex-release','open-matte-edition','regraded-release','edition-directors-cut','edition-extended',
            'uncut-edition','uncensored-edition','black-and-white','true-hue-edition','edition-theatrical'}
GROUP_ORDER = ['gr', 'gv', 'gq', 'ga', 'imax', 'gst']  # resolution, visual, quality, audio, IMAX, special

_fc = {}
def font(path, cap_px):
    k = (path, round(cap_px, 2))
    if k not in _fc:
        f = ImageFont.truetype(path, 200); l, t, r, b = f.getbbox('H')
        _fc[k] = ImageFont.truetype(path, max(1, round(200 * cap_px / (b - t))))
    return _fc[k]

def run_w(text, f, track_em):
    return sum(f.getlength(c) for c in text) + track_em * f.size * (len(text) - 1)

def draw_run(d, x, cap_y_bottom, text, f, track_em, color):
    """Draw text with its capitals' baseline at cap_y_bottom."""
    l, t, r, b = f.getbbox('H')
    y = cap_y_bottom - b
    for c in text:
        d.text((x, y), c, font=f, fill=color + (255,)); x += f.getlength(c) + track_em * f.size
    return x

_ic = {}
def icon(name, size_px, color):
    k = (name, size_px, color)
    if k not in _ic:
        svg = open(f'{TAB}/{name}.svg').read().replace('currentColor', '#%02x%02x%02x' % color).replace('stroke-width="2"', 'stroke-width="2.4"')
        png = subprocess.run(['rsvg-convert', '-w', str(size_px), '-h', str(size_px)], input=svg.encode(), capture_output=True, check=True).stdout
        _ic[k] = Image.open(io.BytesIO(png)).convert('RGBA')
    return _ic[k]

def badge(fid, variant, P, min_dp=34):
    """Image for one filter (16 dp tall, transparent) + chip fill/border. P = px per dp."""
    plain, main, suf, kick, tier, ic = S[fid]
    if variant == 'A': tier = 'core'
    fill, tc, sc, dc, border = TIERS[tier]
    b2 = variant == 'B2'
    if b2: fill = B2_FILL.get(tier, fill)
    s = P * SS; H = 16 * s
    fm = font(SEMI, 7.5 * s); tm = 0.021
    fs = font(MED, 5.0 * s); ts = 0.07
    parts = []  # (kind, width, payload)
    if variant == 'A':
        parts = [('t', run_w(plain, fm, tm), (plain, fm, tm, tc))]
    else:
        use_kick = variant == 'C' and kick
        if variant == 'C' and ic:
            parts.append(('i', 7.5 * s, ic)); parts.append(('g', 2.2 * s, None))
        if use_kick:
            fk = font(MED, 3.4 * s); tk = 0.24; fmk = font(SEMI, 6.2 * s)
            parts.append(('k', max(run_w('DOLBY', fk, tk), run_w(kick, fmk, tm)), (kick, fk, tk, fmk)))
        elif b2 and fid in EDITIONS:  # edition tags read as metadata: lighter weight, wider spacing
            fe = font(MED, 7.0 * s); te = 0.075
            parts.append(('t', run_w(main, fe, te), (main, fe, te, tc)))
        else:
            parts.append(('t', run_w(main, fm, tm), (main, fm, tm, tc)))
        if suf:
            g, dw = (2.4, 1.05) if b2 else (2.6, 0.9)
            parts += [('g', g * s, None), ('d', dw * s, None), ('g', g * s, None), ('t', run_w(suf, fs, ts), (suf, fs, ts, sc))]
    tw = sum(p[1] for p in parts)
    W = int(round(max(tw + 2 * 1.0 * s, min_dp * s))); W += (SS - W % SS) % SS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = (W - tw) / 2; base = (H + 7.5 * s) / 2  # main caps centred
    for kind, w, p in parts:
        if kind == 't':
            text, f, tr, col = p
            draw_run(d, x, base, text, f, tr, col)
        elif kind == 'd':
            dh = 5.4 * s if b2 else 7.5 * s
            mid = base - 7.5 * s / 2
            d.rectangle([x, mid - dh / 2, x + w, mid + dh / 2], fill=dc + (255,))
        elif kind == 'i':
            g = icon(p, int(w), tc); im.alpha_composite(g, (int(x), int((H - g.height) / 2)))
        elif kind == 'k':
            kick, fk, tk, fmk = p
            kh, mh, gap = 3.4 * s, 6.2 * s, 1.2 * s
            top = (H - (kh + gap + mh)) / 2
            draw_run(d, x + (w - run_w('DOLBY', fk, tk)) / 2, top + kh, 'DOLBY', fk, tk, sc)
            draw_run(d, x + (w - run_w(kick, fmk, tm)) / 2, top + kh + gap + mh, kick, fmk, tm, tc)
        x += w
    return im.resize((W // SS, H // SS), Image.LANCZOS), fill, border, tier

def chip(fid, variant, P, min_dp=34):
    img, fill, border, tier = badge(fid, variant, P, min_dp)
    box_w = min(max(img.width, 34 * P), 92 * P)
    over = img.width > 92 * P
    if over: img = img.resize((92 * P, round(img.height * 92 * P / img.width)), Image.LANCZOS)
    cw, ch = box_w + 6 * P, 20 * P
    c = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); dd = ImageDraw.Draw(c)
    dd.rounded_rectangle([0, 0, cw - 1, ch - 1], 6 * P, fill=fill + (255,), outline=(border + (255,)) if border else None, width=max(1, P // 2))
    c.alpha_composite(img, ((cw - img.width) // 2, (ch - img.height) // 2))
    return c, img.width / P if not over else None, over
