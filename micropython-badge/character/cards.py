# The pictures that aren't the character's behaviours: the power symbol shown once after a boot,
# and the badge. Put the real badge at character/badge.png (any size: it's fitted to the panel
# and dithered); until then a placeholder is drawn.
import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

import idle
from face import H, W, pose, thick_line, threshold

BADGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "badge.png")


def boot():
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    cx, cy, r, w = W // 2, H // 2 + 10, 150, 34
    d.arc((cx - r, cy - r, cx + r, cy + r), -55, 235, fill=0, width=w)
    thick_line(d, (cx, cy - r - 10), (cx, cy - 10), w)
    return img.convert("1")


def badge(path=BADGE):
    if os.path.exists(path):
        img = ImageOps.pad(Image.open(path).convert("L"), (W, H), color=255)
        return img.convert("1")  # dithered, so a photo keeps its greys
    # The face is drawn whole before it's scaled, so it can't sit nearer the edge.
    img = idle.render("outlined", pose(fx=560, fy=260, zoom=0.55)).convert("L")
    d = ImageDraw.Draw(img)
    d.text((56, 60), "YOUR NAME", fill=0, font=ImageFont.load_default(size=78))
    d.text((60, 170), "Talk title goes here", fill=0, font=ImageFont.load_default(size=40))
    d.text((60, 230), "@handle", fill=0, font=ImageFont.load_default(size=40))
    note = "placeholder: character/badge.png"  # clear of the link icon's corner
    d.text((60, 400), note, fill=0, font=ImageFont.load_default(size=24))
    return threshold(img)
