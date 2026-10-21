"""Writes slides/art/memory-scale.svg: boards placed by RAM (gold axis) and flash (blue axis) on one log scale.

The figures' sources are in the slide's speaker notes.
"""
import math
from pathlib import Path

ART = Path(__file__).resolve().parents[2] / 'slides' / 'art'
W, H = 1112, 372
RAM_Y, FLASH_Y = 250, 335
AX0, DECADE = 96, 140  # x of 10 KB, px per factor of ten; 100 GB lands at 1076, unlabelled to clear the QR
PX_MM = 1.9
FLOOR = 128  # photos stand on this line
LEADER_TOP = 176
KB, MB, GB = 1024, 1024 ** 2, 1024 ** 3


def x(nbytes):
    return AX0 + (math.log10(nbytes) - 4) * DECADE


def n(v):
    return f'{round(v, 1):g}'


# name, image, aspect, width in mm (micro:bits a touch under their 52 mm), RAM, flash, CPU, photo centre (None: over its RAM via)
BOARDS = [
    ('micro:bit V1', 'microbit-v1.webp', 700 / 519, 46, 16 * KB, 256 * KB, '16 MHz', 86),
    ('micro:bit V2', 'microbit-v2.webp', 700 / 545, 46, 128 * KB, 512 * KB, '64 MHz', 205),
    ('Pyboard D', 'pyboard-d.webp', 700 / 533, 33.5, 256 * KB, 4.5 * MB, '216 MHz', 306),
    ('Pico 2', 'pico-2.webp', 800 / 325, 51, 520 * KB, 4 * MB, '150 MHz', 398),
    ('Nano ESP32', 'arduino-nano-esp32.webp', 700 / 291, 45, 8.5 * MB, 16 * MB, '240 MHz', 505),
    ('Pi Zero 2 W', 'pi-zero-2-w.webp', 700 / 412, 65, 512 * MB, 32 * GB, '1 GHz', None),
    ('Raspberry Pi 5', 'raspberry-pi-5.webp', 800 / 609, 85, 8 * GB, 32 * GB, '2.4 GHz', None),
]


def leader(cx, vx):
    """Down from under the labels, one 45° jog onto the via's column, down to the RAM axis."""
    d = vx - cx
    assert abs(d) <= RAM_Y - 12 - LEADER_TOP, f'jog {d:.0f} too long for a single 45° run'
    if abs(d) < 3:
        return f'M{n(vx)} {LEADER_TOP} V{RAM_Y - 6}'
    return f'M{n(cx)} {LEADER_TOP} V{n(RAM_Y - 12 - abs(d))} L{n(vx)} {RAM_Y - 12} V{RAM_Y - 6}'


def board(name, img, aspect, mm, ram, flash, cpu, cx):
    rx, fx = x(ram), x(flash)
    cx = rx if cx is None else cx
    w = mm * PX_MM
    h = w / aspect
    return [
        f'<image href="/images/boards/{img}" x="{n(cx - w / 2)}" y="{n(FLOOR - h)}" width="{n(w)}" height="{n(h)}" filter="url(#ms-shadow)"/>',
        f'<text class="ms-name" x="{n(cx)}" y="146" text-anchor="middle">{name}</text>',
        f'<text class="ms-cpu" x="{n(cx)}" y="165" text-anchor="middle">{cpu}</text>',
        f'<path class="ms-trace" d="{leader(cx, rx)}"/>',
        f'<path class="ms-link" d="M{n(rx)} {RAM_Y + 6} L{n(fx)} {FLASH_Y - 6}" mask="url(#ms-label-gaps)"/>',
        f'<circle class="ms-via ms-via--ram" cx="{n(rx)}" cy="{RAM_Y}" r="5"/>',
        f'<circle class="ms-via ms-via--flash" cx="{n(fx)}" cy="{FLASH_Y}" r="5"/>',
    ]


def panels():
    """One board panel per group, shown on the slide's one click and drawn under everything else."""
    bottom = H - 1
    mcu = f'M0 0 H590 V{bottom} H0 Z'
    # The computers' panel cuts its corner at 45° to stay clear of the QR's escapes.
    sbc = f'M688 0 H1096 V{bottom - 46} L{1096 - 46} {bottom} H688 Z'
    return [f'<path class="ms-zone" d="{mcu}"/>', f'<path class="ms-zone" d="{sbc}"/>']


def build():
    left, right = x(10 * KB) - 16, x(100 * GB) + 14
    o = ['<defs><filter id="ms-shadow" x="-20%" y="-20%" width="140%" height="160%">'
         '<feDropShadow class="ms-shadow" dx="0" dy="8" stdDeviation="6"/></filter></defs>']
    o.append('<g class="fragment" data-fragment-index="0">' + ''.join(panels()) + '</g>')
    o.append(f'<path class="ms-axis ms-axis--ram" d="M{n(left)} {RAM_Y} H{n(right)}"/>')
    o.append(f'<path class="ms-axis ms-axis--flash" d="M{n(left)} {FLASH_Y} H{n(right)}"/>')
    o.append(f'<text class="ms-axis-label ms-axis-label--ram" x="8" y="{RAM_Y + 6}">RAM</text>')
    o.append(f'<text class="ms-axis-label ms-axis-label--flash" x="8" y="{FLASH_Y + 6}">FLASH</text>')
    ticks, labels, gaps = [], [], []
    for k, label in enumerate(['10 KB', '100 KB', '1 MB', '10 MB', '100 MB', '1 GB', '10 GB', '100 GB']):
        tx = AX0 + k * DECADE
        ticks.append(f'M{tx} {RAM_Y + 6} V{RAM_Y + 12} M{tx} {FLASH_Y + 6} V{FLASH_Y + 12}')
        if label != '100 GB':
            for y in (RAM_Y + 28, FLASH_Y + 28):
                labels.append(f'<text class="ms-tick-label" x="{tx}" y="{y}" text-anchor="middle">{label}</text>')
            w = len(label) * 9.6 + 10  # 14px mono with its tracking
            gaps.append(f'<rect x="{n(tx - w / 2)}" y="{RAM_Y + 14}" width="{n(w)}" height="20"/>')
    o.append(f'<path class="ms-tick" d="{" ".join(ticks)}"/>')
    # The dotted links break where they cross the RAM scale's labels.
    o[0] = o[0].replace('</defs>', f'<mask id="ms-label-gaps" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
                        f'<rect width="{W}" height="{H}" fill="#fff"/><g fill="#000">{"".join(gaps)}</g></mask></defs>')
    for b in BOARDS:
        o.extend(board(*b))
    return o + labels


if __name__ == '__main__':
    inner = '\n'.join('  ' + line for line in build())
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="diagram memory-scale" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">\n'
           '  <title>Boards placed by RAM and by flash on one log scale: microcontrollers have kilobytes to megabytes, single-board computers gigabytes</title>\n'
           f'{inner}\n</svg>\n')
    (ART / 'memory-scale.svg').write_text(svg, encoding='utf-8')
    print('slides/art/memory-scale.svg', len(svg), 'bytes')
