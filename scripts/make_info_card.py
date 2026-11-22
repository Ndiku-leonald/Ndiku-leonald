"""Neofetch-style info card (info-card.svg). Lines fade and slide in on a stagger. STATIC=1 = frozen frame."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

BG, FG, DIM, ACCENT, KEY = "#0d1117", "#c9d1d9", "#8b949e", "#39d353", "#58a6ff"

USER = "panda@github"
ROWS = [
    ("Name", "Ndiku Leonald (“Panda”)"),
    ("Role", "Backend Developer"),
    ("Study", "BSc IT · Uganda Christian University"),
    ("Host", "Mukono, Uganda · UTC+3"),
    None,
    ("Now", "BorrowMate — P2P borrowing for students"),
    ("Prev", "CraftHub — skills + market for mothers"),
    ("Also", "Unistel hostels · UCU Innovators Hub"),
    None,
    ("Stack", "Python · Node.js/Express · TypeScript"),
    ("Web", "React · REST APIs · JWT auth"),
    ("Data", "PostgreSQL · Docker · Git"),
    ("Extra", "WordPress · MQL5 trading bots"),
    None,
    ("Focus", "tech for community-level problems"),
]
COLORS = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]

W, PAD, LH, FS = 490, 22, 21, 13


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    n_lines = 2 + len(ROWS) + 2
    H = 40 + PAD + n_lines * LH + 16
    css = "" if STATIC else """
    .l { opacity:0; animation: in .5s cubic-bezier(.2,.8,.2,1) forwards; }
    @keyframes in { from { opacity:0; transform: translateX(-10px); } to { opacity:1; transform:none; } }
    .cur { animation: blink 1s steps(1) infinite; }
    @keyframes blink { 50% { opacity:0; } }"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="{FS}">',
           f"<style>{css}</style>",
           f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="#30363d"/>',
           f'<path d="M1 30 H{W-1}" stroke="#21262d"/>']
    for i, col in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        out.append(f'<circle cx="{18 + i*16}" cy="15" r="5" fill="{col}"/>')
    out.append(f'<text x="{W/2}" y="19" fill="{DIM}" font-size="11" text-anchor="middle">panda@ucu: ~ — neofetch</text>')

    y = 40 + PAD
    k = 0

    def line(content):
        nonlocal y, k
        delay = "" if STATIC else f' style="animation-delay:{0.35 + k*0.12:.2f}s"'
        out.append(f'<g class="l"{delay}><text x="{PAD}" y="{y}">{content}</text></g>')
        y += LH
        k += 1

    line(f'<tspan fill="{ACCENT}" font-weight="bold">{USER}</tspan>')
    rule = "─" * len(USER)
    line(f'<tspan fill="#30363d">{rule}</tspan>')
    for row in ROWS:
        if row is None:
            y += LH * 0.45
            continue
        key, val = row
        line(f'<tspan fill="{KEY}" font-weight="bold">{key}</tspan><tspan fill="{DIM}">:</tspan>'
             f'<tspan x="{PAD + 64}" fill="{FG}">{esc(val)}</tspan>')
    y += LH * 0.4
    delay = "" if STATIC else f' style="animation-delay:{0.35 + k*0.12:.2f}s"'
    blocks = "".join(f'<rect x="{PAD + i*26}" y="{y - 13}" width="24" height="16" rx="3" fill="{c}"/>' for i, c in enumerate(COLORS))
    out.append(f'<g class="l"{delay}>{blocks}</g>')
    y += LH + 6
    k += 1
    delay = "" if STATIC else f' style="animation-delay:{0.35 + k*0.12:.2f}s"'
    out.append(f'<g class="l"{delay}><text x="{PAD}" y="{y}"><tspan fill="{ACCENT}">panda@ucu</tspan>'
               f'<tspan fill="{DIM}">:~$ </tspan><tspan class="cur" fill="{ACCENT}">▌</tspan></text></g>')
    H2 = int(y + 20)
    out[0] = out[0].replace(f'height="{H}"', f'height="{H2}"').replace(f"0 0 {W} {H}", f"0 0 {W} {H2}")
    out[2] = out[2].replace(f'height="{H-1}"', f'height="{H2-1}"')
    out.append("</svg>")
    open(OUT, "w", encoding="utf-8").write("\n".join(out))
    print(f"wrote {OUT} ({W}x{H2})")


if __name__ == "__main__":
    main()
