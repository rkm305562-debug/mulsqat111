#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
يولّد 240 ملصقاً أصلياً (8 حزم x 30 ملصق) بالرسم البرمجي فقط - لا توجد أي صور خارجية.
Generates 240 ORIGINAL stickers (8 packs x 30) purely by code. No external artwork is used.

الاستخدام / Usage:
    pip install pillow      # يحتاج libraqm لعرض العربية بشكل صحيح
    python tools/generate_stickers.py
"""
import itertools
import json
import math
import os
import shutil

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, features

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "app", "src", "main", "assets")
RES = os.path.join(ROOT, "app", "src", "main", "res")
FONT_PATH = os.path.join(ROOT, "tools", "fonts", "DejaVuSans-Bold.ttf")
PREVIEW = os.path.join(ROOT, "docs", "preview.png")

PUBLISHER = "ملصقات عربية"
S = 1024  # drawing canvas; exported at 512
INK = (43, 29, 18, 255)
CX, CY, R = 512, 600, 340  # head geometry on the canvas

if not features.check("raqm"):
    raise SystemExit("Pillow needs libraqm for Arabic text shaping (pip install pillow, or install libraqm).")


def font(size):
    return ImageFont.truetype(FONT_PATH, size, layout_engine=ImageFont.Layout.RAQM)


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# --------------------------------------------------------------------------- helpers
def new_canvas():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def overlay(img, fn):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    img.alpha_composite(layer)


def clip_paste(img, mask_fn, layer_fn):
    mask = Image.new("L", img.size, 0)
    mask_fn(ImageDraw.Draw(mask))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layer_fn(ImageDraw.Draw(layer))
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    img.alpha_composite(layer)


def round_line(d, pts, width, fill=INK):
    d.line(pts, fill=fill, width=width, joint="curve")
    r = width / 2
    for (x, y) in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def arc(d, bbox, a0, a1, width, fill=INK):
    d.arc(bbox, a0, a1, fill=fill, width=width)
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    rx = (bbox[2] - bbox[0]) / 2
    ry = (bbox[3] - bbox[1]) / 2
    r = width / 2
    for a in (a0, a1):
        x = cx + (rx - r) * math.cos(math.radians(a))
        y = cy + (ry - r) * math.sin(math.radians(a))
        d.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def bezier(p0, p1, p2, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return pts


def heart_pts(x, y, s):
    pts = []
    for i in range(0, 361, 6):
        t = math.radians(i)
        px = 16 * math.sin(t) ** 3
        py = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x + px * s / 17, y - py * s / 17 + s * 0.15))
    return pts


def star_pts(x, y, big, small=None, n=5, rot=-90):
    small = small if small is not None else big * 0.45
    pts = []
    for i in range(n * 2):
        rad = big if i % 2 == 0 else small
        a = math.radians(rot + i * 180 / n)
        pts.append((x + rad * math.cos(a), y + rad * math.sin(a)))
    return pts


def drop(d, x, y, s, fill="#59b8ff"):
    d.polygon([(x, y - s * 1.7), (x - s * 0.92, y - s * 0.35), (x + s * 0.92, y - s * 0.35)], fill=fill)
    d.ellipse((x - s, y - s, x + s, y + s), fill=fill)
    d.ellipse((x - s * 0.55, y - s * 0.15, x - s * 0.2, y + s * 0.5), fill=(255, 255, 255, 200))


# --------------------------------------------------------------------------- icons (for text stickers)
def icon(img, kind, x, y, s):
    d = ImageDraw.Draw(img, "RGBA")
    if kind == "heart":
        d.polygon(heart_pts(x, y, s * 1.9), fill="#ff4d6d", outline="#b0002b", width=8)
    elif kind == "star":
        d.polygon(star_pts(x, y, s, s * 0.45), fill="#FFC400", outline="#C28800", width=8)
    elif kind == "sparkle":
        d.polygon(star_pts(x, y, s, s * 0.24, n=4), fill="#FFE066", outline="#E0A800", width=8)
    elif kind == "sun":
        for i in range(8):
            a = math.radians(i * 45)
            d.line((x + math.cos(a) * s * 0.75, y + math.sin(a) * s * 0.75,
                    x + math.cos(a) * s * 1.05, y + math.sin(a) * s * 1.05), fill="#FFB000", width=int(s * 0.16))
        d.ellipse((x - s * 0.55, y - s * 0.55, x + s * 0.55, y + s * 0.55), fill="#FFC400", outline="#E08800", width=8)
    elif kind == "moon":
        def f(dd):
            dd.ellipse((x - s * 0.8, y - s * 0.8, x + s * 0.8, y + s * 0.8), fill=(255, 213, 79, 255))
            dd.ellipse((x - s * 0.2, y - s * 0.95, x + s * 1.2, y + s * 0.65), fill=(0, 0, 0, 0))
        overlay(img, f)
    elif kind == "flower":
        for i in range(6):
            a = math.radians(i * 60)
            px, py = x + math.cos(a) * s * 0.52, y + math.sin(a) * s * 0.52
            d.ellipse((px - s * 0.4, py - s * 0.4, px + s * 0.4, py + s * 0.4), fill="#ff8fb1", outline="#d6336c", width=5)
        d.ellipse((x - s * 0.34, y - s * 0.34, x + s * 0.34, y + s * 0.34), fill="#FFD43B", outline="#E08800", width=5)
    elif kind == "balloon":
        d.line(bezier((x, y + s * 0.75), (x - s * 0.3, y + s * 1.05), (x, y + s * 1.35)), fill="#555555", width=6)
        d.polygon([(x, y + s * 0.62), (x - s * 0.14, y + s * 0.85), (x + s * 0.14, y + s * 0.85)], fill="#d6336c")
        d.ellipse((x - s * 0.62, y - s * 0.85, x + s * 0.62, y + s * 0.75), fill="#ff6b6b", outline="#b02a37", width=7)
        d.ellipse((x - s * 0.38, y - s * 0.6, x - s * 0.16, y - s * 0.2), fill=(255, 255, 255, 190))
    elif kind == "crown":
        k = s / 100.0
        pts = [(-80, 50), (-95, -40), (-45, 0), (0, -60), (45, 0), (95, -40), (80, 50)]
        d.polygon([(x + px * k, y + py * k) for px, py in pts], fill="#FFC400", outline="#B8860B", width=8)
        for jx, col in ((-40, "#e8284b"), (0, "#2f9e44"), (40, "#1c7ed6")):
            d.ellipse((x + jx * k - 11 * k, y + 22 * k - 11 * k, x + jx * k + 11 * k, y + 22 * k + 11 * k), fill=col)
    elif kind == "lightning":
        k = s / 100.0
        pts = [(10, -100), (-50, 10), (-5, 10), (-25, 100), (55, -22), (8, -22), (40, -100)]
        d.polygon([(x + px * k, y + py * k) for px, py in pts], fill="#FFD43B", outline="#E08800", width=8)


# --------------------------------------------------------------------------- characters / faces
CHARS = {
    "face": ("#FFD84D", "#C99A00"),
    "cat": ("#FFA94D", "#C46A00"),
    "bear": ("#B98255", "#7A4A28"),
    "bunny": ("#EADFFB", "#9B82CC"),
}
EYE_Y = CY - 45
EYES_X = (CX - 135, CX + 135)
MX, MY = CX, CY + 150


def draw_eye(d, kind, x, y, side):
    if kind == "dot":
        d.ellipse((x - 26, y - 38, x + 26, y + 38), fill=INK)
        d.ellipse((x - 13, y - 24, x + 1, y - 10), fill="white")
    elif kind in ("big", "scared", "side"):
        d.ellipse((x - 62, y - 70, x + 62, y + 70), fill="white", outline=INK, width=10)
        if kind == "big":
            d.ellipse((x - 28, y - 24, x + 28, y + 40), fill=INK)
            d.ellipse((x - 14, y - 12, x, y + 2), fill="white")
        elif kind == "scared":
            d.ellipse((x - 13, y - 8, x + 13, y + 22), fill=INK)
        else:
            d.ellipse((x + 4, y - 50, x + 54, y + 10), fill=INK)
    elif kind == "happy":
        arc(d, (x - 58, y - 40, x + 58, y + 76), 200, 340, 20)
    elif kind == "closed":
        arc(d, (x - 58, y - 76, x + 58, y + 40), 20, 160, 20)
    elif kind == "sleepy":
        round_line(d, [(x - 55, y), (x + 55, y)], 18)
    elif kind == "squint":
        if side < 0:
            round_line(d, [(x - 45, y - 42), (x + 40, y), (x - 45, y + 42)], 18)
        else:
            round_line(d, [(x + 45, y - 42), (x - 40, y), (x + 45, y + 42)], 18)
    elif kind == "x":
        round_line(d, [(x - 40, y - 40), (x + 40, y + 40)], 18)
        round_line(d, [(x - 40, y + 40), (x + 40, y - 40)], 18)
    elif kind == "star":
        d.polygon(star_pts(x, y, 70, 30), fill="#FFC400", outline="#C77700", width=6)
    elif kind == "heart":
        d.polygon(heart_pts(x, y - 5, 85), fill="#e8284b", outline="#9c0f2c", width=5)


def draw_brow(d, kind, x, y, side):
    by = y - 85
    if kind == "angry":
        round_line(d, [(x - 58, by + 15 * side), (x + 58, by - 15 * side)], 20)
    elif kind == "sad":
        round_line(d, [(x - 58, by - 15 * side), (x + 58, by + 15 * side)], 20)
    elif kind == "up":
        arc(d, (x - 60, y - 160, x + 60, y - 70), 200, 340, 18)
    elif kind == "flat":
        round_line(d, [(x - 55, by), (x + 55, by)], 20)


DARK_RED = "#7a1e1e"


def draw_mouth(img, d, kind):
    mx, my = MX, MY
    if kind == "smile":
        arc(d, (mx - 110, my - 90, mx + 110, my + 60), 15, 165, 20)
    elif kind == "smile_small":
        arc(d, (mx - 60, my - 40, mx + 60, my + 30), 20, 160, 18)
    elif kind in ("grin", "open"):
        big = kind == "open"
        bbox = (mx - 160, my - 120, mx + 160, my + 110) if big else (mx - 135, my - 115, mx + 135, my + 95)
        cyc = (bbox[1] + bbox[3]) / 2
        teeth = 44 if big else 34

        def layer(l):
            l.rectangle(bbox, fill=DARK_RED)
            l.rectangle((bbox[0], cyc, bbox[2], cyc + teeth), fill="white")
            l.ellipse((mx - 75, cyc + 55, mx + 75, cyc + 150), fill="#ff6f8a")

        clip_paste(img, lambda m: m.chord(bbox, 0, 180, fill=255), layer)
        d.chord(bbox, 0, 180, outline=INK, width=12)
    elif kind == "wail":
        bbox = (mx - 120, my - 60, mx + 120, my + 200)
        cyc = (bbox[1] + bbox[3]) / 2

        def layer(l):
            l.rectangle(bbox, fill=DARK_RED)
            l.ellipse((mx - 62, cyc - 50, mx + 62, cyc + 40), fill="#ff6f8a")

        clip_paste(img, lambda m: m.chord(bbox, 180, 360, fill=255), layer)
        d.chord(bbox, 180, 360, outline=INK, width=12)
    elif kind == "o":
        d.ellipse((mx - 45, my - 35, mx + 45, my + 65), fill=DARK_RED, outline=INK, width=10)
    elif kind == "pucker":
        d.ellipse((mx - 30, my - 20, mx + 30, my + 40), fill="#e0605a", outline=INK, width=8)
    elif kind == "flat":
        round_line(d, [(mx - 60, my), (mx + 60, my)], 18)
    elif kind == "sad":
        arc(d, (mx - 90, my - 10, mx + 90, my + 110), 200, 340, 20)
    elif kind == "tongue":
        d.rounded_rectangle((mx - 45, my + 30, mx + 45, my + 135), radius=40, fill="#ff7a90", outline=INK, width=8)
        d.line((mx, my + 50, mx, my + 95), fill="#d6455f", width=6)
        arc(d, (mx - 110, my - 90, mx + 110, my + 60), 15, 165, 20)
    elif kind == "wavy":
        pts = [(mx - 95 + i * 7, my + 14 * math.sin(i * 0.7)) for i in range(28)]
        round_line(d, pts, 16)
    elif kind == "grimace":
        d.rounded_rectangle((mx - 110, my - 40, mx + 110, my + 50), radius=25, fill="white", outline=INK, width=12)
        for lx in (-55, 0, 55):
            d.line((mx + lx, my - 38, mx + lx, my + 48), fill=INK, width=7)
        d.line((mx - 108, my + 5, mx + 108, my + 5), fill=INK, width=7)
    elif kind == "smirk":
        round_line(d, bezier((mx - 85, my + 10), (mx + 10, my + 70), (mx + 95, my - 25)), 18)


def extra(img, name):
    d = ImageDraw.Draw(img, "RGBA")
    if name in ("blush", "blush2"):
        a = 150 if name == "blush" else 205

        def f(dd):
            for sx in (-1, 1):
                x, y = CX + sx * 235, CY + 60
                dd.ellipse((x - 62, y - 36, x + 62, y + 36), fill=(255, 92, 120, a))
        overlay(img, f)
    elif name == "sweat":
        drop(d, 900, 400, 40)
    elif name == "tears":
        for sx in (-1, 1):
            drop(d, CX + sx * 300, CY - 10, 34)
            drop(d, CX + sx * 330, CY + 95, 26)
    elif name == "streams":
        for x in EYES_X:
            d.rounded_rectangle((x - 24, EYE_Y + 20, x + 24, EYE_Y + 270), radius=24, fill="#6ec1ff")
            d.rounded_rectangle((x - 14, EYE_Y + 40, x - 4, EYE_Y + 200), radius=5, fill=(255, 255, 255, 170))
    elif name == "glasses":
        dark = (20, 20, 24, 255)
        for x in EYES_X:
            d.rounded_rectangle((x - 95, EYE_Y - 60, x + 95, EYE_Y + 70), radius=45, fill=dark)
            d.line((x - 60, EYE_Y - 28, x - 25, EYE_Y - 28), fill=(255, 255, 255, 170), width=10)
        d.rectangle((CX - 45, EYE_Y - 30, CX + 45, EYE_Y - 10), fill=dark)
        d.line((CX - 228, EYE_Y - 25, CX - 305, EYE_Y - 45), fill=dark, width=18)
        d.line((CX + 228, EYE_Y - 25, CX + 305, EYE_Y - 45), fill=dark, width=18)
    elif name in ("hearts", "hearts2"):
        spots = [(95, 360, 55, "#ff4d6d"), (915, 320, 60, "#ff8fa3"), (925, 500, 42, "#ff4d6d")]
        if name == "hearts2":
            spots += [(90, 540, 38, "#ff8fa3"), (930, 170, 36, "#ff4d6d")]
        for x, y, s, c in spots:
            d.polygon(heart_pts(x, y, s * 1.7), fill=c, outline="#b0002b", width=5)
    elif name == "zzz":
        for (x, y, sz) in ((885, 350, 120), (935, 240, 95), (965, 140, 70)):
            d.text((x, y), "Z", font=font(sz), fill="#4a78d0", anchor="mm", stroke_width=4, stroke_fill="white")
    elif name == "anger":
        x, y = 905, 330
        for dx, dy, a0, a1 in ((-1, -1, 0, 90), (1, -1, 90, 180), (-1, 1, 270, 360), (1, 1, 180, 270)):
            cx, cy = x + dx * 46, y + dy * 46
            d.arc((cx - 44, cy - 44, cx + 44, cy + 44), a0, a1, fill="#e03131", width=20)
    elif name == "sparkles":
        for x, y, s in ((105, 300, 62), (925, 250, 75), (900, 560, 48), (110, 580, 45)):
            d.polygon(star_pts(x, y, s, s * 0.24, n=4), fill="#FFE066", outline="#E0A800", width=5)
    elif name == "hat":
        d.polygon([(CX - 150, CY - 300), (CX + 150, CY - 300), (CX + 30, CY - 545)], fill="#7c4dff", outline="#4527a0", width=10)
        for (x, y, r) in ((CX - 40, CY - 340, 16), (CX + 40, CY - 345, 16), (CX + 5, CY - 430, 14)):
            d.ellipse((x - r, y - r, x + r, y + r), fill="#ffd43b")
        d.ellipse((CX + 4, CY - 575, CX + 56, CY - 523), fill="#ffd43b", outline="#E08800", width=6)
    elif name == "crown":
        k = 1.45
        icon(img, "crown", CX, CY - 380, 100 * k)
    elif name == "halo":
        d.ellipse((CX - 135, CY - 440, CX + 135, CY - 350), outline="#FFC400", width=24)
    elif name == "question":
        d.text((900, 300), "?", font=font(260), fill="#4a78d0", anchor="mm", stroke_width=6, stroke_fill="white")
    elif name == "exclaim":
        d.text((900, 310), "!", font=font(280), fill="#e03131", anchor="mm", stroke_width=6, stroke_fill="white")
    elif name == "music":
        d.text((890, 300), "\u266a", font=font(190), fill="#7048e8", anchor="mm", stroke_width=5, stroke_fill="white")
        d.text((940, 480), "\u266b", font=font(140), fill="#e64980", anchor="mm", stroke_width=5, stroke_fill="white")
    elif name == "mask":
        d.rounded_rectangle((CX - 200, CY + 40, CX + 200, CY + 270), radius=60, fill="#cfeaf6", outline="#6aa3bd", width=10)
        for ly in (110, 160, 210):
            d.line((CX - 140, CY + ly, CX + 140, CY + ly), fill="#9cc7da", width=7)


def draw_character(spec, char):
    img = new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    fill, outline = CHARS[char]
    if spec.get("tint"):
        f = hex2rgb(fill)
        t = spec["tint"]
        fill = "#%02x%02x%02x" % tuple(int(f[i] * 0.35 + t[i] * 0.65) for i in range(3))
    # ears (behind the head)
    if char == "cat":
        d.polygon([(CX - 325, CY - 110), (CX - 300, CY - 430), (CX - 60, CY - 305)], fill=fill, outline=outline, width=12)
        d.polygon([(CX + 325, CY - 110), (CX + 300, CY - 430), (CX + 60, CY - 305)], fill=fill, outline=outline, width=12)
        d.polygon([(CX - 275, CY - 200), (CX - 268, CY - 350), (CX - 150, CY - 290)], fill="#ffb3c1")
        d.polygon([(CX + 275, CY - 200), (CX + 268, CY - 350), (CX + 150, CY - 290)], fill="#ffb3c1")
    elif char == "bunny":
        for sx in (-1, 1):
            x = CX + sx * 130
            d.ellipse((x - 85, 10, x + 85, 410), fill=fill, outline=outline, width=12)
            d.ellipse((x - 42, 75, x + 42, 360), fill="#ffc2d4")
    elif char == "bear":
        for sx in (-1, 1):
            x, y = CX + sx * 250, CY - 285
            d.ellipse((x - 105, y - 105, x + 105, y + 105), fill=fill, outline=outline, width=12)
            d.ellipse((x - 55, y - 55, x + 55, y + 55), fill="#e8cba6")
    # head
    d.ellipse((CX - R, CY - R, CX + R, CY + R), fill=fill, outline=outline, width=14)
    d.ellipse((CX - 250, CY - 290, CX - 110, CY - 220), fill=(255, 255, 255, 60))
    if char == "cat":
        d.polygon([(CX - 30, CY + 40), (CX + 30, CY + 40), (CX, CY + 80)], fill="#ff8fa3", outline=INK, width=6)
        for sx in (-1, 1):
            for i in range(3):
                d.line((CX + sx * 170, CY + 70 + i * 28, CX + sx * 330, CY + 40 + i * 52), fill=(60, 40, 25, 255), width=7)
    elif char == "bunny":
        d.ellipse((CX - 30, CY + 35, CX + 30, CY + 78), fill="#ff8fa3", outline=INK, width=5)
        d.rounded_rectangle((CX - 32, CY + 88, CX + 32, CY + 132), radius=10, fill="white", outline=INK, width=5)
        d.line((CX, CY + 90, CX, CY + 130), fill=INK, width=4)
    elif char == "bear":
        d.ellipse((CX - 150, CY + 20, CX + 150, CY + 300), fill="#e8cba6", outline=outline, width=8)
        d.ellipse((CX - 42, CY + 30, CX + 42, CY + 88), fill=INK)
    # cheeks / eyes / brows / mouth / extras
    for name in spec["ex"]:
        if name in ("blush", "blush2"):
            extra(img, name)
    d = ImageDraw.Draw(img, "RGBA")
    eyes = spec["eyes"]
    eyes = eyes if isinstance(eyes, tuple) else (eyes, eyes)
    for i, x in enumerate(EYES_X):
        draw_eye(d, eyes[i], x, EYE_Y, -1 if i == 0 else 1)
    brows = spec.get("brows")
    if brows:
        brows = brows if isinstance(brows, tuple) else (brows, brows)
        for i, x in enumerate(EYES_X):
            draw_brow(d, brows[i], x, EYE_Y, -1 if i == 0 else 1)
    if spec.get("mouth"):
        draw_mouth(img, d, spec["mouth"])
    for name in spec["ex"]:
        if name not in ("blush", "blush2"):
            extra(img, name)
    return img


# --------------------------------------------------------------------------- text stickers
PALETTES = [
    ("#FFE08A", "#D49A00", "#4a2f00"),
    ("#9BE3C4", "#2E9E78", "#0b3d2b"),
    ("#FFB3C7", "#D8456F", "#5c0f2a"),
    ("#A9D4FF", "#3a82d6", "#0d2c57"),
    ("#D7C2FF", "#7b4fd6", "#2b1160"),
    ("#FFC59A", "#E0711c", "#5a2500"),
    ("#2e7d6b", "#14513f", "#ffffff"),
    ("#3f51b5", "#232f80", "#ffffff"),
    ("#d6336c", "#8e1b47", "#ffffff"),
]


def fit_text(text, W, H, max_lines=3, max_size=210, min_size=60):
    words = text.split()
    for size in range(max_size, min_size - 1, -6):
        f = font(size)
        lh = int(size * 1.4)
        for n in range(1, min(max_lines, len(words)) + 1):
            if n * lh > H:
                break
            best = None
            for cuts in itertools.combinations(range(1, len(words)), n - 1):
                parts, prev = [], 0
                for c in list(cuts) + [len(words)]:
                    parts.append(" ".join(words[prev:c]))
                    prev = c
                w = max(f.getlength(p, direction="rtl", language="ar") for p in parts)
                if w <= W and (best is None or w < best[0]):
                    best = (w, parts)
            if best:
                return f, best[1], lh
    f = font(min_size)
    return f, words, int(min_size * 1.4)


def draw_text_block(img, text, cx, cy, W, H, color, max_lines=3):
    d = ImageDraw.Draw(img)
    f, parts, lh = fit_text(text, W, H, max_lines)
    total = lh * len(parts)
    y = cy - total / 2 + lh / 2
    for p in parts:
        d.text((cx, y), p, font=f, fill=color, anchor="mm", direction="rtl", language="ar")
        y += lh


def text_sticker(text, idx, pack_idx, icons):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    fill, outline, tcol = PALETTES[(idx * 5 + pack_idx * 2) % len(PALETTES)]
    style = ("bubble", "circle", "burst", "banner")[(idx + pack_idx) % 4]
    flip = idx % 2 == 1
    if style == "bubble":
        base = 300 if not flip else 724
        sx = 1 if not flip else -1
        d.polygon([(base, 780), (base - 40 * sx, 930), (base + 150 * sx, 790)], fill=fill, outline=outline, width=14)
        d.rounded_rectangle((70, 300, 954, 800), radius=150, fill=fill, outline=outline, width=16)
        d.polygon([(base + 10 * sx, 784), (base + 130 * sx, 784), (base - 25 * sx, 905)], fill=fill)
        cx, cy, W, H, ml = 512, 550, 730, 400, 3
    elif style == "circle":
        d.ellipse((162, 240, 862, 940), fill=fill, outline=outline, width=18)
        d.ellipse((200, 278, 824, 902), outline=(255, 255, 255, 140), width=6)
        cx, cy, W, H, ml = 512, 590, 500, 380, 3
    elif style == "burst":
        d.polygon(star_pts(512, 610, 420, 350, n=14), fill=fill, outline=outline, width=16)
        cx, cy, W, H, ml = 512, 610, 560, 400, 3
    else:
        d.polygon([(40, 400), (170, 400), (170, 760), (40, 760), (110, 580)], fill=outline, outline=outline, width=6)
        d.polygon([(984, 400), (854, 400), (854, 760), (984, 760), (914, 580)], fill=outline, outline=outline, width=6)
        d.rounded_rectangle((110, 340, 914, 820), radius=40, fill=fill, outline=outline, width=16)
        cx, cy, W, H, ml = 512, 580, 690, 400, 3
    draw_text_block(img, text, cx, cy, W, H, tcol, ml)
    icon(img, icons[idx % len(icons)], 180, 165, 80)
    icon(img, icons[(idx + 1) % len(icons)], 850, 165, 70)
    return img



# --------------------------------------------------------------------------- talking characters (body + speech bubble)
BX = 360  # body centre x in the composite
BELLY = {"bunny": "#ffffff", "cat": "#ffe3bf", "face": "#fff2b0", "bear": "#e8cba6"}
BUBBLE = {"bunny": ("#9B82CC", "#3b2a63"), "cat": ("#C46A00", "#5a2500"), "bear": ("#7A4A28", "#4a2a12")}
MOODS = {
    "wave": dict(eyes="dot", mouth="grin", ex=[], pose="wave"),
    "happy": dict(eyes="happy", mouth="smile", ex=["blush"], pose="wave"),
    "smile": dict(eyes="dot", mouth="smile", ex=[], pose="down"),
    "love": dict(eyes="heart", mouth="smile", ex=[], pose="cheer", deco="love"),
    "sleepy": dict(eyes="sleepy", mouth="o", ex=[], pose="down", deco="sleepy"),
    "sad": dict(eyes="dot", brows="sad", mouth="sad", ex=[], pose="down"),
    "cry": dict(eyes="squint", mouth="wail", ex=["streams"], pose="down"),
    "laugh": dict(eyes="squint", mouth="open", ex=[], pose="cheer"),
    "party": dict(eyes="happy", mouth="grin", ex=[], pose="cheer", deco="party"),
    "cool": dict(eyes="dot", mouth="smirk", ex=["glasses"], pose="point"),
    "think": dict(eyes="side", brows=("flat", "up"), mouth="flat", ex=[], pose="down"),
    "shock": dict(eyes="big", brows="up", mouth="o", ex=[], pose="out"),
    "no": dict(eyes="dot", brows="angry", mouth="grimace", ex=[], pose="out"),
    "shy": dict(eyes="closed", mouth="smile_small", ex=["blush2"], pose="down"),
    "star": dict(eyes="star", mouth="open", ex=[], pose="cheer", deco="party"),
    "tongue": dict(eyes=("dot", "happy"), mouth="tongue", ex=[], pose="wave"),
    "tired": dict(eyes="sleepy", brows="sad", mouth="wavy", ex=[], pose="down"),
    "pray": dict(eyes="closed", mouth="smile", ex=[], pose="pray"),
    "ask": dict(eyes="big", brows="up", mouth="smile_small", ex=[], pose="pray"),
    "run": dict(eyes="dot", mouth="open", ex=[], pose="point"),
    "yum": dict(eyes="happy", mouth="tongue", ex=["blush"], pose="down"),
    "ok": dict(eyes="happy", mouth="smile", ex=[], pose="point"),
    "point": dict(eyes="dot", brows="up", mouth="smile_small", ex=[], pose="point"),
}
POSES = {
    "down": ([(-135, 790), (-185, 930)], [(135, 790), (185, 930)]),
    "wave": ([(-135, 790), (-185, 930)], [(135, 800), (230, 780), (290, 620)]),
    "cheer": ([(-135, 800), (-230, 740), (-250, 590)], [(135, 800), (230, 740), (250, 590)]),
    "out": ([(-135, 800), (-250, 850), (-310, 880)], [(135, 800), (250, 850), (310, 880)]),
    "point": ([(-135, 790), (-185, 930)], [(135, 800), (240, 740), (340, 700)]),
    "pray": ([(-135, 800), (-70, 870), (-10, 830)], [(135, 800), (70, 870), (10, 830)]),
}


def draw_body(img, char, pose):
    d = ImageDraw.Draw(img, "RGBA")
    fill, outline = CHARS[char]
    # tail
    if char == "cat":
        pts = bezier((BX + 150, 930), (BX + 330, 900), (BX + 300, 740), 30)
        round_line(d, pts, 52, outline)
        round_line(d, pts, 34, fill)
    else:
        d.ellipse((BX - 215, 880, BX - 135, 960), fill=("white" if char == "bunny" else fill), outline=outline, width=8)
    # feet
    for sx in (-1, 1):
        d.ellipse((BX + sx * 80 - 70, 945, BX + sx * 80 + 70, 1012), fill=fill, outline=outline, width=10)
    # body
    d.ellipse((BX - 170, 700, BX + 170, 990), fill=fill, outline=outline, width=14)
    d.ellipse((BX - 105, 780, BX + 105, 960), fill=BELLY[char])
    # arms
    left, right = POSES[pose]
    for arm in (left, right):
        pts = [(BX + x, y) for x, y in arm]
        round_line(d, pts, 78, outline)
        round_line(d, pts, 54, fill)
        hx, hy = pts[-1]
        d.ellipse((hx - 42, hy - 42, hx + 42, hy + 42), fill=fill, outline=outline, width=10)


def talk_sticker(phrase, mood, char):
    spec = dict(MOODS[mood])
    spec.setdefault("brows", None)
    img = new_canvas()
    d = ImageDraw.Draw(img, "RGBA")
    stroke, tcol = BUBBLE[char]
    deco = spec.get("deco")
    if deco == "party":
        icon(img, "balloon", 90, 200, 75)
        icon(img, "sparkle", 200, 95, 50)
    elif deco == "love":
        icon(img, "heart", 90, 230, 60)
        icon(img, "heart", 190, 110, 40)
    elif deco == "sleepy":
        icon(img, "moon", 100, 190, 70)
        icon(img, "sparkle", 200, 100, 40)
    draw_body(img, char, spec["pose"])
    head = draw_character(spec, char)
    k = 0.647
    hs = head.resize((round(S * k), round(S * k)), Image.LANCZOS)
    img.alpha_composite(hs, (round(BX - 512 * k), round(560 - 600 * k)))
    d = ImageDraw.Draw(img, "RGBA")
    d.polygon([(610, 325), (700, 325), (625, 440)], fill="white", outline=stroke, width=12)
    d.rounded_rectangle((560, 40, 1000, 340), radius=100, fill="white", outline=stroke, width=14)
    d.polygon([(622, 322), (688, 322), (628, 410)], fill="white")
    draw_text_block(img, phrase, 780, 190, 360, 230, tcol, 3)
    return img

# --------------------------------------------------------------------------- finishing
def finalize(img1024):
    box = img1024.getchannel("A").getbbox()
    crop = img1024.crop(box)
    target = 468
    k = target / max(crop.size)
    crop = crop.resize((max(1, round(crop.width * k)), max(1, round(crop.height * k))), Image.LANCZOS)
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    img.alpha_composite(crop, ((512 - crop.width) // 2, (512 - crop.height) // 2))
    alpha = img.getchannel("A")
    ring = alpha.filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(2.5)).point(lambda v: 255 if v > 70 else 0)
    ring = ring.filter(ImageFilter.GaussianBlur(0.8))
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white.putalpha(ring)
    return Image.alpha_composite(white, img)


def save_webp(img, path):
    for q in (82, 74, 66, 58, 50):
        img.save(path, "WEBP", quality=q, method=3)
        if os.path.getsize(path) <= 95 * 1024:
            return
    raise RuntimeError("sticker too large: " + path)


# --------------------------------------------------------------------------- content
EXPRESSIONS = [
    dict(n="سعيد", em=["😊"], eyes="happy", mouth="smile", ex=["blush"]),
    dict(n="ضحك", em=["😂"], eyes="squint", mouth="open", ex=["tears"]),
    dict(n="ابتسامة كبيرة", em=["😀"], eyes="dot", mouth="grin", ex=[]),
    dict(n="غمزة", em=["😉"], eyes=("dot", "happy"), mouth="smirk", ex=[]),
    dict(n="حب", em=["😍"], eyes="heart", mouth="smile", ex=["hearts"]),
    dict(n="قبلة", em=["😘"], eyes=("dot", "happy"), mouth="pucker", ex=["hearts"]),
    dict(n="نجمة", em=["🤩"], eyes="star", mouth="open", ex=["sparkles"]),
    dict(n="رائع", em=["😎"], eyes="dot", mouth="smirk", ex=["glasses"]),
    dict(n="حزين", em=["😞"], eyes="dot", brows="sad", mouth="sad", ex=[]),
    dict(n="بكاء", em=["😭"], eyes="squint", mouth="wail", ex=["streams"]),
    dict(n="غاضب", em=["😡"], eyes="dot", brows="angry", mouth="grimace", ex=["anger"], tint=(255, 110, 85)),
    dict(n="نعسان", em=["😴"], eyes="sleepy", mouth="o", ex=["zzz"]),
    dict(n="متفاجئ", em=["😮"], eyes="big", brows="up", mouth="o", ex=[]),
    dict(n="تفكير", em=["🤔"], eyes="side", brows=("flat", "up"), mouth="flat", ex=["question"]),
    dict(n="خجول", em=["😳"], eyes="dot", mouth="smile_small", ex=["blush2"]),
    dict(n="مريض", em=["😷"], eyes="sleepy", brows="sad", mouth=None, ex=["mask"], tint=(190, 220, 140)),
    dict(n="خائف", em=["😨"], eyes="scared", brows="sad", mouth="wavy", ex=["sweat"]),
    dict(n="دوخة", em=["😵"], eyes="x", mouth="wavy", ex=[]),
    dict(n="لسان", em=["😜"], eyes=("dot", "happy"), mouth="tongue", ex=[]),
    dict(n="احتفال", em=["🥳"], eyes="happy", mouth="grin", ex=["hat", "sparkles"]),
    dict(n="ملك", em=["👑"], eyes="dot", mouth="smile", ex=["crown"]),
    dict(n="لذيذ", em=["😋"], eyes="happy", mouth="tongue", ex=["blush"]),
    dict(n="توتر", em=["😅"], eyes="side", brows="sad", mouth="grimace", ex=["sweat"]),
    dict(n="ملل", em=["😑"], eyes="sleepy", mouth="flat", ex=[]),
    dict(n="شك", em=["🤨"], eyes="dot", brows=("flat", "up"), mouth="smirk", ex=[]),
    dict(n="صدمة", em=["😱"], eyes="big", brows="up", mouth="wail", ex=["exclaim"]),
    dict(n="موسيقى", em=["🎵"], eyes="happy", mouth="smile", ex=["music"]),
    dict(n="حنان", em=["🥰"], eyes="closed", mouth="smile", ex=["blush", "hearts2"]),
    dict(n="حزن هادئ", em=["😔"], eyes="sleepy", brows="sad", mouth="sad", ex=[]),
    dict(n="دعاء", em=["😇"], eyes="closed", mouth="smile", ex=["halo", "sparkles"]),
]

TEXT_PACKS = {
    "greetings": ("تحيات وصباحيات", ["sun", "flower", "sparkle", "moon"], [
        ("صباح الخير", "☀️"), ("مساء الخير", "🌆"), ("صباح النور", "🌞"), ("مساء النور", "🌇"),
        ("تصبح على خير", "🌙"), ("أحلام سعيدة", "😴"), ("السلام عليكم", "👋"), ("وعليكم السلام", "🤝"),
        ("مرحباً", "👋"), ("أهلاً وسهلاً", "🤗"), ("يا هلا والله", "🤗"), ("حياك الله", "🌹"),
        ("نورت", "💡"), ("منور", "🌟"), ("كيف حالك؟", "🙂"), ("الحمد لله بخير", "😊"),
        ("وينك؟", "🤔"), ("صباحك عسل", "🍯"), ("مع السلامة", "👋"), ("في أمان الله", "🙏"),
        ("إلى اللقاء", "👋"), ("يومك سعيد", "🌞"), ("جمعة مباركة", "🕌"), ("كل عام وأنتم بخير", "🎉"),
        ("عيد مبارك", "🌙"), ("رمضان كريم", "🌙"), ("تقبل الله طاعتكم", "🤲"), ("أسعد الله صباحك", "☕"),
        ("طابت أوقاتكم", "🌷"), ("يومك جميل", "🌸"),
    ]),
    "love_feelings": ("حب ومشاعر", ["heart", "sparkle", "heart", "star"], [
        ("أحبك", "❤️"), ("قلبي", "💖"), ("عمري", "💞"), ("حبيبي", "😍"),
        ("حبيبتي", "😘"), ("يا قمر", "🌙"), ("وحشتني", "💔"), ("اشتقت إليك", "💕"),
        ("أنت الأجمل", "✨"), ("أحبك كثيراً", "❤️"), ("أنا معك", "🤝"), ("فداك روحي", "💝"),
        ("ما أحلاك", "😍"), ("تسلم", "🌹"), ("يا عيوني", "👀"), ("قمر الزمان", "🌕"),
        ("أنت حياتي", "💘"), ("لا تتركني", "🥺"), ("أفتقدك", "💔"), ("أنت أحلى ما عندي", "🎁"),
        ("روحي", "💗"), ("نبض قلبي", "💓"), ("صديقي الغالي", "🤗"), ("أخي الحبيب", "💪"),
        ("أختي الغالية", "🌸"), ("أمي حبيبتي", "👩"), ("أبي قدوتي", "👨"), ("شكراً لوجودك", "🙏"),
        ("أنت نور حياتي", "💡"), ("كل الحب لك", "💌"),
    ]),
    "quick_replies": ("ردود سريعة", ["star", "sparkle", "lightning", "star"], [
        ("تمام", "👍"), ("ماشي", "👌"), ("أكيد", "✅"), ("طبعاً", "💯"),
        ("لا", "❌"), ("مستحيل", "🚫"), ("ربما", "🤷"), ("ما أدري", "🤷"),
        ("إن شاء الله", "🤲"), ("يا سلام", "😮"), ("رائع", "👏"), ("ممتاز", "⭐"),
        ("هههههه", "😂"), ("لا تقول", "😱"), ("صح؟", "🤔"), ("بالضبط", "🎯"),
        ("معك حق", "👍"), ("أنا موافق", "✔️"), ("ما عندي مانع", "😉"), ("فكرة حلوة", "💡"),
        ("لحظة من فضلك", "⏳"), ("دقيقة", "⏱️"), ("ثواني", "⏰"), ("أنا قادم", "🏃"),
        ("في الطريق", "🚗"), ("وصلت", "📍"), ("خلاص", "🙌"), ("على راحتك", "😌"),
        ("سأخبرك لاحقاً", "📱"), ("كلمني", "☎️"),
    ]),
    "duaa_blessing": ("دعاء وبركة", ["moon", "star", "sparkle", "flower"], [
        ("ما شاء الله", "✨"), ("بارك الله فيك", "🌹"), ("جزاك الله خيراً", "🤲"), ("الحمد لله", "🙏"),
        ("سبحان الله", "🌙"), ("الله أكبر", "🕌"), ("لا حول ولا قوة إلا بالله", "🤲"), ("أستغفر الله", "🤲"),
        ("بإذن الله", "🌟"), ("الله يعطيك العافية", "💪"), ("الله يحفظك", "🛡️"), ("الله يسلمك", "💚"),
        ("الله يبارك لك", "🎁"), ("توكلنا على الله", "🌿"), ("حسبي الله ونعم الوكيل", "🤲"), ("رزقك الله", "✨"),
        ("تقبل الله منا ومنكم", "🤲"), ("اللهم آمين", "🤲"), ("الله المستعان", "🙏"), ("إن شاء الله خير", "🌱"),
        ("الله يرحمه", "🕊️"), ("شفاك الله", "🌿"), ("الله يهديك", "🌟"), ("الله يوفقك", "🌟"),
        ("ما شاء الله تبارك الله", "✨"), ("ألف الحمد لله", "🙏"), ("يا رب", "🤲"), ("صبراً جميلاً", "🌿"),
        ("ربي يحفظكم", "🛡️"), ("اللهم بارك", "🌙"),
    ]),
    "occasions": ("مناسبات ومواقف", ["balloon", "crown", "star", "sparkle"], [
        ("مبروك", "🎉"), ("ألف مبروك", "🎊"), ("تهانينا", "🥳"), ("عقبال عندك", "🎁"),
        ("بالتوفيق", "🍀"), ("بالرفاه والبنين", "💍"), ("مبروك النجاح", "🎓"), ("مبروك الوظيفة", "💼"),
        ("مبروك المولود", "👶"), ("عيد ميلاد سعيد", "🎂"), ("سنة حلوة يا جميل", "🎈"), ("شكراً", "🙏"),
        ("شكراً جزيلاً", "🌹"), ("عفواً", "😊"), ("لا شكر على واجب", "🤝"), ("آسف", "🙏"),
        ("سامحني", "🥺"), ("لا تزعل", "🤗"), ("صباح الإنجاز", "💪"), ("تعبان", "😩"),
        ("جوعان", "🍔"), ("نعسان", "😴"), ("مشغول", "💻"), ("ما في مشكلة", "👌"),
        ("لا تقلق", "😌"), ("خلها علي", "😎"), ("عندي اجتماع", "📅"), ("أنا بخير", "😊"),
        ("حظ سعيد", "🍀"), ("يعطيك العافية", "👏"),
    ]),
    "gulf_dialect": ("لهجة خليجية", ["star", "sparkle", "moon", "flower"], [
        ("وش الأخبار؟", "🗞️"), ("أبشر", "👍"), ("سم طال عمرك", "🙏"), ("تامر أمر", "😎"),
        ("ما عليك زود", "👌"), ("زين", "👍"), ("حيا الله من جانا", "🤗"), ("شلونك؟", "🙂"),
        ("الله يسلمك", "🤝"), ("يا شيخ", "😮"), ("وايد حلو", "😍"), ("مب مشكلة", "👌"),
        ("خلنا نطلع", "🚗"), ("على كيفك", "😌"), ("عساك على القوة", "💪"), ("ما قصرت", "🌹"),
        ("يعطيك العافية يا غالي", "🤝"), ("الله يخليك", "🙏"), ("تسلم يدينك", "👏"), ("ما يخالف", "✅"),
        ("لا تشيل هم", "😌"), ("هلا والله", "👋"), ("يا حبيبي", "❤️"), ("صح لسانك", "👍"),
        ("أنا جاي", "🏃"), ("وين رايح؟", "🚗"), ("بشرني عنك", "🗣️"), ("طيب", "👌"),
        ("وش رايك؟", "🤔"), ("الحمد لله على السلامة", "🤗"),
    ]),
    "levant_egypt": ("لهجات شامية ومصرية", ["sparkle", "heart", "star", "sun"], [
        ("إزيك؟", "🙂"), ("عامل إيه؟", "😊"), ("كيفك؟", "👋"), ("شو الأخبار؟", "🗞️"),
        ("يا عم", "😮"), ("ولا يهمك", "👌"), ("على عيني", "👁️"), ("يا زلمة", "😎"),
        ("دير بالك", "🛡️"), ("يلا بينا", "🏃"), ("تمام التمام", "👍"), ("حبيبي يا غالي", "❤️"),
        ("مية مية", "💯"), ("ما فيش مشكلة", "✅"), ("ولا إيه؟", "🤔"), ("خلاص كده", "🙌"),
        ("استنى شوية", "⏳"), ("أنا جاي", "🏃"), ("معلش", "🤗"), ("يا ساتر", "😱"),
        ("ما تقلقش", "😌"), ("تسلم إيدك", "👏"), ("يا رب سترك", "🤲"), ("عاش", "👏"),
        ("حقك علي", "🙏"), ("شكراً يا قمر", "🌙"), ("قلبي معاك", "💞"), ("ولا يهمك حبيبي", "🤝"),
        ("أهلين", "👋"), ("يسلمو", "🌹"),
    ]),
    "daily_life": ("يوميات وأكل", ["flower", "sun", "sparkle", "star"], [
        ("صباح القهوة", "☕"), ("وقت الشاي", "🍵"), ("جوعان جداً", "🍔"), ("الفطور جاهز", "🍳"),
        ("الغداء جاهز", "🍛"), ("العشاء جاهز", "🍽️"), ("صحتين وعافية", "😋"), ("حلويات", "🍰"),
        ("ما أطيب", "😋"), ("عطشان", "🥤"), ("نعسان جداً", "😴"), ("قيلولة", "🛌"),
        ("في السوق", "🛒"), ("في البيت", "🏠"), ("في العمل", "💼"), ("في المشوار", "🚗"),
        ("الجو حار", "☀️"), ("الجو بارد", "🥶"), ("أمطرت", "🌧️"), ("سفر سعيد", "✈️"),
        ("رحلة موفقة", "🧳"), ("وصلنا بالسلامة", "🛬"), ("ليلة هادئة", "🌃"), ("سهرة جميلة", "🌙"),
        ("نهاركم سعيد", "🌤️"), ("خذ راحتك", "🛋️"), ("يلا نتعشى", "🍕"), ("قهوة؟", "☕"),
        ("أحبكم", "🥰"), ("يوم رائع", "🌈"),
    ]),
    "work_study": ("دراسة وعمل", ["lightning", "star", "sparkle", "crown"], [
        ("اجتماع الآن", "📅"), ("مشغول حالياً", "💻"), ("سأعاود الاتصال", "📞"), ("تم الإنجاز", "✅"),
        ("قيد العمل", "🛠️"), ("في انتظار الرد", "⏳"), ("شكراً على جهودكم", "👏"), ("عمل رائع", "🌟"),
        ("بالتوفيق في الامتحان", "📚"), ("اختبار غداً", "📝"), ("ذاكرت كثيراً", "🤓"), ("نجحت بحمد الله", "🎓"),
        ("أحسنت", "👏"), ("لا تستسلم", "💪"), ("كن إيجابياً", "🌈"), ("خطوة بخطوة", "👣"),
        ("التزم بالموعد", "⏰"), ("ممتاز أكمل", "👍"), ("أرسل الملف", "📎"), ("وصلني شكراً", "📥"),
        ("سنتحدث لاحقاً", "🗓️"), ("إجازة سعيدة", "🏖️"), ("بداية أسبوع موفقة", "🌅"), ("نهاية أسبوع سعيدة", "🎉"),
        ("تعبت اليوم", "😩"), ("استراحة قصيرة", "☕"), ("لدي فكرة", "💡"), ("ما رأيكم؟", "🤔"),
        ("موافق", "✔️"), ("سأراجع وأخبرك", "🔍"),
    ]),
    "islamic_events": ("مناسبات إسلامية", ["moon", "star", "sparkle", "flower"], [
        ("أهلاً رمضان", "🌙"), ("تقبل الله صيامكم", "🤲"), ("صيام مقبول", "🌙"), ("إفطار شهي", "🍽️"),
        ("سحور مبارك", "🌃"), ("ليلة القدر", "✨"), ("عيد الفطر مبارك", "🎉"), ("عيد الأضحى مبارك", "🐑"),
        ("حج مبرور", "🕋"), ("عمرة مقبولة", "🕋"), ("رحلة إيمانية", "🕌"), ("يوم الجمعة نور", "🕌"),
        ("صلاة مقبولة", "🤲"), ("حفظك الله", "🛡️"), ("عساكم من عواده", "🎊"), ("هلّ هلال", "🌙"),
        ("ليلة مباركة", "🌙"), ("دعواتكم", "🤲"), ("في ميزان حسناتك", "⚖️"), ("أجر وعافية", "🌿"),
        ("اللهم لك الحمد", "🙏"), ("تصبحون على خير", "🌙"), ("نسألكم الدعاء", "🤲"), ("بركة الشهر", "🌟"),
        ("صدقة جارية", "💝"), ("ذكر الله", "📿"), ("الله يشفيه", "🌿"), ("اللهم ارحمه", "🕊️"),
        ("مبارك عليكم الشهر", "🌙"), ("كل طاعة وأنتم بخير", "🌹"),
    ]),
    "funny_replies": ("مواقف طريفة", ["lightning", "star", "sparkle", "balloon"], [
        ("هههه أموت", "💀"), ("لا أصدق", "😳"), ("يا ويلي", "😱"), ("كفو", "👏"),
        ("أنت تمزح", "🤨"), ("وش هالسالفة", "🧐"), ("يا الله", "😮"), ("جد؟", "🤔"),
        ("ما صدقت", "😲"), ("لا حول", "🤦"), ("أعوذ بالله", "😨"), ("ضحكتني", "😂"),
        ("على جثتي", "😤"), ("خلاص انتهينا", "🙅"), ("أنا نايم", "😴"), ("ما سمعت شي", "🙉"),
        ("تفاءل", "🌈"), ("أعطني فرصة", "🙏"), ("هدّي اللعب", "😅"), ("أنا بريء", "😇"),
        ("جبتها", "🎯"), ("ما عندي خبر", "🤷"), ("إيش القصة؟", "🤔"), ("لا تفضحني", "🙈"),
        ("سر بيننا", "🤫"), ("يا سلام عليك", "😏"), ("هذا أنا", "😎"), ("مو معقول", "😵"),
        ("الله يستر", "🙏"), ("خير إن شاء الله", "🤞"),
    ]),
    "praise_cheer": ("مديح وتشجيع", ["star", "crown", "sparkle", "heart"], [
        ("أنت رائع", "🌟"), ("فخور بك", "👏"), ("إبداع", "🎨"), ("مبدع", "💡"),
        ("عمل ممتاز", "👍"), ("كفو والله", "👏"), ("أحسنت صنعاً", "🌹"), ("تستاهل", "🏆"),
        ("بطل", "🏅"), ("أنت الأفضل", "🥇"), ("نجم النجوم", "⭐"), ("ما شاء الله عليك", "✨"),
        ("استمر", "💪"), ("واصل التقدم", "🚀"), ("الله يقويك", "💪"), ("إلى الأمام", "➡️"),
        ("أداء مذهل", "🤩"), ("فريق رائع", "🤝"), ("رائع جداً", "👌"), ("جهد مشكور", "🙏"),
        ("شكراً لك يا بطل", "🦸"), ("أنت قدها", "💪"), ("لا شيء مستحيل", "🌈"), ("آمن بنفسك", "✨"),
        ("ثق بنفسك", "😎"), ("نجاح باهر", "🎓"), ("تفوق مستمر", "📈"), ("أنت ملهم", "💡"),
        ("كل التقدير", "🌹"), ("دمت متألقاً", "🌟"),
    ]),
    "weekdays_time": ("أيام وأوقات", ["sun", "moon", "flower", "sparkle"], [
        ("سبت مبارك", "📅"), ("أحد جميل", "📅"), ("اثنين نشيط", "💪"), ("ثلاثاء هادئ", "😌"),
        ("أربعاء موفق", "🍀"), ("خميس سعيد", "🎉"), ("أحلى جمعة", "🕌"), ("فجر جميل", "🌅"),
        ("ظهيرة سعيدة", "☀️"), ("عصر هادئ", "🌤️"), ("مغرب جميل", "🌇"), ("ليل هادئ", "🌌"),
        ("منتصف الليل", "🕛"), ("بداية جديدة", "🌱"), ("غداً أفضل", "🌈"), ("أول الشهر", "📅"),
        ("نهاية الشهر", "💸"), ("الصيف", "🏖️"), ("الشتاء", "❄️"), ("الخريف", "🍂"),
        ("الربيع", "🌸"), ("كل يوم جديد", "🌞"), ("الآن", "⏱️"), ("بعد قليل", "⏳"),
        ("قريباً", "🔜"), ("اليوم", "📍"), ("غداً", "➡️"), ("أسبوع موفق", "📅"),
        ("عطلة سعيدة", "🏝️"), ("وقت مستقطع", "⏸️"),
    ]),
}

TALK_PACKS = {
    "bunny_talk": ("أرنوب يتكلم", "bunny", [
        ("هلو", "👋", "wave"), ("شلونك؟", "🙂", "smile"), ("أهلاً", "🤗", "happy"), ("مرحباً", "👋", "wave"),
        ("صباح الخير", "☀️", "happy"), ("مساء الخير", "🌆", "smile"), ("تصبح على خير", "🌙", "sleepy"), ("شكراً", "🙏", "pray"),
        ("عفواً", "😊", "shy"), ("آسف", "🥺", "sad"), ("أحبك", "❤️", "love"), ("تمام", "👍", "ok"),
        ("ماشي", "👌", "ok"), ("لا", "🙅", "no"), ("ممكن؟", "🙏", "ask"), ("وينك؟", "🤔", "think"),
        ("اشتقت لك", "💕", "love"), ("مبروك", "🎉", "party"), ("بالتوفيق", "🍀", "happy"), ("جوعان", "🍔", "yum"),
        ("نعسان", "😴", "sleepy"), ("تعبان", "😩", "tired"), ("زعلان", "😢", "cry"), ("أنا قادم", "🏃", "run"),
        ("بعد قليل", "⏳", "think"), ("يا سلام", "🤩", "star"), ("هههههه", "😂", "laugh"), ("مستحيل", "😱", "shock"),
        ("كلمني", "☎️", "tongue"), ("مع السلامة", "👋", "wave"),
    ]),
    "cat_talk": ("ميمو يتكلم", "cat", [
        ("يا هلا", "👋", "wave"), ("حياك الله", "🌹", "happy"), ("وش أخبارك؟", "🗞️", "smile"), ("كيف الحال؟", "🙂", "smile"),
        ("الحمد لله", "🙏", "pray"), ("أبشر", "👍", "ok"), ("على راسي", "👌", "ok"), ("ما عليك", "😌", "shy"),
        ("يا غالي", "❤️", "love"), ("يعطيك العافية", "💪", "cool"), ("الله يسلمك", "🤝", "happy"), ("جزاك الله خير", "🤲", "pray"),
        ("نورتنا", "🌟", "star"), ("بسرعة", "⚡", "run"), ("لحظة", "⏳", "think"), ("أنا زعلان", "😢", "cry"),
        ("أنا جوعان", "🍕", "yum"), ("ما أبي", "🙅", "no"), ("أبي قهوة", "☕", "ask"), ("تعال هنا", "👉", "tongue"),
        ("وين رايح؟", "🚗", "think"), ("سلامات", "🌿", "smile"), ("تسلم", "🌹", "happy"), ("أنا مشغول", "💻", "tired"),
        ("موافق", "✔️", "ok"), ("أحسنت", "👏", "party"), ("مبروك عليك", "🎉", "party"), ("ليلة سعيدة", "🌙", "sleepy"),
        ("صباح الورد", "🌹", "love"), ("مع السلامة", "👋", "wave"),
    ]),
    "bear_talk": ("دبدوب يتكلم", "bear", [
        ("أهلاً بك", "🤗", "happy"), ("كل عام وأنتم بخير", "🎉", "party"), ("صباح النور", "☀️", "wave"), ("مساء النور", "🌇", "smile"),
        ("نوم العافية", "😴", "sleepy"), ("أنا معك", "🤝", "ok"), ("لا تقلق", "😌", "shy"), ("فداك", "💝", "love"),
        ("وحشتني", "💔", "sad"), ("أحبك كثيراً", "❤️", "love"), ("يلا نطلع", "🚗", "run"), ("أبي عسل", "🍯", "yum"),
        ("تعال نلعب", "🎈", "party"), ("أنا غاضب", "😡", "no"), ("ما أصدق", "😱", "shock"), ("ههههه", "😂", "laugh"),
        ("فكرة", "💡", "think"), ("بالتوفيق", "🍀", "happy"), ("أحسنت", "👏", "star"), ("سامحني", "🥺", "sad"),
        ("شكراً جزيلاً", "🌹", "pray"), ("الله يحفظك", "🤲", "pray"), ("وين الأكل؟", "🍽️", "ask"), ("حاضر", "👍", "ok"),
        ("بكرة نتكلم", "🗓️", "think"), ("قوم يا كسلان", "⏰", "tired"), ("أنا بخير", "😊", "smile"), ("تعبت", "😩", "tired"),
        ("ممتاز", "⭐", "cool"), ("إلى اللقاء", "👋", "wave"),
    ]),
    "bunny_talk2": ("أرنوب يتكلم 2", "bunny", [
        ("كيف حالك؟", "🙂", "smile"), ("الحمد لله", "🙏", "pray"), ("يعطيك العافية", "💪", "cool"), ("ما شاء الله", "✨", "star"),
        ("بارك الله فيك", "🌹", "happy"), ("جزاك الله خيراً", "🤲", "pray"), ("إن شاء الله", "🤞", "ask"), ("بإذن الله", "🌟", "happy"),
        ("صباح الورد", "🌹", "love"), ("مساء الفل", "🌼", "happy"), ("حبيبي", "😍", "love"), ("يا قلبي", "💖", "love"),
        ("لحظة", "⏳", "think"), ("دقيقة", "⏱️", "think"), ("أنا في الطريق", "🚗", "run"), ("وصلت", "📍", "wave"),
        ("خلاص", "🙌", "star"), ("لا تزعل", "🤗", "shy"), ("مسامح", "🤝", "ok"), ("أنا آسف جداً", "🙏", "sad"),
        ("عيد سعيد", "🎊", "party"), ("رمضان كريم", "🌙", "happy"), ("جمعة مباركة", "🕌", "pray"), ("يا رب", "🤲", "pray"),
        ("ما أدري", "🤷", "think"), ("أكيد", "✅", "ok"), ("طبعاً", "💯", "cool"), ("مو مشكلة", "👌", "ok"),
        ("بسرعة", "⚡", "run"), ("نلتقي قريباً", "🤝", "wave"),
    ]),
    "cat_talk2": ("ميمو يتكلم 2", "cat", [
        ("صباح الخير", "☀️", "wave"), ("مساء الخير", "🌆", "smile"), ("تصبح على خير", "🌙", "sleepy"), ("هلا والله", "👋", "wave"),
        ("كلمني", "☎️", "tongue"), ("أنا مشغول", "💼", "tired"), ("اشتقت لك", "💕", "love"), ("أحبك", "❤️", "love"),
        ("شكراً", "🙏", "pray"), ("عفواً", "😊", "shy"), ("آسف", "🥺", "sad"), ("تمام", "👍", "ok"),
        ("لا", "🙅", "no"), ("يمكن", "🤷", "think"), ("مستحيل", "😱", "shock"), ("هههههه", "😂", "laugh"),
        ("وش رايك؟", "🤔", "think"), ("زين", "👌", "ok"), ("مبروك", "🎉", "party"), ("حظ سعيد", "🍀", "happy"),
        ("بالعافية", "🍽️", "yum"), ("نعسان", "😴", "sleepy"), ("جوعان", "🍔", "yum"), ("تعبان", "😩", "tired"),
        ("أنا جاي", "🏃", "run"), ("وين انت؟", "🧐", "ask"), ("لا تتأخر", "⏰", "point"), ("يا سلام", "🤩", "star"),
        ("ما عليه", "😌", "shy"), ("سلام", "👋", "wave"),
    ]),
}


def build():
    for key, (_, _, phrases) in TEXT_PACKS.items():
        assert 3 <= len(phrases) <= 30, (key, len(phrases))
    if os.path.isdir(ASSETS):
        shutil.rmtree(ASSETS)
    os.makedirs(ASSETS)
    packs = []
    previews = []

    def add_pack(identifier, name, images):
        folder = os.path.join(ASSETS, identifier)
        os.makedirs(folder)
        stickers = []
        for i, (img, emojis, acc) in enumerate(images, 1):
            fn = "%02d.webp" % i
            final = finalize(img)
            save_webp(final, os.path.join(folder, fn))
            stickers.append({"image_file": fn, "emojis": emojis, "accessibility_text": acc})
            if i <= 10:
                previews.append(final)
            if i == 1:
                final.resize((96, 96), Image.LANCZOS).save(os.path.join(folder, "tray.png"), optimize=True)
        packs.append({
            "identifier": identifier, "name": name, "publisher": PUBLISHER,
            "tray_image_file": "tray.png", "image_data_version": "1", "avoid_cache": False,
            "publisher_email": "", "publisher_website": "", "privacy_policy_website": "",
            "license_agreement_website": "", "stickers": stickers,
        })
        print("pack %-15s %d stickers" % (identifier, len(stickers)))

    for char, ident, name in (("face", "faces_smile", "وجوه مرحة"),
                              ("cat", "cats_mood", "قطط المزاج"),
                              ("bear", "bears_mood", "دببة المشاعر")):
        items = [(draw_character(e, char), e["em"], e["n"]) for e in EXPRESSIONS]
        add_pack(ident, name, items)

    for p_idx, (ident, (name, icons, phrases)) in enumerate(TEXT_PACKS.items(), start=3):
        items = [(text_sticker(t, i, p_idx, icons), [em], t) for i, (t, em) in enumerate(phrases)]
        add_pack(ident, name, items)

    for ident, (name, char, rows) in TALK_PACKS.items():
        assert 3 <= len(rows) <= 30, (ident, len(rows))
        items = [(talk_sticker(t, mood, char), [em], t) for (t, em, mood) in rows]
        add_pack(ident, name, items)

    with open(os.path.join(ASSETS, "contents.json"), "w", encoding="utf-8") as fh:
        json.dump({"android_play_store_link": "", "ios_app_store_link": "", "sticker_packs": packs},
                  fh, ensure_ascii=False, indent=2)

    total = sum(len(p["stickers"]) for p in packs)
    print("TOTAL stickers:", total)

    # launcher icons
    first = Image.open(os.path.join(ASSETS, "cats_mood", "01.webp")).convert("RGBA")
    for folder, size in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        big = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        bg = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle((0, 0, 511, 511), radius=110, fill=(31, 163, 122, 255))
        big.alpha_composite(bg)
        face = first.resize((400, 400), Image.LANCZOS)
        big.alpha_composite(face, (56, 62))
        out = os.path.join(RES, "mipmap-" + folder)
        os.makedirs(out, exist_ok=True)
        big.resize((size, size), Image.LANCZOS).save(os.path.join(out, "ic_launcher.png"), optimize=True)

    # preview sheet
    cols, th = 10, 96
    rows = (len(previews) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * th, rows * th), (236, 239, 241, 255))
    for i, im in enumerate(previews):
        t = im.resize((th - 6, th - 6), Image.LANCZOS)
        sheet.alpha_composite(t, ((i % cols) * th + 3, (i // cols) * th + 3))
    os.makedirs(os.path.dirname(PREVIEW), exist_ok=True)
    sheet.convert("RGB").save(PREVIEW, optimize=True)


if __name__ == "__main__":
    build()
