# The picture that isn't the character's behaviours: the power symbol shown once after a boot.
# The badge, in four greys, is badge.py's.
from PIL import Image, ImageDraw

from face import H, W, thick_line


def boot():
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    cx, cy, r, w = W // 2, H // 2 + 10, 150, 34
    d.arc((cx - r, cy - r, cx + r, cy + r), -55, 235, fill=0, width=w)
    thick_line(d, (cx, cy - r - 10), (cx, cy - 10), w)
    return img.convert("1")
