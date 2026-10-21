"""Writes slides/art/breadboard-blink.svg, "1. Blink an LED" on the owl slide: a Pico on a breadboard wired to one LED."""
from pathlib import Path

ART = Path(__file__).resolve().parents[2] / 'slides' / 'art'
ROWS_TOP, ROWS_BOTTOM = (116, 126, 136, 146, 156), (176, 186, 196, 206, 216)


def n(v):
    return f'{round(v, 2):g}'


def group(s):
    return f'<g>{s}</g>'


def ring(x, y, r):
    return f'M{n(x - r)} {n(y)} a{r} {r} 0 1 0 {n(2 * r)} 0 a{r} {r} 0 1 0 {n(-2 * r)} 0'


def wire(d, colour, ends):
    pins = ''.join(f'<circle class="bb-pin" cx="{x}" cy="{y}" r="2.2"/>' for x, y in ends)
    return (pins + f'<path class="bb-wire-edge" d="{d}"/>'
            f'<path class="bb-wire bb-wire--{colour}" d="{d}"/>')


def board():
    o = []
    o.append('<defs>'
             '<pattern id="bb-holes" width="10" height="10" x="-5" y="1" patternUnits="userSpaceOnUse">'
             '<rect class="bb-hole" x="3.3" y="3.3" width="3.4" height="3.4" rx="0.6"/></pattern>'
             '<pattern id="bb-rail-holes" width="60" height="10" x="35" y="1" patternUnits="userSpaceOnUse">'
             + ''.join(f'<rect class="bb-hole" x="{3.3 + 10 * i}" y="3.3" width="3.4" height="3.4" rx="0.6"/>' for i in range(5)) +
             '</pattern>'
             '<radialGradient id="bb-glow"><stop offset="0" class="bb-glow-in"/><stop offset="1" class="bb-glow-out"/></radialGradient>'
             '<linearGradient id="bb-cable-fade" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="150">'
             '<stop offset="0" class="bb-cable-out"/><stop offset="0.6" class="bb-cable-in"/></linearGradient>'
             '</defs>')

    # The breadboard.
    labels = ''.join(f'<text class="bb-label" x="{30 + 10 * (c - 1)}" y="110" text-anchor="middle">{c}</text>'
                     f'<text class="bb-label" x="{30 + 10 * (c - 1)}" y="226" text-anchor="middle">{c}</text>'
                     for c in (1, 5, 10, 15, 20, 25, 30, 35, 40))
    letters = ''.join(f'<text class="bb-label" x="25" y="{y + 1.8}" text-anchor="middle">{ch}</text>'
                      for ch, y in zip('abcdefghij', ROWS_TOP + ROWS_BOTTOM))
    signs = ''.join(f'<text class="bb-sign bb-sign--{cls}" x="{x}" y="{y}" text-anchor="middle">{g}</text>'
                    for x in (26, 454) for y, g, cls in ((83, '−', 'neg'), (105, '+', 'pos'), (233, '+', 'pos'), (255, '−', 'neg')))
    o.append(group(
        '<rect class="bb" x="20" y="74" width="440" height="184" rx="5"/>'
        '<path class="bb-rail" d="M38 80 H442 M38 252 H442"/>'
        '<path class="bb-rail bb-rail--pos" d="M38 102 H442 M38 230 H442"/>'
        '<rect fill="url(#bb-rail-holes)" x="35" y="81" width="410" height="20"/>'
        '<rect fill="url(#bb-rail-holes)" x="35" y="231" width="410" height="20"/>'
        '<rect fill="url(#bb-holes)" x="25" y="111" width="430" height="50"/>'
        '<rect fill="url(#bb-holes)" x="25" y="171" width="430" height="50"/>'
        '<rect class="bb-channel" x="24" y="161.5" width="432" height="9" rx="1"/>'
        + labels + letters + signs))

    # The Pico, pressed in across the channel: pins in rows b and h, 7 pitches apart like the real one.
    pins_top = [(50 + 10 * i, 126) for i in range(20)]
    pins_bottom = [(50 + 10 * i, 196) for i in range(20)]
    castles = ' '.join(f'M{x - 1.6} 119.5h3.2v2h-3.2z M{x - 1.6} 200.5h3.2v2h-3.2z' for x in range(50, 241, 10))
    traces = ('M136 152 V140 L130 134 H110 V129 M140 147 V137 H150 V129 M160 147 V139 L168 131 V129 '
              'M164 161 H180 M164 157 H178 L182 153 M164 165 H182 '
              'M144 175 V188 L140 192 V193 M152 175 V186 L160 194 M136 170 L122 184 L122 193 '
              'M196 161 H210 L218 153 H238 M100 140 L92 132 H70 V129')
    qfn = ''.join(f'M{n(136 + 2.33 * i - 0.5)} 145h1v2h-1z M{n(136 + 2.33 * i - 0.5)} 175h1v2h-1z '
                  f'M134 {n(149 + 2.33 * i - 0.5)}h2v1h-2z M164 {n(149 + 2.33 * i - 0.5)}h2v1h-2z' for i in range(13))
    pico = (
        '<g class="op-green">'
        '<rect class="op-mask bb-pico" x="44.5" y="119.5" width="201" height="83" rx="2"/>'
        f'<path class="op-trace" d="{traces}"/>'
        f'<path class="op-gold" d="{castles}"/>'
        '<rect class="op-gold" x="47" y="123" width="6" height="6" rx="0.5"/>'
        f'<path class="op-gold" d="{" ".join(ring(x, y, 3) for x, y in pins_top[1:] + pins_bottom)}"/>'
        f'<path class="op-hole" d="{" ".join(ring(x, y, 1.4) for x, y in pins_top + pins_bottom)}"/>'
        '<rect class="op-ic" x="136" y="147" width="28" height="28" rx="1"/>'
        f'<path class="op-tin" d="{qfn}"/>'
        '<image href="/images/python-mark.svg" x="141.5" y="152.5" width="17" height="17"/>'
        '<rect class="op-ic" x="184" y="154" width="12" height="15" rx="1"/>'
        '<path class="op-tin" d="M181 156h3v1.6h-3z M181 160h3v1.6h-3z M181 164h3v1.6h-3z M196 156h3v1.6h-3z M196 160h3v1.6h-3z M196 164h3v1.6h-3z"/>'
        '<rect class="op-metal" x="113" y="178" width="11" height="8" rx="1.2"/>'
        '<rect class="op-tin" x="82" y="140" width="12" height="12" rx="1"/><circle class="bb-key" cx="88" cy="146" r="3.6"/>'
        '<rect class="bb-onboard-led" x="64" y="138" width="4" height="2.4" rx="0.4"/>'
        '<rect class="op-ic" x="214" y="176" width="8" height="10" rx="0.8"/>'
        '<path class="op-gold" d="' + ' '.join(ring(238, y, 2.2) for y in (150, 160, 170)) + '"/>'
        '<rect class="op-metal" x="37" y="150" width="16" height="22" rx="1.5"/>'
        '<rect class="op-metal-top" x="39" y="152" width="12" height="18" rx="1"/>'
        '<rect class="op-usb-mouth" x="36.5" y="155" width="2.5" height="12" rx="1"/>'
        '</g>')
    o.append(group(pico))

    # USB cable from the laptop, off the top of the panel.
    o.append('<path class="bb-cable" stroke="url(#bb-cable-fade)" '
             'd="M4 0 V120 C4 146 6 161 22 161"/>')
    o.append(group('<rect class="bb-plug" x="18" y="152" width="20" height="18" rx="3"/>'
                   '<path class="bb-plug-grip" d="M22 155 V167 M25 155 V167 M28 155 V167"/>'))

    # Jumper wires, under the LED: the signal from the Pico's top pin to the LED, ground to the rail.
    o.append(wire('M240 116 C250 90 310 90 320 116', 'gold', [(240, 116), (320, 116)]))
    o.append(wire('M70 216 C58 226 58 236 70 246', 'blue', [(70, 216), (70, 246)]))

    # 220 Ω resistor from the LED's cathode column down to the ground rail.
    o.append(group('<path class="bb-lead" d="M330 156 V246"/>'
                   '<rect class="bb-res" x="324.5" y="183" width="11" height="30" rx="4.5"/>'
                   '<path class="bb-band bb-band--red" d="M324.5 189 H335.5 M324.5 195 H335.5"/>'
                   '<path class="bb-band bb-band--brown" d="M324.5 201 H335.5"/>'
                   '<path class="bb-band bb-band--gold" d="M324.5 208 H335.5"/>'))

    # The LED, standing on its legs in row c.
    o.append(group('<path class="bb-lead" d="M320 136 V127 M330 136 V127"/>'
                   '<rect class="bb-led-flange" x="315" y="124" width="20" height="5" rx="1.5"/>'
                   '<path class="led-blink bb-led-dome" d="M317 126 V106 A8 8 0 0 1 333 106 V126 Z"/>'
                   '<path class="bb-led-shine" d="M321 108 V118"/>'))
    o.append('<circle class="bb-halo" cx="325" cy="112" r="30" fill="url(#bb-glow)"/>')

    return o


if __name__ == '__main__':
    inner = '\n'.join('  ' + line for line in board())
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" class="diagram breadboard" viewBox="0 0 480 262" width="480" height="262" role="img">\n'
           '  <title>A MicroPython board on a breadboard, wired to one blinking LED</title>\n'
           f'{inner}\n</svg>\n')
    (ART / 'breadboard-blink.svg').write_text(svg, encoding='utf-8')
    print('slides/art/breadboard-blink.svg', len(svg), 'bytes')
