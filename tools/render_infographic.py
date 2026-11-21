#!/usr/bin/env python3
"""Render an original typographic news poster for 21 November 2026.

Draws only geometry and original text. No photographs, no image-generation
APIs, no third-party artwork. Output is a deterministic 1024x1024 PNG.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
OUT = Path(__file__).resolve().parent.parent / "assets" / "entry.png"
PREVIEW = Path(__file__).resolve().parent.parent / "preview" / "entry.png"

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
SERIF = FONT_DIR / "LiberationSerif-Regular.ttf"
SERIF_B = FONT_DIR / "LiberationSerif-Bold.ttf"
SANS = FONT_DIR / "LiberationSans-Regular.ttf"
SANS_B = FONT_DIR / "LiberationSans-Bold.ttf"
SANS_I = FONT_DIR / "LiberationSans-Italic.ttf"

# Editorial palette — original, not taken from any masthead
PAPER = (244, 239, 228)
INK = (22, 27, 34)
MUTED = (78, 82, 88)
RULE = (163, 36, 36)
NAVY = (18, 44, 74)
TEAL = (22, 92, 88)
GOLD = (168, 126, 62)
CARD = (252, 250, 244)
CARD_ALT = (237, 242, 239)
HAIR = (196, 188, 174)


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else f"{cur} {word}"
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, xy, text, fnt, fill, max_w, leading=None, max_y=None):
    x, y = xy
    if leading is None:
        leading = int(fnt.size * 1.28)
    lines = wrap(draw, text, fnt, max_w)
    used = 0
    for i, line in enumerate(lines):
        yy = y + i * leading
        if max_y is not None and yy + leading > max_y:
            break
        draw.text((x, yy), line, font=fnt, fill=fill)
        used += 1
    return y + used * leading, used


def rounded_rect(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def icon_arrows(draw, cx, cy, color):
    """Three descending chevrons — abstract incursion, not a map or logo."""
    for i, dy in enumerate((-16, 0, 16)):
        y = cy + dy
        s = 11 - i
        draw.polygon([(cx - 14, y - s), (cx, y + s), (cx + 14, y - s)], outline=color)
        draw.line([(cx - 14, y - s), (cx, y + s), (cx + 14, y - s)], fill=color, width=2)


def icon_link(draw, cx, cy, c1, c2):
    """Two interlocking rings — concluded agreements."""
    r = 13
    draw.ellipse((cx - 22, cy - r, cx - 22 + 2 * r, cy + r), outline=c1, width=3)
    draw.ellipse((cx + 22 - 2 * r, cy - r, cx + 22, cy + r), outline=c2, width=3)


def icon_talks(draw, cx, cy, color):
    """Two facing blocks at a table — talks, not a portrait."""
    draw.rectangle((cx - 20, cy - 8, cx - 8, cy + 10), outline=color, width=2)
    draw.rectangle((cx + 8, cy - 8, cx + 20, cy + 10), outline=color, width=2)
    draw.line((cx - 22, cy + 14, cx + 22, cy + 14), fill=color, width=2)


def icon_scales(draw, cx, cy, color):
    """Geometric balance — court, not a copyrighted emblem."""
    draw.line((cx, cy - 16, cx, cy + 16), fill=color, width=2)
    draw.line((cx - 16, cy - 8, cx + 16, cy - 8), fill=color, width=2)
    draw.polygon([(cx - 16, cy - 8), (cx - 7, cy + 6), (cx - 25, cy + 6)], outline=color)
    draw.polygon([(cx + 16, cy - 8), (cx + 7, cy + 6), (cx + 25, cy + 6)], outline=color)
    draw.rectangle((cx - 8, cy + 14, cx + 8, cy + 18), fill=color)


def icon_capsule(draw, cx, cy, color):
    """Abstract capsule and arc — scheduled return, not a photo."""
    draw.rounded_rectangle((cx - 8, cy - 16, cx + 8, cy + 12), radius=6, outline=color, width=2)
    draw.arc((cx - 22, cy - 28, cx + 22, cy - 4), start=200, end=340, fill=color, width=2)
    draw.line((cx - 14, cy - 14, cx - 8, cy - 8), fill=color, width=2)
    draw.line((cx + 14, cy - 14, cx + 8, cy - 8), fill=color, width=2)


def render() -> Image.Image:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    f_kicker = font(SANS, 15)
    f_date = font(SANS_B, 15)
    f_title = font(SERIF_B, 44)
    f_sub = font(SANS, 16)
    f_region = font(SANS_B, 12)
    f_head = font(SERIF_B, 22)
    f_head_sm = font(SERIF_B, 18)
    f_body = font(SANS, 14)
    f_src = font(SANS_I, 11)
    f_foot = font(SANS, 11)
    f_num = font(SANS_B, 16)

    # Outer rule
    d.rectangle((16, 16, W - 17, H - 17), outline=NAVY, width=2)
    d.rectangle((22, 22, W - 23, H - 23), outline=GOLD, width=1)

    # Masthead
    y = 34
    d.text((40, y), "SATURDAY  21  NOVEMBER  2026", font=f_date, fill=NAVY)
    right = "WORLD DESK  ·  ONE IMAGE"
    rw = d.textlength(right, font=f_kicker)
    d.text((W - 40 - rw, y), right, font=f_kicker, fill=MUTED)
    y = 58
    d.line((40, y, W - 40, y), fill=RULE, width=3)
    y = 68
    d.text((40, y), "The world on Saturday", font=f_title, fill=INK)
    y = 122
    sub = (
        "A typographic briefing of verified reports circulating on 21 November 2026. "
        "Each card prints the event date. No photographs."
    )
    y, _ = draw_wrapped(d, (40, y), sub, f_sub, MUTED, W - 80, leading=20)
    y += 8
    d.line((40, y, W - 40, y), fill=HAIR, width=1)

    # --- Card 1: Poland, full width ---
    y += 12
    x0, x1 = 36, W - 36
    card1_h = 196
    rounded_rect(d, (x0, y, x1, y + card1_h), 8, CARD, outline=HAIR, width=1)
    d.rectangle((x0, y, x0 + 8, y + card1_h), fill=RULE)
    icon_arrows(d, x0 + 44, y + 44, RULE)
    d.text((x0 + 70, y + 14), "01   POLAND  ·  NATO'S EASTERN FLANK", font=f_region, fill=RULE)
    d.text((x0 + 70, y + 32), "Poland reports Russian missiles and a drone in its airspace", font=f_head, fill=INK)
    body1 = (
        "On Friday 20 November, Defence Minister Władysław Kosiniak-Kamysz said three objects entered Polish airspace overnight: a Kh-101 missile, a second missile, and what was most likely a jet-powered drone. Prime Minister Donald Tusk called it an “intentional provocation,” noting allied exercises in Poland that day. NATO Secretary General Mark Rutte described the incident as “clearly dangerous” and was due in Warsaw on Saturday. The Russian embassy in Warsaw had not commented when Reuters filed."
    )
    draw_wrapped(d, (x0 + 20, y + 78), body1, f_body, INK, x1 - x0 - 40, leading=18, max_y=y + card1_h - 24)
    d.text((x0 + 20, y + card1_h - 22), "Source: Reuters  ·  20 Nov 2026, 08:01 UTC  ·  dateline Nowy Lipowiec", font=f_src, fill=MUTED)

    y = y + card1_h + 10
    gap = 10
    col_w = (W - 72 - gap) // 2
    left = 36
    right_x = 36 + col_w + gap
    row_h = 232

    cards = [
        {
            "box": (left, y, left + col_w, y + row_h),
            "num": "02",
            "kicker": "BRUSSELS  ·  EU–UK SUMMIT",
            "color": TEAL,
            "icon": "link",
            "head": "EU and UK close talks on food trade, carbon and youth travel",
            "body": (
                "Leaders met in Brussels on 20 November and welcomed three deals: an SPS area aiming to drop most animal and plant certificates from 1 March 2028; linking emissions-trading systems from 2028, with a path to mutual CBAM exemptions; and a Youth Experience Scheme for 100,000 young people from each side, for up to three years, with places no later than January 2030."
            ),
            "src": "Sources: GOV.UK joint statement; European Commission, 20 Nov 2026",
            "head_font": "sm",
        },
        {
            "box": (right_x, y, right_x + col_w, y + row_h),
            "num": "03",
            "kicker": "WASHINGTON  ·  IRAN",
            "color": NAVY,
            "icon": "talks",
            "head": "Trump says Iran wants a deal — not one he will accept",
            "body": (
                "In a 21 November world summary, Xinhua reported that on Friday President Donald Trump told a White House press conference Iran wants an agreement with the United States but remains unwilling to accept terms Washington considers acceptable. His words, as carried: “Iran wants to make a deal, but they don't want to make a deal that's acceptable to me.”"
            ),
            "src": "Source: Xinhua world news summary, 21 Nov 2026, 08:28:30",
            "head_font": "sm",
        },
        {
            "box": (left, y + row_h + gap, left + col_w, y + row_h + gap + row_h),
            "num": "04",
            "kicker": "THE HAGUE  ·  19 NOV, STILL IN SATURDAY BRIEFS",
            "color": GOLD,
            "icon": "scales",
            "head": "ICJ finds Myanmar committed genocide against the Rohingya",
            "body": (
                "On Thursday 19 November the International Court of Justice, in The Gambia v. Myanmar, found Myanmar responsible for genocide during the 2017 Rakhine “clearance operations” — the first such ruling against a State. The judgment is final and binding. The court ordered investigation and, where warranted, prosecution; safe, voluntary return; and a report within two years on restitution and compensation. Saturday briefings, including SBS, still carried the ruling."
            ),
            "src": "Sources: UN News, 19 Nov 2026  ·  SBS bulletin, 21 Nov 2026",
            "head_font": "sm",
        },
        {
            "box": (right_x, y + row_h + gap, right_x + col_w, y + row_h + gap + row_h),
            "num": "05",
            "kicker": "ISS TO CALIFORNIA  ·  SCHEDULED, NOT CONFIRMED",
            "color": NAVY,
            "icon": "capsule",
            "head": "Dragon cargo craft is due to splash down on Saturday",
            "body": (
                "The uncrewed SpaceX Dragon undocked from the ISS Harmony module at 12:05 p.m. EST on Friday 20 November. NASA said it is due to splash down off the California coast at approximately 4:55 p.m. EST (1:55 p.m. PST) on Saturday 21 November. NASA will not livestream the splashdown. This poster was compiled on Saturday morning in Asia/Shanghai, before that US afternoon window, so the return is shown as scheduled, not as completed."
            ),
            "src": "Source: NASA ISS blog, 20 Nov 2026, 12:08 p.m.",
            "head_font": "sm",
        },
    ]

    for card in cards:
        x0, y0, x1, y1 = card["box"]
        rounded_rect(d, (x0, y0, x1, y1), 8, CARD, outline=HAIR, width=1)
        d.rectangle((x0, y0, x0 + 7, y1), fill=card["color"])
        cx, cy = x0 + 32, y0 + 28
        if card["icon"] == "link":
            icon_link(d, cx, cy, TEAL, NAVY)
        elif card["icon"] == "talks":
            icon_talks(d, cx, cy, card["color"])
        elif card["icon"] == "scales":
            icon_scales(d, cx, cy, card["color"])
        elif card["icon"] == "capsule":
            icon_capsule(d, cx, cy, card["color"])
        d.text((x0 + 52, y0 + 10), f"{card['num']}   {card['kicker']}", font=f_region, fill=card["color"])
        hf = f_head_sm
        hy, _ = draw_wrapped(d, (x0 + 16, y0 + 44), card["head"], hf, INK, x1 - x0 - 32, leading=22)
        draw_wrapped(d, (x0 + 16, hy + 6), card["body"], f_body, INK, x1 - x0 - 32, leading=17, max_y=y1 - 24)
        d.text((x0 + 16, y1 - 22), card["src"], font=f_src, fill=MUTED)

    # Footer
    fy = H - 58
    d.line((40, fy, W - 40, fy), fill=HAIR, width=1)
    foot = (
        "Original geometry and typography only. Compiled 21 November 2026. "
        "Claims follow the cited outlets; dates are printed on each card. "
        "Not an official publication of Reuters, the EU, the UK, Xinhua, the UN or NASA."
    )
    draw_wrapped(d, (40, fy + 6), foot, f_foot, MUTED, W - 80, leading=14)
    return img


def main() -> None:
    img = render()
    assert img.size == (1024, 1024)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    img.save(PREVIEW, format="PNG", optimize=True)
    size = OUT.stat().st_size
    print(f"wrote {OUT} ({size} bytes, {size/1024:.1f} KiB)")
    print(f"wrote {PREVIEW}")
    if size > 1024 * 1024:
        raise SystemExit(f"PNG too large: {size} bytes")
    # max edge already 1024


if __name__ == "__main__":
    main()
