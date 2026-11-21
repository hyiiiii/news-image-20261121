#!/usr/bin/env python3
"""Render the 21 November 2026 world-news front illustration."""

from __future__ import annotations

import argparse
import io
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W = 1024
H = 1024
S = 2

PAPER = (244, 235, 216)
PAPER_LIGHT = (250, 243, 228)
PAPER_DARK = (228, 215, 191)
INK = (16, 36, 49)
INK_SOFT = (49, 69, 78)
VERM = (198, 65, 45)
VERM_DARK = (143, 45, 37)
TEAL = (38, 113, 106)
TEAL_DARK = (24, 75, 75)
TEAL_LIGHT = (137, 173, 158)
GOLD = (207, 159, 78)
GOLD_LIGHT = (235, 198, 127)
CREAM = (250, 243, 226)
SAND = (204, 159, 105)
DUSK = (148, 91, 66)
NIGHT = (10, 27, 42)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONTS = {
    "serif": FONT_DIR / "DejaVuSerif.ttf",
    "serifb": FONT_DIR / "DejaVuSerif-Bold.ttf",
    "sans": FONT_DIR / "DejaVuSans.ttf",
    "sansb": FONT_DIR / "DejaVuSans-Bold.ttf",
    "mono": FONT_DIR / "DejaVuSansMono.ttf",
}

STORY_LINES = {
    "lead_kicker": "01 / RIYADH · SATURDAY 21 NOV",
    "lead_headline": ("COALITION REPORTS", "THREE MISSILES DOWNED"),
    "lead_status": "SAUDI-LED COALITION CLAIM",
    "lead_body": "Coalition says three Houthi ballistic missiles were destroyed. A Reuters witness saw a projectile and heard a bang; no independent confirmation of every intercept.",
    "cop31_kicker": "02 / ANTALYA, TURKEY",
    "cop31_headline": ("COP31 RUNS", "INTO OVERTIME"),
    "cop31_status": "SAT 21 NOV · NO FINAL DEAL",
    "cop31_body": "Overtime past Friday's end; no final deal confirmed. A draft is criticized for omitting fossil fuels.",
    "korea_kicker": "03 / NORTH KOREA",
    "korea_headline": ("KIM VISIT REPORTED", "AFTER TRUMP TRIP"),
    "korea_status": "STATE MEDIA REPORT / 21 NOV",
    "korea_body": "KCNA says a Friday factory visit included school equipment; no comment on Trump.",
    "iran_kicker": "04 / TEHRAN–WASHINGTON",
    "iran_headline": ("DIPLOMACY STILL", "OPEN, IRAN SAYS"),
    "iran_status": "REPORTED SAT 21 NOV · NO DEAL",
    "iran_body": "Araqchi cites messages through mediators; Trump said Friday that Iran's terms were unacceptable.",
    "dragon_kicker": "05 / CALIFORNIA COAST",
    "dragon_headline": ("DRAGON RETURN", "SCHEDULED"),
    "dragon_status": "SCHEDULED / NOT YET CONFIRMED",
    "dragon_body": "NASA gives about 4:55pm EST (1:55pm PST); the capsule undocked on Friday.",
}

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(kind: str, size: float) -> ImageFont.FreeTypeFont:
    key = (kind, int(round(size * S)))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(FONTS[kind]), key[1])
    return _font_cache[key]


def sc(v: float) -> int:
    return int(round(v * S))


def box(values):
    return tuple(sc(v) for v in values)


def new_layer() -> Image.Image:
    return Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))


def paste_clipped(base: Image.Image, layer: Image.Image, mask: Image.Image) -> None:
    alpha = ImageChops.multiply(layer.getchannel("A"), mask)
    layer.putalpha(alpha)
    base.alpha_composite(layer)


def rect_mask(x0, y0, x1, y1) -> Image.Image:
    mask = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(mask).rectangle(box((x0, y0, x1, y1)), fill=255)
    return mask


def circle_mask(cx, cy, r) -> Image.Image:
    mask = Image.new("L", (W * S, H * S), 0)
    ImageDraw.Draw(mask).ellipse(box((cx - r, cy - r, cx + r, cy + r)), fill=255)
    return mask


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def paper_background() -> Image.Image:
    stops = [
        (0.00, (246, 237, 219)),
        (0.42, (244, 234, 214)),
        (0.74, (242, 232, 212)),
        (1.00, (236, 223, 201)),
    ]
    strip = Image.new("RGB", (1, H))
    px = strip.load()
    for y in range(H):
        t = y / (H - 1)
        for i in range(len(stops) - 1):
            a, ca = stops[i]
            b, cb = stops[i + 1]
            if a <= t <= b:
                px[0, y] = mix(ca, cb, (t - a) / (b - a) if b > a else 0)
                break
    bg = strip.resize((W * S, H * S), Image.Resampling.BILINEAR)
    return bg.convert("RGBA")


def add_glow(layer, cx, cy, rx, ry, color, strength):
    size = 160
    mask = Image.new("L", (size, size), 0)
    pix = mask.load()
    for yy in range(size):
        for xx in range(size):
            dx = (xx - size / 2) / (size / 2)
            dy = (yy - size / 2) / (size / 2)
            d = math.sqrt(dx * dx + dy * dy)
            if d < 1:
                value = (1 - d) ** 2
                pix[xx, yy] = int(255 * value)
    mask = mask.resize((max(2, sc(rx * 2)), max(2, sc(ry * 2))), Image.Resampling.BILINEAR)
    glow = Image.new("RGBA", mask.size, color + (0,))
    glow.putalpha(mask.point(lambda v: int(v * strength)))
    layer.alpha_composite(glow, (sc(cx - rx), sc(cy - ry)))


def tracked_width(text, kind, size, tracking):
    f = font(kind, size)
    return (sum(f.getlength(ch) for ch in text) + tracking * S * max(0, len(text) - 1)) / S


def tracked(draw, x, y, text, kind, size, fill, tracking=0.0, align="left"):
    f = font(kind, size)
    total = tracked_width(text, kind, size, tracking)
    if align == "right":
        x -= total
    elif align == "center":
        x -= total / 2
    cursor = x
    for ch in text:
        draw.text((sc(cursor), sc(y)), ch, font=f, fill=fill, anchor="lt")
        cursor += f.getlength(ch) / S + tracking
    return total


def text(draw, x, y, value, kind, size, fill, align="left"):
    f = font(kind, size)
    anchor = "lt"
    if align == "right":
        anchor = "rt"
    elif align == "center":
        anchor = "mt"
    draw.text((sc(x), sc(y)), value, font=f, fill=fill, anchor=anchor)


def wrap(value, kind, size, max_width):
    words = value.split()
    lines = []
    line = ""
    for word in words:
        trial = word if not line else line + " " + word
        if font(kind, size).getlength(trial) / S <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def hairline(draw, x0, y0, x1, y1, color, width=0.7):
    draw.line((sc(x0), sc(y0), sc(x1), sc(y1)), fill=color, width=max(1, sc(width)))


def draw_header(base):
    layer = new_layer()
    d = ImageDraw.Draw(layer)
    tracked(d, 52, 39, "THE SATURDAY WORLD DESK", "sansb", 9.2, INK, 1.55)
    tracked(d, 972, 39, "SATURDAY · AS OF 03:45 UTC / EARLY EDITION", "sansb", 9.2, VERM, 1.2, "right")
    hairline(d, 52, 60, 972, 60, INK, 0.9)

    text(d, 50, 62, "WORLD", "serifb", 112, INK)
    tracked(d, 55, 181, "AN ILLUSTRATED EDITION OF FIVE DISPATCHES", "sansb", 9.1, INK_SOFT, 1.35)

    text(d, 970, 54, "21", "serifb", 144, INK, "right")
    text(d, 970, 188, "NOV 2026", "serifb", 27, INK, "right")
    tracked(d, 970, 216, "11:45 ASIA / SHANGHAI", "sans", 8.6, INK_SOFT, 1.05, "right")

    hairline(d, 52, 229, 972, 229, INK, 1.35)
    hairline(d, 52, 234, 972, 234, INK, 0.4)
    base.alpha_composite(layer)


def bezier(p0, p1, p2, count=120):
    pts = []
    for i in range(count + 1):
        t = i / count
        u = 1 - t
        x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
        y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def dashed_polyline(d, pts, color, width, dash=5, gap=4):
    distance = 0.0
    draw_on = True
    elapsed = 0.0
    prev = pts[0]
    for point in pts[1:]:
        seg = math.dist(prev, point)
        if seg == 0:
            continue
        steps = max(1, int(seg / 1.5))
        for k in range(1, steps + 1):
            frac = k / steps
            q = (prev[0] + (point[0] - prev[0]) * frac, prev[1] + (point[1] - prev[1]) * frac)
            elapsed += seg / steps
            if draw_on:
                d.line((sc(prev[0]), sc(prev[1]), sc(q[0]), sc(q[1])), fill=color, width=max(1, sc(width)))
            if draw_on and elapsed >= dash:
                draw_on = False
                elapsed = 0
            elif not draw_on and elapsed >= gap:
                draw_on = True
                elapsed = 0
            prev = q


def starburst(d, cx, cy, r1, r2, points, fill, inner=None):
    verts = []
    for i in range(points * 2):
        angle = -math.pi / 2 + i * math.pi / points
        radius = r1 if i % 2 == 0 else r2
        verts.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    d.polygon([(sc(x), sc(y)) for x, y in verts], fill=fill)
    if inner:
        d.ellipse(box((cx - r2 * 0.62, cy - r2 * 0.62, cx + r2 * 0.62, cy + r2 * 0.62)), fill=inner)


def globe_project(lat, lon, cx, cy, r, lat0=23.0, lon0=47.0):
    phi = math.radians(lat)
    lam = math.radians(lon)
    phi0 = math.radians(lat0)
    cosc = math.sin(phi0) * math.sin(phi) + math.cos(phi0) * math.cos(phi) * math.cos(lam)
    if cosc < 0:
        return None
    x = math.cos(phi) * math.sin(lam)
    y = math.cos(phi0) * math.sin(phi) - math.sin(phi0) * math.cos(phi) * math.cos(lam)
    return cx + x * r, cy - y * r


def geo_segments(points, cx, cy, r, closed=False):
    pairs = list(zip(points, points[1:]))
    if closed:
        pairs.append((points[-1], points[0]))
    segments = []
    for (lat1, lon1), (lat2, lon2) in pairs:
        p1 = globe_project(lat1, lon1, cx, cy, r)
        p2 = globe_project(lat2, lon2, cx, cy, r)
        if p1 and p2:
            segments.append((p1, p2))
    return segments


def draw_moon(layer, d, cx, cy, r):
    d.ellipse(box((cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5)), fill=(118, 80, 61, 135))
    d.ellipse(box((cx - r, cy - r, cx + r, cy + r)), fill=(231, 212, 171, 255))

    globe = new_layer()
    gd = ImageDraw.Draw(globe)
    gd.ellipse(box((cx - r, cy - r, cx + r, cy + r)), fill=(230, 210, 168, 255))
    add_glow(globe, cx - 35, cy - 42, r * 0.92, r * 0.92, (250, 239, 209), 0.34)

    coastlines = [
        [(-17, 21), (-16, 14), (-8, 4), (2, 5), (9, 4), (9, -1), (13, -5), (12, -17), (15, -23), (20, -35), (27, -34), (33, -27), (40, -16), (41, -4), (51, 12), (43, 12), (41, 15), (37, 22), (34, 28), (32, 31), (25, 32), (15, 33), (10, 37), (0, 36), (-6, 36), (-10, 31), (-17, 21)],
        [(-10, 36), (-9, 43), (-2, 48), (2, 51), (8, 54), (11, 58), (20, 60), (30, 60), (40, 56), (40, 48), (30, 45), (28, 41), (20, 39), (12, 38), (5, 37), (-10, 36)],
        [(30, 60), (45, 68), (65, 70), (90, 75), (120, 75), (145, 58), (145, 45), (135, 35), (125, 30), (122, 22), (110, 20), (105, 10), (100, 7), (95, 15), (90, 22), (80, 23), (72, 20), (68, 24), (60, 25), (55, 28), (50, 30), (45, 40), (40, 50), (30, 60)],
        [(34, 29), (38, 31), (43, 30), (50, 25), (57, 23), (53, 17), (50, 15), (45, 12), (43, 15), (39, 17), (35, 22), (34, 29)],
        [(68, 24), (72, 20), (77, 8), (82, 15), (88, 22), (80, 25), (68, 24)],
        [(95, 5), (105, 0), (115, 0), (120, 5), (130, 0), (140, -5), (130, -8), (120, -8), (110, -7), (100, 0), (95, 5)],
        [(115, -20), (122, -18), (130, -12), (142, -12), (147, -20), (150, -30), (145, -38), (135, -35), (125, -32), (115, -34), (113, -26), (115, -20)],
        [(43, -13), (48, -15), (50, -22), (46, -25), (43, -22), (43, -13)],
        [(130, 31), (135, 34), (140, 37), (145, 44), (142, 45), (138, 37), (132, 33), (130, 31)],
        [(-5, 50), (-2, 54), (0, 57), (-3, 58), (-6, 55), (-5, 50)],
    ]
    for coast in coastlines:
        for p1, p2 in geo_segments(coast, cx, cy, r):
            gd.line((sc(p1[0]), sc(p1[1]), sc(p2[0]), sc(p2[1])), fill=(68, 111, 101, 145), width=sc(0.65))

    for lat in [-45, -30, -15, 0, 15, 30, 45, 60, 75]:
        pts = []
        for lon in range(-180, 181, 5):
            q = globe_project(lat, lon, cx, cy, r)
            if q:
                pts.append(q)
            elif len(pts) > 1:
                gd.line([(sc(x), sc(y)) for x, y in pts], fill=(61, 110, 101, 56), width=sc(0.45))
                pts = []
            else:
                pts = []
        if len(pts) > 1:
            gd.line([(sc(x), sc(y)) for x, y in pts], fill=(61, 110, 101, 56), width=sc(0.45))
    for lon in range(-180, 181, 15):
        pts = []
        for lat in range(-85, 86, 4):
            q = globe_project(lat, lon, cx, cy, r)
            if q:
                pts.append(q)
            elif len(pts) > 1:
                gd.line([(sc(x), sc(y)) for x, y in pts], fill=(61, 110, 101, 52), width=sc(0.45))
                pts = []
            else:
                pts = []
        if len(pts) > 1:
            gd.line([(sc(x), sc(y)) for x, y in pts], fill=(61, 110, 101, 52), width=sc(0.45))

    riyadh = globe_project(24.7, 46.7, cx, cy, r)
    if riyadh:
        d.arc(box((riyadh[0] - 11, riyadh[1] - 11, riyadh[0] + 11, riyadh[1] + 11)), 0, 360, fill=(188, 66, 45, 120), width=sc(0.55))
        d.ellipse(box((riyadh[0] - 4.5, riyadh[1] - 4.5, riyadh[0] + 4.5, riyadh[1] + 4.5)), fill=(247, 237, 214, 245))
        d.ellipse(box((riyadh[0] - 2.6, riyadh[1] - 2.6, riyadh[0] + 2.6, riyadh[1] + 2.6)), fill=(194, 61, 44, 255))

    mask = circle_mask(cx, cy, r)
    paste_clipped(layer, globe, mask)

    shade = new_layer()
    sd = ImageDraw.Draw(shade)
    sd.ellipse(box((cx - r, cy - r, cx + r, cy + r)), fill=(17, 35, 48, 255))
    smask = Image.new("L", (128, 128), 0)
    sp = smask.load()
    for yy in range(128):
        for xx in range(128):
            dx = (xx - 42) / 88
            dy = (yy - 48) / 88
            dval = math.sqrt(dx * dx + dy * dy)
            sp[xx, yy] = int(52 * max(0.0, min(1.0, (dval - 0.62) / 0.62)) ** 1.3)
    smask = smask.resize((sc(r * 2), sc(r * 2)), Image.Resampling.BILINEAR)
    alpha = ImageChops.multiply(smask, circle_mask(cx, cy, r).crop(box((cx - r, cy - r, cx + r, cy + r))))
    shade = shade.crop(box((cx - r, cy - r, cx + r, cy + r)))
    shade.putalpha(alpha)
    layer.alpha_composite(shade, (sc(cx - r), sc(cy - r)))

    d.arc(box((cx - r, cy - r, cx + r, cy + r)), 0, 360, fill=(176, 138, 89, 210), width=sc(1.1))
    d.arc(box((cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2)), 0, 360, fill=(246, 234, 207, 105), width=sc(0.5))

def draw_skyline(d):
    ink = (17, 38, 50, 255)
    window = (232, 178, 93, 235)
    glow = (222, 151, 87, 44)

    buildings = [
        (65, 462, 94, 31),
        (99, 452, 45, 41),
        (150, 458, 43, 35),
        (250, 448, 57, 45),
        (316, 460, 32, 33),
        (420, 452, 52, 41),
        (478, 444, 38, 49),
        (525, 458, 63, 35),
        (596, 450, 43, 43),
        (642, 462, 58, 31),
        (708, 453, 39, 40),
        (755, 465, 55, 28),
        (818, 455, 41, 38),
        (866, 461, 52, 32),
    ]
    for x, y, w, h in buildings:
        d.rectangle(box((x, y, x + w, y + h)), fill=ink)
        if w > 38:
            cols = max(1, w // 15)
            for c in range(cols):
                for r in range(max(1, h // 14)):
                    wx = x + 7 + c * 13
                    wy = y + 8 + r * 10
                    if wx + 2 < x + w - 4 and wy + 2 < y + h - 4:
                        d.rectangle(box((wx, wy, wx + 2, wy + 2)), fill=window)

    d.rectangle(box((254, 423, 263, 491)), fill=ink)
    d.rectangle(box((245, 438, 272, 444)), fill=ink)
    d.polygon([(sc(255), sc(423)), (sc(259), sc(409)), (sc(263), sc(423))], fill=ink)
    d.ellipse(box((251, 435, 266, 451)), fill=(215, 166, 88, 255))
    d.ellipse(box((254, 438, 263, 447)), fill=(248, 210, 135, 255))
    d.line((sc(258.5), sc(409), sc(258.5), sc(392)), fill=ink, width=sc(1.6))
    d.ellipse(box((257, 389, 260, 392)), fill=ink)

    left_body = [(348, 490), (348, 434), (352, 421), (362, 412), (369, 413), (370, 444), (370, 490)]
    right_body = [(390, 490), (390, 444), (391, 413), (398, 412), (408, 421), (412, 434), (412, 490)]
    d.polygon([(sc(x), sc(y)) for x, y in left_body], fill=ink)
    d.polygon([(sc(x), sc(y)) for x, y in right_body], fill=ink)
    d.rectangle(box((362, 409, 398, 417)), fill=ink)
    d.arc(box((361, 416, 399, 446)), 180, 360, fill=ink, width=sc(2.0))
    d.line((sc(370), sc(417), sc(370), sc(474)), fill=(34, 67, 78, 255), width=sc(0.8))
    d.line((sc(390), sc(417), sc(390), sc(474)), fill=(34, 67, 78, 255), width=sc(0.8))
    for wx, wy in [(359, 450), (402, 450), (361, 468), (400, 468)]:
        d.rectangle(box((wx, wy, wx + 3, wy + 4)), fill=window)

    d.rectangle(box((500, 424, 505, 494)), fill=ink)
    d.rectangle(box((495, 438, 510, 442)), fill=ink)
    d.polygon([(sc(490), sc(490)), (sc(490), sc(466)), (sc(502.5), sc(454)), (sc(515), sc(466)), (sc(515), sc(490))], fill=ink)
    d.ellipse(box((492, 464, 513, 483)), fill=ink)
    d.ellipse(box((497, 469, 508, 478)), fill=(39, 82, 82, 255))

    for x, y, w in [(555, 439, 59), (624, 447, 34), (675, 433, 46), (736, 442, 71), (810, 451, 34), (850, 444, 63), (918, 456, 42)]:
        d.rectangle(box((x, y, x + w, 493)), fill=ink)
        for wx in range(x + 6, x + w - 5, 13):
            for wy in range(y + 8, 487, 13):
                d.rectangle(box((wx, wy, wx + 2, wy + 2)), fill=window)



def draw_dunes(d):
    ridge = []
    for i in range(241):
        x = 52 + i * (920 / 240)
        y = 503 + 5 * math.sin(i / 11.0) + 2 * math.sin(i / 4.2)
        ridge.append((x, y))
    poly = ridge + [(972, 560), (52, 560)]
    d.polygon([(sc(x), sc(y)) for x, y in poly], fill=(195, 133, 84, 255))

    ridge2 = []
    for i in range(241):
        x = 52 + i * (920 / 240)
        y = 522 + 6 * math.sin(i / 15.0 + 1.4) + 2.5 * math.sin(i / 5.6)
        ridge2.append((x, y))
    poly2 = ridge2 + [(972, 560), (52, 560)]
    d.polygon([(sc(x), sc(y)) for x, y in poly2], fill=(224, 170, 111, 255))

    ridge3 = []
    for i in range(241):
        x = 52 + i * (920 / 240)
        y = 540 + 5 * math.sin(i / 18.0 + 2.1) + 2 * math.sin(i / 7.0)
        ridge3.append((x, y))
    poly3 = ridge3 + [(972, 560), (52, 560)]
    d.polygon([(sc(x), sc(y)) for x, y in poly3], fill=(239, 199, 146, 255))

    for pts, col in [(ridge, (137, 83, 60, 150)), (ridge2, (158, 97, 65, 115)), (ridge3, (173, 116, 78, 80))]:
        d.line([(sc(x), sc(y)) for x, y in pts], fill=col, width=sc(0.8))

    d.line([(sc(52), sc(550)), (sc(972), sc(550))], fill=(118, 73, 57, 90), width=sc(0.7))

    d.ellipse(box((100, 521, 104, 525)), fill=(20, 37, 42, 255))
    d.line((sc(102), sc(525), sc(102), sc(535)), fill=(20, 37, 42, 255), width=sc(1.4))
    d.line((sc(102), sc(535), sc(99), sc(543)), fill=(20, 37, 42, 255), width=sc(1.1))
    d.line((sc(102), sc(535), sc(105), sc(542)), fill=(20, 37, 42, 255), width=sc(1.1))
    d.line((sc(102), sc(529), sc(96), sc(533)), fill=(20, 37, 42, 255), width=sc(1.1))
    d.rectangle(box((104, 520, 108, 523)), fill=(20, 37, 42, 255))
    d.line((sc(106), sc(523), sc(106), sc(521)), fill=(20, 37, 42, 255), width=sc(0.6))


def draw_hero(base):
    x0, y0, x1, y1 = 52, 248, 972, 550
    layer = new_layer()
    d = ImageDraw.Draw(layer)

    sky_strip = Image.new("RGB", (1, 160))
    sky_px = sky_strip.load()
    stops = [
        (0.00, (8, 24, 39)),
        (0.34, (12, 34, 50)),
        (0.60, (31, 55, 65)),
        (0.80, (85, 66, 65)),
        (1.00, (154, 106, 77)),
    ]
    for yy in range(160):
        t = yy / 159
        for i in range(len(stops) - 1):
            a, ca = stops[i]
            b, cb = stops[i + 1]
            if a <= t <= b:
                sky_px[0, yy] = mix(ca, cb, (t - a) / (b - a) if b > a else 0)
                break
    sky = sky_strip.resize((sc(x1 - x0), sc(y1 - y0)), Image.Resampling.BILINEAR)
    layer.paste(sky, (sc(x0), sc(y0)))

    rng = random.Random(21112026)
    for _ in range(86):
        xx = rng.uniform(x0 + 10, x1 - 10)
        yy = rng.uniform(y0 + 8, y0 + 200)
        rr = rng.choice([0.55, 0.7, 0.85, 1.05])
        alpha = rng.randint(65, 155)
        d.ellipse(box((xx - rr, yy - rr, xx + rr, yy + rr)), fill=(245, 231, 199, alpha))

    draw_moon(layer, d, 768, 382, 143)
    add_glow(layer, 770, 430, 210, 170, (224, 152, 89), 0.27)

    d.arc(box((602, 258, 922, 540)), 196, 342, fill=(203, 101, 71, 120), width=sc(0.8))
    d.arc(box((627, 282, 900, 515)), 202, 338, fill=(203, 101, 71, 70), width=sc(0.6))

    trails = [
        ((70, 526), (250, 394), (452, 306)),
        ((118, 550), (356, 345), (576, 270)),
        ((196, 553), (458, 340), (704, 302)),
    ]
    for idx, (p0, p1, p2) in enumerate(trails):
        pts = bezier(p0, p1, p2)
        d.line([(sc(x), sc(y)) for x, y in pts], fill=(209, 76, 49, 80), width=sc(3.2))
        dashed_polyline(d, pts, (240, 118, 72, 245), 1.45, dash=5.5, gap=4.5)
        tip = pts[-1]
        starburst(d, tip[0], tip[1], 18 + idx * 2, 4.5, 9, (243, 197, 107, 255), (211, 78, 49, 255))
        for k in range(4):
            ang = math.radians(112 + idx * 11 + k * 19)
            length = 11 + k * 3
            d.line(
                (
                    sc(tip[0] + math.cos(ang) * 14),
                    sc(tip[1] + math.sin(ang) * 14),
                    sc(tip[0] + math.cos(ang) * (14 + length)),
                    sc(tip[1] + math.sin(ang) * (14 + length)),
                ),
                fill=(230, 159, 87, 145),
                width=sc(0.8),
            )
        d.arc(box((tip[0] - 25, tip[1] - 25, tip[0] + 25, tip[1] + 25)), 0, 360, fill=(242, 196, 111, 75), width=sc(0.7))

    for tx, ty, angle in [(438, 301, 1.1), (560, 276, 1.8), (704, 254, 2.5)]:
        d.line(
            (
                sc(tx),
                sc(ty),
                sc(tx + math.cos(angle) * 27),
                sc(ty + math.sin(angle) * 27),
            ),
            fill=(242, 197, 111, 115),
            width=sc(0.75),
        )

    add_glow(layer, 520, 482, 330, 105, (221, 145, 83), 0.22)
    add_glow(layer, 300, 493, 210, 70, (215, 137, 78), 0.14)
    draw_skyline(d)
    draw_dunes(d)

    vmask = Image.new("L", (128, 128), 0)
    vp = vmask.load()
    for yy in range(128):
        for xx in range(128):
            dx = abs(xx - 63.5) / 63.5
            dy = abs(yy - 63.5) / 63.5
            edge = max(dx, dy)
            vp[xx, yy] = int(55 * max(0.0, (edge - 0.56) / 0.44) ** 1.7)
    vmask = vmask.resize((sc(x1 - x0), sc(y1 - y0)), Image.Resampling.BILINEAR)
    overlay = Image.new("RGBA", vmask.size, (8, 20, 28, 0))
    overlay.putalpha(vmask)
    layer.alpha_composite(overlay, (sc(x0), sc(y0)))

    paste_clipped(base, layer, rect_mask(x0, y0, x1, y1))
    d0 = ImageDraw.Draw(base)
    hairline(d0, x0, y0, x1, y0, (85, 95, 89, 150), 0.6)
    hairline(d0, x0, y1, x1, y1, (20, 43, 52, 190), 0.8)


def draw_lead_text(base):
    layer = new_layer()
    d = ImageDraw.Draw(layer)
    tracked(d, 52, 565, "01 / RIYADH · SATURDAY 21 NOV", "sansb", 9.8, VERM, 1.3)
    text(d, 50, 578, STORY_LINES["lead_headline"][0], "serifb", 37, INK)
    text(d, 50, 617, STORY_LINES["lead_headline"][1], "serifb", 37, INK)
    hairline(d, 628, 574, 628, 653, (146, 111, 88), 0.7)
    tracked(d, 650, 573, STORY_LINES["lead_status"], "sansb", 9.4, VERM, 1.0)
    body_lines = wrap(STORY_LINES["lead_body"], "sans", 11.3, 312)
    yy = 590
    for line in body_lines[:5]:
        text(d, 650, yy, line, "sans", 11.3, INK_SOFT)
        yy += 14.0
    base.alpha_composite(layer)


def brief_circle(base, cx, cy, r, painter):
    layer = new_layer()
    d = ImageDraw.Draw(layer)
    mask = circle_mask(cx, cy, r)
    painter(d, cx, cy, r, layer)
    paste_clipped(base, layer, mask)
    overlay = new_layer()
    od = ImageDraw.Draw(overlay)
    od.ellipse(box((cx - r - 4, cy - r - 4, cx + r + 5, cy + r + 5)), outline=(16, 36, 49, 210), width=sc(1.2))
    od.ellipse(box((cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1)), outline=(247, 236, 216, 190), width=sc(0.7))
    base.alpha_composite(overlay)


def paint_cop31(d, cx, cy, r, layer):
    d.ellipse(box((cx - r, cy - r, cx + r, cy + r)), fill=(26, 67, 73, 255))
    d.arc(box((cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5)), 205, 330, fill=(47, 103, 100, 160), width=sc(0.7))
    for k in range(7):
        xx = cx - 38 + k * 12
        d.line((sc(xx), sc(cy - 43), sc(xx + 3), sc(cy - 20)), fill=(102, 151, 140, 100), width=sc(0.5))

    d.ellipse(box((cx + 12, cy - 43, cx + 54, cy - 1)), fill=(242, 230, 205, 255))
    d.ellipse(box((cx + 12, cy - 43, cx + 54, cy - 1)), outline=(198, 147, 75, 255), width=sc(1.0))
    for k in range(12):
        ang = math.radians(k * 30)
        d.line(
            (
                sc(cx + 33 + math.cos(ang) * 16),
                sc(cy - 22 + math.sin(ang) * 16),
                sc(cx + 33 + math.cos(ang) * 18.5),
                sc(cy - 22 + math.sin(ang) * 18.5),
            ),
            fill=(43, 75, 79, 180),
            width=sc(0.6),
        )
    d.line((sc(cx + 33), sc(cy - 22), sc(cx + 28), sc(cy - 33)), fill=(153, 50, 40, 255), width=sc(1.2))
    d.line((sc(cx + 33), sc(cy - 22), sc(cx + 41), sc(cy - 17)), fill=(153, 50, 40, 255), width=sc(0.9))

    d.arc(box((cx - 57, cy - 8, cx + 16, cy + 58)), 180, 360, fill=(43, 92, 91, 255), width=sc(1.0))
    for wx, wy in [(cx - 48, cy + 3), (cx - 32, cy - 3)]:
        d.line((sc(wx), sc(cy - 4), sc(wx), sc(cy + 28)), fill=(191, 214, 198, 115), width=sc(0.6))
        d.line((sc(wx - 5), sc(cy + 4), sc(wx + 5), sc(cy + 4)), fill=(191, 214, 198, 115), width=sc(0.6))
        d.line((sc(wx - 5), sc(cy + 10), sc(wx + 5), sc(cy + 10)), fill=(191, 214, 198, 115), width=sc(0.6))

    d.ellipse(box((cx - 68, cy + 28, cx + 64, cy + 65)), fill=(197, 160, 107, 255))
    d.ellipse(box((cx - 65, cy + 25, cx + 61, cy + 58)), fill=(228, 199, 151, 255))
    d.arc(box((cx - 66, cy + 25, cx + 62, cy + 62)), 0, 180, fill=(143, 105, 71, 190), width=sc(0.8))
    for mx in [cx - 38, cx - 4, cx + 29]:
        d.line((sc(mx), sc(cy + 37), sc(mx + 1), sc(cy + 17)), fill=(30, 50, 50, 255), width=sc(0.8))
        d.ellipse(box((mx - 2, cy + 12, mx + 4, cy + 18)), fill=(38, 55, 52, 255))
    d.rectangle(box((cx - 50, cy + 40, cx - 25, cy + 45)), fill=(246, 238, 216, 220))
    d.rectangle(box((cx + 12, cy + 43, cx + 42, cy + 48)), fill=(246, 238, 216, 185))

    for side, col in [(-1, (22, 53, 59, 255)), (1, (22, 53, 59, 255))]:
        xx = cx + side * 58
        d.ellipse(box((xx - 11, cy + 13, xx + 11, cy + 32)), fill=col)
        d.rectangle(box((xx - 10, cy + 26, xx + 10, cy + 61)), fill=col)
        d.line((sc(xx - 8), sc(cy + 61), sc(xx - 12), sc(cy + 70)), fill=col, width=sc(2.0))
        d.line((sc(xx + 8), sc(cy + 61), sc(xx + 12), sc(cy + 70)), fill=col, width=sc(2.0))

    d.line((sc(cx - 77), sc(cy + 67), sc(cx + 78), sc(cy + 67)), fill=(190, 148, 92, 120), width=sc(0.7))


def paint_korea(d, cx, cy, r, layer):
    d.ellipse(box((cx - r, cy - r, cx + r, cy + r)), fill=(219, 189, 143, 255))
    d.rectangle(box((cx - r, cy + 17, cx + r, cy + r)), fill=(198, 161, 110, 255))
    d.rectangle(box((cx - 51, cy - 58, cx + 28, cy - 3)), fill=(44, 105, 101, 255))
    d.rectangle(box((cx - 45, cy - 52, cx + 22, cy - 8)), fill=(173, 200, 178, 255))
    d.line((sc(cx - 51), sc(cy + 4), sc(cx + 28), sc(cy + 4)), fill=(31, 71, 74, 255), width=sc(2.0))
    d.line((sc(cx - 38), sc(cy - 52), sc(cx - 38), sc(cy + 3)), fill=(31, 71, 74, 255), width=sc(0.8))
    d.line((sc(cx - 9), sc(cy - 52), sc(cx - 9), sc(cy + 3)), fill=(31, 71, 74, 255), width=sc(0.8))
    d.rectangle(box((cx - 33, cy - 31, cx - 18, cy + 4)), fill=(33, 77, 79, 255))
    d.rectangle(box((cx - 22, cy - 55, cx - 17, cy - 31)), fill=(33, 77, 79, 255))
    d.rectangle(box((cx + 2, cy - 47, cx + 8, cy + 4)), fill=(33, 77, 79, 255))
    d.polygon([(sc(cx - 36), sc(cy - 55)), (sc(cx - 34), sc(cy - 63)), (sc(cx - 31), sc(cy - 55))], fill=(231, 220, 196, 165))
    d.polygon([(sc(cx - 22), sc(cy - 60)), (sc(cx - 19), sc(cy - 68)), (sc(cx - 16), sc(cy - 60))], fill=(231, 220, 196, 120))

    d.rectangle(box((cx - 52, cy + 31, cx + 56, cy + 42)), fill=(83, 53, 45, 255))
    d.rectangle(box((cx - 48, cy + 42, cx + 52, cy + 51)), fill=(112, 70, 54, 255))
    d.polygon([(sc(cx - 42), sc(cy + 31)), (sc(cx - 33), sc(cy + 8)), (sc(cx + 22), sc(cy + 8)), (sc(cx + 34), sc(cy + 31))], fill=(239, 226, 199, 255))
    d.line((sc(cx - 5), sc(cy + 9), sc(cx - 5), sc(cy + 30)), fill=(158, 126, 93, 255), width=sc(0.8))
    for off in [-7, 7]:
        d.arc(box((cx - 33 + off, cy + 12, cx + 15 + off, cy + 29)), 180, 360, fill=(151, 117, 85, 130), width=sc(0.5))

    d.rectangle(box((cx + 36, cy + 12, cx + 58, cy + 30)), fill=(114, 74, 55, 255))
    d.line((sc(cx + 39), sc(cy + 15), sc(cx + 39), sc(cy + 29)), fill=(237, 219, 185, 255), width=sc(0.7))
    d.line((sc(cx + 44), sc(cy + 15), sc(cx + 44), sc(cy + 29)), fill=(237, 219, 185, 255), width=sc(0.7))
    d.line((sc(cx + 49), sc(cy + 15), sc(cx + 49), sc(cy + 29)), fill=(237, 219, 185, 255), width=sc(0.7))
    for bx in [cx + 40, cx + 45, cx + 50, cx + 55]:
        for by in [cy + 18, cy + 23]:
            d.ellipse(box((bx - 1.5, by - 1.5, bx + 1.5, by + 1.5)), fill=(196, 69, 47, 255))

    d.rectangle(box((cx + 45, cy + 32, cx + 59, cy + 52)), fill=(44, 84, 79, 255))
    d.line((sc(cx + 52), sc(cy + 32), sc(cx + 52), sc(cy + 14)), fill=(44, 84, 79, 255), width=sc(1.4))
    d.ellipse(box((cx + 46, cy + 11, cx + 58, cy + 21)), fill=(44, 84, 79, 255))

    d.line((sc(cx - 75), sc(cy + 55), sc(cx + 78), sc(cy + 55)), fill=(111, 70, 49, 130), width=sc(0.7))


def paint_iran(d, cx, cy, r, layer):
    d.ellipse(box((cx - r, cy - r, cx + r, cy + r)), fill=(18, 45, 57, 255))
    d.rectangle(box((cx - 73, cy - 54, cx + 2, cy + 31)), fill=(35, 75, 79, 255))
    d.rectangle(box((cx + 2, cy - 54, cx + 73, cy + 31)), fill=(200, 181, 148, 255))
    d.line((sc(cx + 2), sc(cy - 56), sc(cx + 2), sc(cy + 32)), fill=(221, 158, 83, 210), width=sc(0.9))
    for k in range(3):
        yy = cy - 45 + k * 15
        d.line((sc(cx - 61), sc(yy), sc(cx - 12), sc(yy)), fill=(112, 155, 143, 90), width=sc(0.6))
        d.line((sc(cx + 14), sc(yy), sc(cx + 59), sc(yy)), fill=(128, 101, 78, 80), width=sc(0.6))

    d.ellipse(box((cx - 67, cy + 17, cx + 70, cy + 55)), fill=(209, 170, 113, 255))
    d.ellipse(box((cx - 64, cy + 13, cx + 67, cy + 50)), fill=(236, 210, 166, 255))
    d.arc(box((cx - 65, cy + 13, cx + 68, cy + 55)), 0, 180, fill=(137, 99, 68, 180), width=sc(0.8))
    for xx in [cx - 48, cx - 29, cx + 29, cx + 48]:
        d.rectangle(box((xx - 7, cy + 27, xx + 7, cy + 40)), fill=(248, 241, 225, 230))
        d.line((sc(xx - 5), sc(cy + 30), sc(xx + 4), sc(cy + 30)), fill=(156, 129, 99, 110), width=sc(0.45))
        d.line((sc(xx - 5), sc(cy + 34), sc(xx + 4), sc(cy + 34)), fill=(156, 129, 99, 110), width=sc(0.45))

    for side, col, xoff in [(-1, (31, 75, 78, 255), -55), (1, (154, 54, 43, 255), 55)]:
        xx = cx + xoff
        d.ellipse(box((xx - 12, cy - 2, xx + 12, cy + 19)), fill=col)
        d.rectangle(box((xx - 11, cy + 14, xx + 11, cy + 48)), fill=col)
        d.line((sc(xx - 8), sc(cy + 48), sc(xx - 13), sc(cy + 58)), fill=col, width=sc(2.0))
        d.line((sc(xx + 8), sc(cy + 48), sc(xx + 13), sc(cy + 58)), fill=col, width=sc(2.0))

    d.rectangle(box((cx - 17, cy + 24, cx + 17, cy + 33)), fill=(142, 42, 36, 255))
    d.rectangle(box((cx - 14, cy + 22, cx + 14, cy + 27)), fill=(190, 54, 41, 255))
    d.arc(box((cx - 30, cy + 24, cx - 15, cy + 35)), 90, 270, fill=(142, 42, 36, 255), width=sc(1.2))
    d.arc(box((cx + 15, cy + 24, cx + 31, cy + 36)), 270, 90, fill=(142, 42, 36, 255), width=sc(1.2))
    d.ellipse(box((cx - 6, cy + 26, cx + 6, cy + 32)), fill=(243, 196, 112, 255))
    for k in range(12):
        ang = k * math.pi / 6
        d.ellipse(box((cx + 2 + math.cos(ang) * 2.2, cy + 34 + math.sin(ang) * 2.2, cx + 3.5 + math.cos(ang) * 2.2, cy + 35.5 + math.sin(ang) * 2.2)), fill=(236, 194, 112, 235))

    d.line((sc(cx - 73), sc(cy + 60), sc(cx + 73), sc(cy + 60)), fill=(223, 189, 132, 100), width=sc(0.6))


def paint_dragon(d, cx, cy, r, layer):
    d.ellipse(box((cx - r, cy - r, cx + r, cy + r)), fill=(205, 220, 205, 255))
    d.pieslice(box((cx - r, cy - r, cx + r, cy + r)), 0, 180, fill=(35, 100, 103, 255))
    d.pieslice(box((cx - r, cy - r + 28, cx + r, cy + r), ), 0, 180, fill=(43, 116, 113, 255))
    for k in range(4):
        yy = cy + 19 + k * 12
        d.arc(box((cx - 75 + k * 9, yy - 12, cx - 10 + k * 7, yy + 16)), 190, 345, fill=(157, 194, 181, 140), width=sc(0.6))
        d.arc(box((cx + 2, yy - 8, cx + 74 - k * 8, yy + 18)), 190, 345, fill=(157, 194, 181, 115), width=sc(0.6))
    d.arc(box((cx - 75, cy + 24, cx + 76, cy + 68)), 190, 350, fill=(231, 211, 173, 110), width=sc(0.7))

    d.arc(box((cx - 27, cy - 54, cx - 2, cy - 27)), 120, 305, fill=(196, 65, 45, 255), width=sc(0.9))
    d.arc(box((cx + 2, cy - 54, cx + 27, cy - 27)), 235, 60, fill=(196, 65, 45, 255), width=sc(0.9))
    d.arc(box((cx - 19, cy - 61, cx + 19, cy - 28)), 205, 335, fill=(239, 220, 179, 255), width=sc(1.0))
    for xx, yy in [(cx - 14, cy - 26), (cx, cy - 24), (cx + 14, cy - 26)]:
        d.line((sc(xx), sc(yy), sc(xx - 3), sc(cy - 7)), fill=(194, 171, 127, 210), width=sc(0.5))
        d.line((sc(xx), sc(yy), sc(xx + 3), sc(cy - 7)), fill=(194, 171, 127, 210), width=sc(0.5))

    d.ellipse(box((cx - 10, cy - 8, cx + 10, cy + 14)), fill=(229, 212, 176, 255))
    d.rectangle(box((cx - 7, cy + 5, cx + 8, cy + 21)), fill=(182, 118, 67, 255))
    d.ellipse(box((cx - 8, cy + 1, cx + 8, cy + 11)), fill=(30, 61, 67, 255))
    d.rectangle(box((cx - 4, cy + 10, cx + 4, cy + 16)), fill=(232, 186, 105, 255))
    d.polygon([(sc(cx - 1), sc(cy + 14)), (sc(cx + 9), sc(cy + 11)), (sc(cx + 1), sc(cy + 18))], fill=(201, 70, 47, 255))

    d.line((sc(cx + 4), sc(cy + 26), sc(cx - 26), sc(cy + 34)), fill=(110, 156, 148, 95), width=sc(0.6))
    dashed_polyline(d, bezier((cx + 38, cy - 77), (cx + 5, cy - 49), (cx + 3, cy - 16)), (246, 234, 204, 180), 0.7, dash=2.5, gap=3.5)
    for rr in [16, 29, 42]:
        d.arc(box((cx - rr, cy + 58 - rr * 0.22, cx + rr, cy + 58 + rr * 0.22)), 0, 360, fill=(226, 238, 217, 70), width=sc(0.5))


def draw_briefs(base):
    cols = [52, 284, 516, 748]
    cy = 735
    radius = 53
    painters = [paint_cop31, paint_korea, paint_iran, paint_dragon]

    layer = new_layer()
    d = ImageDraw.Draw(layer)
    hairline(d, 52, 677, 972, 677, INK, 0.9)
    for x in [266, 498, 730]:
        hairline(d, x, 687, x, 922, (101, 96, 84), 0.55)
    base.alpha_composite(layer)

    for idx, (x, paint) in enumerate(zip(cols, painters)):
        cx = x + 108
        brief_circle(base, cx, cy, radius, paint)
        num_layer = new_layer()
        nd = ImageDraw.Draw(num_layer)
        nd.ellipse(box((x, 681, x + 23, 704)), fill=VERM)
        text(nd, x + 11.5, 683.2, f"{idx + 2:02d}", "sansb", 8.2, CREAM, "center")
        base.alpha_composite(num_layer)

        layer = new_layer()
        d = ImageDraw.Draw(layer)
        kicker_key = ["cop31_kicker", "korea_kicker", "iran_kicker", "dragon_kicker"][idx]
        headline_key = ["cop31_headline", "korea_headline", "iran_headline", "dragon_headline"][idx]
        status_key = ["cop31_status", "korea_status", "iran_status", "dragon_status"][idx]
        body_key = ["cop31_body", "korea_body", "iran_body", "dragon_body"][idx]

        tracked(d, x, 796, STORY_LINES[kicker_key], "sansb", 8.9, VERM, 0.8)
        yy = 813
        for line in STORY_LINES[headline_key]:
            text(d, x, yy, line, "serifb", 17.2, INK)
            yy += 20.0
        tracked(d, x, 869, STORY_LINES[status_key], "sansb", 9.1, VERM if idx != 3 else TEAL_DARK, 0.42)
        body_lines = wrap(STORY_LINES[body_key], "sans", 10.6, 211)
        yy = 886
        for line in body_lines[:3]:
            text(d, x, yy, line, "sans", 10.6, INK_SOFT)
            yy += 13.2
        base.alpha_composite(layer)


def draw_footer(base):
    layer = new_layer()
    d = ImageDraw.Draw(layer)
    hairline(d, 52, 939, 972, 939, INK, 0.9)
    tracked(d, 52, 949, "WORLD / 21 NOV 2026", "sansb", 8.8, INK, 1.15)
    tracked(d, 512, 949, "EARLY EDITION · AS OF 03:45 UTC / 11:45 ASIA-SHANGHAI", "sansb", 8.8, VERM, 0.65, "center")
    tracked(d, 972, 949, "REUTERS · AP · AFP · NASA", "sansb", 8.8, INK, 0.8, "right")
    text(d, 512, 964, "Statuses as reported at cutoff; this is not a final end-of-day digest.", "sans", 8.9, INK_SOFT, "center")
    base.alpha_composite(layer)


def add_paper_finish(img):
    rng = random.Random(21112026)
    grain = Image.new("L", (150, 150))
    gp = grain.load()
    for yy in range(150):
        for xx in range(150):
            gp[xx, yy] = max(0, min(255, int(rng.gauss(128, 12))))
    grain = grain.filter(ImageFilter.GaussianBlur(0.55)).resize((W, H), Image.Resampling.BILINEAR)
    grain_rgb = Image.merge("RGB", (grain, grain, grain))
    textured = ImageChops.add(img, grain_rgb, scale=1.0, offset=-128)
    img = Image.blend(img, textured, 0.22)

    fibers = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fibers)
    for _ in range(150):
        x = rng.uniform(42, 982)
        y = rng.uniform(36, 982)
        length = rng.uniform(2, 10)
        angle = rng.uniform(-0.25, 0.25)
        fd.line((x, y, x + length * math.cos(angle), y + length * math.sin(angle)), fill=(92, 72, 50, rng.randint(8, 20)), width=1)

    vignette = Image.new("L", (W, H), 0)
    vp = vignette.load()
    for yy in range(H):
        for xx in range(W):
            dx = abs(xx - W / 2) / (W / 2)
            dy = abs(yy - H / 2) / (H / 2)
            d = max(dx, dy)
            vp[xx, yy] = int(26 * max(0, d - 0.58) / 0.42)
    shade = Image.new("RGBA", (W, H), (36, 26, 18, 0))
    shade.putalpha(vignette)
    img = Image.alpha_composite(img.convert("RGBA"), fibers)
    img = Image.alpha_composite(img, shade)

    corner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cd = ImageDraw.Draw(corner)
    cd.rectangle((0, 0, W - 1, H - 1), outline=(81, 65, 48, 34), width=1)
    return Image.alpha_composite(img, corner).convert("RGB")


def render() -> Image.Image:
    base = paper_background()
    draw_header(base)
    draw_hero(base)
    draw_lead_text(base)
    draw_briefs(base)
    draw_footer(base)
    img = base.convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    return add_paper_finish(img)


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True, compress_level=9)
    data = buf.getvalue()
    if len(data) > 1_048_576:
        for colors in (192, 128, 96):
            q = img.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
            buf = io.BytesIO()
            q.save(buf, format="PNG", optimize=True, compress_level=9)
            data = buf.getvalue()
            if len(data) <= 1_048_576:
                break
    if len(data) > 1_048_576:
        raise RuntimeError("rendered PNG exceeds 1,048,576 bytes")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="assets/entry.png")
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = render()
    data = png_bytes(img)
    out.write_bytes(data)
    print(f"wrote {out} ({img.width}x{img.height}, {len(data)} bytes)")


if __name__ == "__main__":
    main()
