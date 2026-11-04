# Renders the character for the board: a frame pack per style (a shared pose is one frame,
# numbered alike in every style), cards.frm (pictures in no style), badge.gs2 and idle.json (each
# animation's frames or cards, and the cards' order). A pack: b"FRM1", the frame count (u16),
# count + 1 offsets (u32, from the file's start), then each frame as a zlib stream of the panel's
# 800x480 MONO_HLSB buffer, 1 for white. badge.gs2: b"GRY1", then a zlib GS2_HMSB frame, 0 black.
import json
import os
import struct
import sys
import zlib

import badge
import cards
import idle
import slides
from face import REST, STYLES

# Committed: the board's /idle/, copied with the rest of device/.
BOARD = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "device", "idle"))
WBITS = 10  # a 1 KB window: packs within 3% of the largest window's
GROUPS = {"behaviours": idle.BEHAVIOURS, "blinks": idle.BLINKS, "slides": slides.SLIDES}


def frames():
    """The distinct poses, and each group's animations as (frame, ms) pairs."""
    poses, index, table = [], {}, {}
    for group, animations in GROUPS.items():
        table[group] = {}
        for name, steps in animations.items():
            table[group][name] = []
            for st, ms in steps:
                if isinstance(st, str):  # a card, by name
                    table[group][name].append([st, ms])
                    continue
                key = repr(sorted(st.items()))
                if key not in index:
                    index[key] = len(poses)
                    poses.append(st)
                table[group][name].append([index[key], ms])
    return poses, table


def compress(data):
    z = zlib.compressobj(9, zlib.DEFLATED, WBITS)
    return z.compress(data) + z.flush()


def pack(images):
    data = [compress(img.tobytes()) for img in images]
    head = 4 + 2 + 4 * (len(data) + 1)
    offsets = [head]
    for frame in data:
        offsets.append(offsets[-1] + len(frame))
    return b"FRM1" + struct.pack("<H%dI" % len(offsets), len(data), *offsets) + b"".join(data)


def write(out, name, blob):
    with open(os.path.join(out, name), "wb") as f:
        f.write(blob)
    print(name, len(blob), "bytes")


def main(out=BOARD):
    # Everything is drawn before anything is written: a pack whose frame numbers idle.json no
    # longer matches would play the wrong frames.
    poses, table = frames()
    print(len(poses), "frames a style")
    files = [(style + ".frm", pack(idle.render(style, st) for st in poses)) for style in STYLES]
    files.append(("cards.frm", pack(draw() for draw in cards.CARDS.values())))
    files.append(("badge.gs2", b"GRY1" + compress(badge.gs2(badge.draw()))))
    table["styles"] = list(STYLES)
    table["cards"] = list(cards.CARDS)  # cards.frm's order, for the board to find them by name
    table["rest"] = poses.index(REST)  # every animation starts and ends on it
    files.append(("idle.json", json.dumps(table, separators=(",", ":")).encode()))
    os.makedirs(out, exist_ok=True)
    for name, blob in files:
        write(out, name, blob)
    print(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
