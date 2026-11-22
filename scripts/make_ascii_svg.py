"""Draw a panda (I go by Panda), convert it to ASCII with a density ramp, and emit a self-typing SVG.

Each row is revealed by a left-to-right clip wipe with a block cursor on the edge, rows staggered
top to bottom; plays once and freezes. STATIC=1 writes a frozen frame.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "panda-ascii.svg")
STATIC = os.environ.get("STATIC") == "1"

RAMP = " .`:-=+*cs#%@"  # sparse -> dense (text is light on dark, so dense = bright)
COLS, ROWS = 60, 30
CW, CH = 10, 20  # source pixels per character cell (chars are ~1:2)
FONT, LH = 10, 11.6
CHAR_W = 6.02
BG, FG, ACCENT, DIM = "#0d1117", "#c9d1d9", "#39d353", "#8b949e"


def draw_panda():
    W, H = COLS * CW, ROWS * CH
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    cx = W // 2
    black, white = 70, 235
    # body / shoulders with a laptop
    d.ellipse([cx - 210, 470, cx + 210, 800], fill=black)
    d.ellipse([cx - 120, 500, cx + 120, 700], fill=white - 30)
    # ears
    for sx in (-1, 1):
        d.ellipse([cx + sx * 150 - 62, 40, cx + sx * 150 + 62, 160], fill=black)
    # head
    d.ellipse([cx - 200, 70, cx + 200, 470], fill=white)
    # eye patches (tilted)
    for sx in (-1, 1):
        patch = Image.new("L", (130, 170), 0)
        ImageDraw.Draw(patch).ellipse([0, 0, 130, 170], fill=255)
        patch = patch.rotate(-28 * sx, expand=True, resample=Image.BICUBIC)
        px = cx + sx * 85 - patch.width // 2
        img.paste(black, (px, 170, px + patch.width, 170 + patch.height), patch)
    d = ImageDraw.Draw(img)
    # eyes + highlights
    for sx in (-1, 1):
        ex = cx + sx * 78
        d.ellipse([ex - 22, 245, ex + 22, 295], fill=150)
        d.ellipse([ex - 8 + sx * 4, 252, ex + 8 + sx * 4, 270], fill=255)
    # nose + mouth
    d.ellipse([cx - 36, 330, cx + 36, 372], fill=30)
    d.line([cx, 372, cx, 395], fill=60, width=8)
    d.arc([cx - 48, 360, cx, 420], 20, 160, fill=60, width=8)
    d.arc([cx, 360, cx + 48, 420], 20, 160, fill=60, width=8)
    # laptop
    d.polygon([(cx - 150, 640), (cx + 150, 640), (cx + 185, 720), (cx - 185, 720)], fill=110)
    d.rectangle([cx - 185, 720, cx + 185, 740], fill=200)
    d.text((cx - 18, 665), "</>", fill=255)

    # radial shading for a bit of depth on the white fur
    yy, xx = np.mgrid[0:H, 0:W]
    shade = 1.0 - 0.35 * np.clip(np.hypot((xx - cx) / 260, (yy - 250) / 260), 0, 1)
    arr = np.asarray(img.filter(ImageFilter.GaussianBlur(1.2)), dtype=float) / 255.0
    return arr * np.where(arr > 0.8, shade, 1.0)


def to_ascii(arr):
    lines = []
    for r in range(ROWS):
        row = ""
        for c in range(COLS):
            v = arr[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW].mean()
            row += RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]
        lines.append(row.rstrip())
    # trim empty rows top/bottom
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    lines = to_ascii(draw_panda())
    pad = 18
    W = int(COLS * CHAR_W + 2 * pad)
    H = int(len(lines) * LH + 2 * pad + 14)
    per_row, start = 0.11, 0.3
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FONT}">',
           f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="#30363d"/>']
    if not STATIC:
        out.append("<defs>")
        for i, ln in enumerate(lines):
            w = len(ln) * CHAR_W + 2
            b = start + i * per_row
            out.append(f'<clipPath id="r{i}"><rect x="{pad}" y="{pad + i*LH}" height="{LH+1}" width="0">'
                       f'<animate attributeName="width" from="0" to="{w:.1f}" begin="{b:.2f}s" dur="{per_row:.2f}s" fill="freeze"/>'
                       f"</rect></clipPath>")
        out.append("</defs>")
    for i, ln in enumerate(lines):
        y = pad + i * LH + FONT
        clip = "" if STATIC else f' clip-path="url(#r{i})"'
        tl = f' textLength="{len(ln)*CHAR_W:.1f}" lengthAdjust="spacing"' if ln else ""
        out.append(f'<text x="{pad}" y="{y:.1f}" fill="{FG}" xml:space="preserve"{tl}{clip}>{esc(ln)}</text>')
    if not STATIC:
        # block cursor riding the wipe edge, then parking at the bottom and blinking
        total = start + len(lines) * per_row
        xs, ys, kt = [], [], []
        for i, ln in enumerate(lines):
            t0 = (start + i * per_row) / (total + 0.4)
            t1 = (start + i * per_row + per_row * 0.99) / (total + 0.4)
            xs += [pad, pad + len(ln) * CHAR_W]
            ys += [pad + i * LH, pad + i * LH]
            kt += [t0, t1]
        kt = [0] + kt + [1]
        xs = [pad] + xs + [pad]
        ys = [pad] + ys + [pad + len(lines) * LH + 2]
        out.append(f'<rect width="{CHAR_W:.1f}" height="{LH:.1f}" fill="{ACCENT}">'
                   f'<animate attributeName="x" values="{";".join(f"{x:.1f}" for x in xs)}" keyTimes="{";".join(f"{t:.4f}" for t in kt)}" '
                   f'dur="{total+0.4:.2f}s" calcMode="linear" fill="freeze"/>'
                   f'<animate attributeName="y" values="{";".join(f"{y:.1f}" for y in ys)}" keyTimes="{";".join(f"{t:.4f}" for t in kt)}" '
                   f'dur="{total+0.4:.2f}s" calcMode="discrete" fill="freeze"/>'
                   f'<animate attributeName="opacity" values="1;0;1" dur="1s" begin="{total+0.4:.2f}s" repeatCount="indefinite" calcMode="discrete"/>'
                   f"</rect>")
    out.append(f'<text x="{W - pad}" y="{H - 10}" fill="{DIM}" font-size="9" text-anchor="end">~/panda.txt</text>')
    out.append("</svg>")
    open(OUT, "w").write("\n".join(out))
    print("\n".join(lines))
    print(f"wrote {OUT} ({W}x{H}, {len(lines)} rows)")


if __name__ == "__main__":
    main()
