"""Kanalens varumärke – används av alla filmer.

Ändra brand.json så får alla framtida renderingar den nya loggan.
"""
import json
import os

from PIL import ImageFont

_B = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand.json"), encoding="utf-8"))
TOP = _B["topp"]
BOTTOM = _B["botten"]
ACCENT = tuple(int(_B["accent"][i:i + 2], 16) for i in (1, 3, 5))

_FD = "/usr/share/fonts/opentype/inter"


def _f(name, size):
    p = os.path.join(_FD, name)
    return ImageFont.truetype(p, size) if os.path.exists(p) else ImageFont.load_default(size)


F_TOP = _f("InterDisplay-SemiBold.otf", 22)
F_BOTTOM = _f("InterDisplay-Black.otf", 50)


def _spaced(d, xy, txt, font, fill, spacing):
    x, y = xy
    for ch in txt:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + spacing


def _spaced_w(d, txt, font, spacing):
    return sum(d.textlength(c, font=font) for c in txt) + spacing * (len(txt) - 1)


def draw_logo(d, right=1010, top=200, dark=False, alpha=225):
    """Ritar loggan högerjusterad i övre högra hörnet (under TikToks sökikon)."""
    fg = (15, 15, 18) if dark else (245, 245, 248)
    wb = _spaced_w(d, BOTTOM, F_BOTTOM, 2)
    wt = _spaced_w(d, TOP, F_TOP, 9)
    w = max(wb, wt) + 36
    x0 = right - w
    d.rectangle([x0, top, right, top + 100], outline=fg + (alpha,), width=3)
    d.rectangle([x0, top, x0 + 10, top + 100], fill=ACCENT + (alpha,))
    _spaced(d, (x0 + 10 + (w - 10 - wt) / 2, top + 10), TOP, F_TOP, fg + (alpha,), 9)
    _spaced(d, (x0 + 10 + (w - 10 - wb) / 2, top + 36), BOTTOM, F_BOTTOM, fg + (alpha,), 2)
