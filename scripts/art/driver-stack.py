"""Writes slides/art/driver-stack.svg: one chip-ID read followed from your code down to the BME280."""
from pathlib import Path

ART = Path(__file__).resolve().parents[2] / 'slides' / 'art'
W, H = 1112, 480
BAR_X, BAR_W, BAR_H, PITCH = 40, 380, 52, 66
FLOW_X = 14
# The slide's code panel sits right of the layers, above the divide: keep driver-stack.css in step.
SPLIT_Y = 290
CHIP_Y, CHIP_H = 326, 150
PIN_YS = [344, 372, 400, 428, 456]
NEAR_X, NEAR_W = 480, 172
FAR_X, FAR_W = 700, 190
PART_H = 26

# (name, file or None), one click each; the slide shows each layer's code beside it.
LAYERS = [
    ('YOUR CODE', 'main.py'),
    ('DRIVER', 'bme280.py'),
    ('MICROPYTHON', 'machine.I2C'),
    ('SILICON VENDOR SDK', None),
]
PINS = ['I²C', 'SPI', 'UART', 'PWM', 'GPIO']
# (pin index, near or far column, label); I²C carries two parts, so its trace runs on to the second.
PARTS = [(0, 'near', 'BME280'), (0, 'far', 'SSD1306 OLED'), (1, 'far', 'SD card'),
         (2, 'near', 'GPS'), (3, 'far', 'SG90 servo'), (4, 'near', 'NeoPixel ring')]


def mid(i):
    return i * PITCH + BAR_H / 2


def flow(y0, y1):
    """A gold step of the read going down, with its own head."""
    return f'<path class="ds-flow" pathLength="1" d="M{FLOW_X} {y0 + 4} V{y1 - 2} M{FLOW_X - 6} {y1 - 9} L{FLOW_X} {y1 - 2} L{FLOW_X + 6} {y1 - 9}"/>'


def build():
    out = []
    last = len(LAYERS) - 1
    chip_at, parts_at, read_at = last + 1, last + 2, last + 3

    # On entry only the divide and two empty boxes; each turns into its layers on a click.
    out.append(f'<path class="ds-split b-fade" style="--d:0" d="M0 {SPLIT_Y} H{W}"/>')
    out.append(f'<text class="ds-side b-fade" style="--d:0" x="{BAR_X}" y="{SPLIT_Y - 6}">SOFTWARE ↑</text>')
    out.append(f'<text class="ds-side b-fade" style="--d:0" x="{BAR_X}" y="{SPLIT_Y + 22}">HARDWARE ↓</text>')
    soft_h = last * PITCH + BAR_H
    out.append(f'<g class="b-fade" style="--d:1"><g class="fragment fade-out" data-fragment-index="{last}">'
               f'<rect class="ds-box" x="{BAR_X}" y="0" width="{BAR_W}" height="{soft_h}" rx="6"/></g></g>')
    out.append(f'<g class="b-fade" style="--d:2"><g class="fragment fade-out" data-fragment-index="{chip_at}">'
               f'<rect class="ds-box" x="{BAR_X}" y="{CHIP_Y}" width="{BAR_W}" height="{CHIP_H}" rx="10"/></g></g>')

    # Software, one layer per click, the one you write in gold; the read steps down with it.
    for i, (name, file) in enumerate(LAYERS):
        y = i * PITCH
        you = ' ds-layer--you' if i == 1 else ''
        out.append(f'<g class="fragment" data-fragment-index="{i}">'
                   f'<rect class="ds-layer{you}" x="{BAR_X}" y="{y}" width="{BAR_W}" height="{BAR_H}" rx="6"/>'
                   f'<text class="ds-name{" ds-name--you" if i == 1 else ""}" x="{BAR_X + 18}" y="{y + 32}">{name}</text>'
                   + (f'<text class="ds-file" x="{BAR_X + BAR_W - 18}" y="{y + 32}">{file}</text>' if file else '')
                   + (f'<circle class="ds-flow-start" cx="{FLOW_X}" cy="{mid(0)}" r="5"/>' if i == 0 else '')
                   + '</g>')
        if i:
            out.append(f'<g class="draw fragment" data-fragment-index="{i}">{flow(mid(i - 1), mid(i))}</g>')

    # Hardware: the microcontroller and its peripherals as pins, then the parts on their traces.
    out.append(f'<g class="fragment" data-fragment-index="{chip_at}">'
               f'<rect class="ds-chip" x="{BAR_X}" y="{CHIP_Y}" width="{BAR_W}" height="{CHIP_H}" rx="10"/>'
               f'<text class="ds-chip-name" x="{BAR_X + 24}" y="{CHIP_Y + 42}">MICROCONTROLLER</text>'
               + ''.join(f'<text class="ds-pin" x="{BAR_X + BAR_W - 14}" y="{y + 6}">{p}</text>'
                         f'<rect class="ds-pad" x="{BAR_X + BAR_W}" y="{y - 5}" width="10" height="10"/>'
                         for p, y in zip(PINS, PIN_YS)) + '</g>')
    out.append(f'<g class="draw fragment" data-fragment-index="{chip_at}">{flow(mid(last), CHIP_Y + 40)}</g>')
    pad = BAR_X + BAR_W + 10
    ends = {}
    for pin, col, _ in PARTS:
        end = FAR_X if col == 'far' else NEAR_X
        ends[pin] = max(ends.get(pin, 0), end)
    out.append(f'<g class="draw fragment" data-fragment-index="{parts_at}">'
               '<path class="ds-trace" pathLength="1" d="'
               + ' '.join(f'M{pad} {PIN_YS[p]} H{e}' for p, e in ends.items()) + '"/></g>')
    out.append(f'<g class="fragment" data-fragment-index="{parts_at}">' + ''.join(
        f'<rect class="ds-part" x="{x}" y="{PIN_YS[pin] - PART_H / 2}" width="{w}" height="{PART_H}" rx="4"/>'
        f'<text class="ds-part-name" x="{x + w / 2}" y="{PIN_YS[pin] + 6}">{label}</text>'
        for pin, col, label in PARTS
        for x, w in [(FAR_X, FAR_W) if col == 'far' else (NEAR_X, NEAR_W)]) + '</g>')

    # Last click: the read leaves on the I²C pins for the BME280.
    out.append(f'<g class="draw fragment" data-fragment-index="{read_at}">'
               f'<path class="ds-hot" pathLength="1" d="M{pad} {PIN_YS[0]} H{NEAR_X}"/></g>')
    out.append(f'<g class="fragment" data-fragment-index="{read_at}">'
               f'<rect class="ds-hot-box" x="{NEAR_X}" y="{PIN_YS[0] - PART_H / 2}" width="{NEAR_W}" height="{PART_H}" rx="4"/>'
               f'<text class="ds-note" x="{BAR_X + 24}" y="{CHIP_Y + 112}">its I²C block drives the wires</text></g>')
    return out


if __name__ == '__main__':
    inner = '\n'.join('  ' + line for line in build())
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" class="diagram driver-stack build" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img">\n'
           '  <title>The layers under one sensor read: your code, the driver, MicroPython and the silicon vendor SDK '
           'in software; the microcontroller and its I2C, SPI, UART, PWM and GPIO pins in hardware, wired to a BME280, '
           'an OLED, an SD card, a GPS, a servo and a NeoPixel ring</title>\n'
           f'{inner}\n</svg>\n')
    (ART / 'driver-stack.svg').write_text(svg, encoding='utf-8')
    print('slides/art/driver-stack.svg', len(svg), 'bytes')
