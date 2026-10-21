"""Writes slides/art/deck-map.svg, the map on "But there is a lot more!": the talk's slides, stacks of detail below."""
from pathlib import Path

ART = Path(__file__).resolve().parents[2] / 'slides' / 'art'
W, H, GAP, ROW = 96, 54, 40, 82
LABEL_W = 200  # 'Extra details ↓' as rendered
INSET = 40  # labels start this far in from the content edge
X0 = INSET + LABEL_W + 20
XS = [X0 + k * (W + GAP) for k in range(6)]
STACKS = {1: ['links', 'sources'], 3: ['code'], 4: ['sources', 'links']}
STEP = 4  # quarter beats between one talk slide and the next


def n(v):
    return f'{round(v, 2):g}'


def frame(x, y, detail):
    cls = 'map-slide map-slide--detail' if detail else 'map-slide'
    title = 'map-title map-title--detail' if detail else 'map-title'
    return (f'<rect class="{cls}" x="{x}" y="{y}" width="{W}" height="{H}" rx="4"/>'
            f'<path class="{title}" d="M{x + 10} {y + 12} H{x + 46}"/>')


def lines(x, y, widths, cls='map-text'):
    return f'<path class="{cls}" d="' + ' '.join(f'M{x + 10} {y + 22 + 7 * i} H{x + 10 + w}' for i, w in enumerate(widths)) + '"/>'


def content(kind, x, y):
    if kind == 'text':
        return lines(x, y, [70, 58, 64, 40])
    if kind == 'wave':
        clk = 'M{0} {1} h6 v-8 h6 v8 h6 v-8 h6 v8 h6 v-8 h6 v8 h6 v-8 h6 v8 h6'.format(x + 12, y + 32)
        sda = 'M{0} {1} h10 l3 -8 h18 l3 8 h12 l3 -8 h14 l3 8 h10'.format(x + 12, y + 46)
        return f'<path class="map-wave map-wave--clk" d="{clk}"/><path class="map-wave" d="{sda}"/>'
    if kind == 'code':
        return (f'<rect class="map-well" x="{x + 10}" y="{y + 18}" width="{W - 20}" height="28" rx="2"/>'
                f'<path class="map-code map-code--kw" d="M{x + 15} {y + 25} h12 M{x + 15} {y + 39} h8"/>'
                f'<path class="map-code" d="M{x + 30} {y + 25} h30 M{x + 21} {y + 32} h40 M{x + 26} {y + 39} h22"/>'
                f'<path class="map-code map-code--str" d="M{x + 64} {y + 32} h14"/>')
    if kind == 'heap':
        cells = []
        for r in range(4):
            for c in range(11):
                k = (r * 11 + c) * 7 % 10
                cls = 'map-cell--a' if k < 3 else 'map-cell--f' if k < 5 else 'map-cell--x' if k == 9 else 'map-cell'
                cells.append(f'<rect class="{cls}" x="{x + 10 + c * 7}" y="{y + 18 + r * 7}" width="5" height="5" rx="0.8"/>')
        return ''.join(cells)
    if kind == 'chart':
        bars = [14, 22, 18, 30, 26]
        return ('<path class="map-axis" d="M{0} {1} H{2}"/>'.format(x + 10, y + 46, x + 86) +
                ''.join(f'<rect class="map-bar{" map-bar--hi" if i == 3 else ""}" x="{x + 14 + i * 14}" y="{y + 46 - b}" width="9" height="{b}"/>'
                        for i, b in enumerate(bars)))
    if kind == 'rule':
        return (f'<rect class="map-rule" x="{x + 10}" y="{y + 18}" width="{W - 20}" height="28" rx="3"/>'
                f'<path class="map-rule-text" d="M{x + 16} {y + 27} h24 M{x + 16} {y + 35} h56 M{x + 16} {y + 41} h40"/>')
    if kind == 'links':
        return (lines(x, y, [52, 64]) +
                f'<path class="map-link-text" d="M{x + 10} {y + 38} H{x + 60} M{x + 10} {y + 45} H{x + 50}"/>'
                f'<path class="map-link-icon" d="M{x + 72} {y + 44} l8 -8 m-6 0 h6 v6"/>')
    if kind == 'sources':
        return ''.join(f'<circle class="map-dot" cx="{x + 12}" cy="{y + 22 + 7 * i}" r="1.6"/>' for i in range(4)) + \
            '<path class="map-text" d="' + ' '.join(f'M{x + 18} {y + 22 + 7 * i} H{x + 18 + w}' for i, w in enumerate([60, 48, 66, 38])) + '"/>'
    raise ValueError(kind)


def build():
    out = []
    talk = ['text', 'wave', 'code', 'heap', 'chart', 'rule']
    mid = H / 2
    # The talk: each slide appears in turn, lights as the current one, and the trace runs on to the next.
    for k, x in enumerate(XS):
        d = 2 + STEP * k
        out.append(f'<g class="b-rise" style="--d:{d}">{frame(x, 0, False)}{content(talk[k], x, 0)}'
                   f'<rect class="map-current b-flash" style="--d:{d}" x="{x}" y="0" width="{W}" height="{H}" rx="4"/></g>')
        if k < len(XS) - 1:
            out.append(f'<path class="map-link b-draw" pathLength="1" style="--d:{d + 2}" d="M{x + W} {n(mid)} H{x + W + GAP}"/>')
    out.append(f'<text class="map-label b-fade" style="--d:0" x="{n(X0 - 20)}" y="{n(mid + 6)}" text-anchor="end">The talk →</text>')

    # The details: one click shows them all.
    det, links, vias = [], [], []
    for k, kinds in STACKS.items():
        cx = XS[k] + W / 2
        vias.append(f'M{n(cx - 3)} {H + 6} a3 3 0 1 0 6 0 a3 3 0 1 0 -6 0')
        for depth, kind in enumerate(kinds, start=1):
            y = depth * ROW
            det.append(frame(XS[k], y, True) + content(kind, XS[k], y))
            links.append(f'M{n(cx)} {H + 9 if depth == 1 else (depth - 1) * ROW + H} V{y}')
    out.append('<g class="fragment" data-fragment-index="0">')
    out.append(f'  <path class="map-link map-link--detail" d="{" ".join(links)}"/>')
    out.append(f'  <path class="map-via" d="{" ".join(vias)}"/>')
    out += ['  ' + d for d in det]
    for i, word in enumerate(('Extra details ↓', 'resources&nbsp;&nbsp;', 'links&nbsp;&nbsp;')):
        out.append(f'  <text class="map-label map-label--detail" x="{n(X0 - 20)}" y="{n(ROW + mid + 24 * i)}" text-anchor="end">{word}</text>')
    out.append('</g>')
    return out


if __name__ == '__main__':
    inner = '\n'.join('  ' + line for line in build())
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" class="diagram deck-map build" viewBox="0 0 1112 218" width="1112" height="218" role="img">\n'
           '  <title>The talk runs left to right, one slide at a time; some slides have a stack of detail slides below them</title>\n'
           f'{inner}\n</svg>\n')
    (ART / 'deck-map.svg').write_text(svg, encoding='utf-8')
    print('slides/art/deck-map.svg', len(svg), 'bytes')
