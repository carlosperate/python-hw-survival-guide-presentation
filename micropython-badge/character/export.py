# Renders the character for the board: a frame pack per style, idle.json (what each animation
# plays) and cards.frm (boot, badge). A shared pose is one frame, numbered alike in every style.
# A pack: b"FRM1", the frame count (u16), count + 1 offsets (u32, from the file's start), then
# each frame as a zlib stream of the panel's buffer (800x480, MONO_HLSB, 1 for white).
import json
import os
import struct
import sys
import zlib

import cards
import idle
from face import REST, STYLES

# Committed: the board's /idle/, copied with the rest of device/.
BOARD = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "device", "idle"))
WBITS = 10  # a 1 KB window: packs within 3% of the largest window's
GROUPS = {"behaviours": idle.BEHAVIOURS, "blinks": idle.BLINKS}


def frames():
    """The distinct poses, and each group's animations as (frame, ms) pairs."""
    poses, index, table = [], {}, {}
    for group, animations in GROUPS.items():
        table[group] = {}
        for name, steps in animations.items():
            table[group][name] = []
            for st, ms in steps:
                key = repr(sorted(st.items()))
                if key not in index:
                    index[key] = len(poses)
                    poses.append(st)
                table[group][name].append([index[key], ms])
    return poses, table


def pack(images):
    data = []
    for img in images:
        z = zlib.compressobj(9, zlib.DEFLATED, WBITS)
        data.append(z.compress(img.tobytes()) + z.flush())
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
    os.makedirs(out, exist_ok=True)
    poses, table = frames()
    print(len(poses), "frames a style")
    for style in STYLES:
        write(out, style + ".frm", pack(idle.render(style, st) for st in poses))
    write(out, "cards.frm", pack([cards.boot(), cards.badge()]))  # deck/idle.py's CARDS
    table["styles"] = list(STYLES)
    table["rest"] = poses.index(REST)  # every animation starts and ends on it
    with open(os.path.join(out, "idle.json"), "w") as f:
        json.dump(table, f, separators=(",", ":"))
    print(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
