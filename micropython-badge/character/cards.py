# The pictures that aren't the character, the same in every style: the power symbol shown once
# after a boot, and the slides' cards (the 640K photo, the owl, POP). The badge, in four greys,
# is badge.py's.
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

import badge
import stage
from face import H, W, thick_line

IMAGES = Path(__file__).resolve().parent / "images"


def boot():
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    cx, cy, r, w = W // 2, H // 2 + 10, 150, 34
    d.arc((cx - r, cy - r, cx + r, cy + r), -55, 235, fill=0, width=w)
    thick_line(d, (cx, cy - r - 10), (cx, cy - 10), w)
    return img.convert("1")


def pop():
    """Out of RAM: the face, swollen, bursts."""
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    stage.burst(d, 400, 230, 120, 230, n=14, w=14)
    stage.label(d, 400, 230, "POP", 80)
    return img.convert("1")


def roboto(size, weight):
    return badge.font("roboto", size, weight, scale=1)


def memory():
    """The 640K photo under its quote, dithered: a partial refresh can't show grey."""
    src = Image.open(IMAGES / "640k.png").convert("L")
    photo = src.crop((0, 56, src.width, src.height))  # below the picture's own caption
    photo = ImageOps.fit(photo, (W, 384), centering=(0.5, 0.4), method=Image.LANCZOS)
    photo = ImageEnhance.Contrast(photo).enhance(1.25)
    photo = ImageEnhance.Brightness(photo).enhance(1.15)
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    d.text(
        (400, 30),
        "“640K ought to be enough for anybody.”",
        font=roboto(38, 700),
        fill=0,
        anchor="mm",
    )
    d.text((400, 72), "attributed to Bill Gates, 1981", font=roboto(24, 450), fill=0, anchor="mm")
    img.paste(photo.convert("1").convert("L"), (0, 96))
    return img.convert("1")


def owl():
    """The owl meme, its pencil drawings dithered and its words set again, so they stay crisp."""
    drawing = Image.open(IMAGES / "owl.webp").convert("L").crop((0, 34, 530, 385))
    drawing = ImageEnhance.Contrast(ImageOps.autocontrast(drawing, cutoff=1)).enhance(1.3)
    drawing = drawing.resize((560, round(351 * 560 / 530)), Image.LANCZOS)
    img = Image.new("L", (W, H), 255)
    img.paste(drawing.convert("1").convert("L"), (120, 48))
    d = ImageDraw.Draw(img)
    d.text((40, 26), "How to draw an owl", font=roboto(30, 500), fill=0, anchor="lm")
    first, caption = "1. Draw some circles", roboto(26, 500)
    d.text((40, 450), first, font=caption, fill=0, anchor="lm")
    left = 40 + caption.getlength(first) + 36
    d.text((left, 450), "2. Draw the rest of the fucking owl", font=caption, fill=0, anchor="lm")
    return img.convert("1")


CARDS = {"boot": boot, "640k": memory, "owl": owl, "pop": pop}  # in cards.frm, in this order
