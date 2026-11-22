"""Render data/contributions.json as an animated contribution heatmap SVG (contrib-heatmap.svg)."""
import json
import os
from collections import defaultdict
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "contrib-heatmap.svg")
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, FG, DIM, ACCENT = "#0d1117", "#c9d1d9", "#8b949e", "#39d353"
CELL, GAP = 13, 3
STEP = CELL + GAP
LEFT, TOP = 44, 64
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def level_for(count, maxc):
    if count == 0:
        return 0
    if count >= maxc * 0.75 and count >= 20:
        return 5
    return min(4, 1 + int(4 * count / max(maxc * 0.5, 1)))


def stats(days):
    counts = [d["count"] for d in days]
    total = sum(counts)
    # longest streak
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    # current streak (today may still be empty, so start from yesterday in that case)
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1
    current = 0
    while i >= 0 and counts[i]:
        current += 1
        i -= 1
    best = max(days, key=lambda d: d["count"]) if days else None
    months = defaultdict(int)
    for d in days:
        months[d["date"][:7]] += d["count"]
    top_month = max(months.items(), key=lambda kv: kv[1]) if months else ("", 0)
    active = sum(1 for c in counts if c)
    return total, current, longest, best, top_month, active


def fmt_day(iso):
    d = date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def main():
    data = json.load(open(DATA))
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # Sunday = row 0
    maxc = max(d["count"] for d in days) or 1
    ncols = (len(days) + offset + 6) // 7
    W = LEFT + ncols * STEP + 20
    H = TOP + 7 * STEP + 96

    css = "" if STATIC else f"""
    .c {{ opacity:0; animation: pop .45s cubic-bezier(.2,.8,.2,1) forwards; }}
    @keyframes pop {{ from {{ opacity:0; transform: translate(-6px,-6px); }} to {{ opacity:1; transform: none; }} }}
    .f {{ opacity:0; animation: fade .6s ease-out forwards; }}
    @keyframes fade {{ from {{ opacity:0; transform: translateY(6px); }} to {{ opacity:1; transform:none; }} }}
    .cur {{ animation: blink 1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}"""

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
           f"<style>{css}</style>",
           f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{BG}" stroke="#30363d"/>']

    # title bar
    for i, col in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        out.append(f'<circle cx="{18 + i*16}" cy="16" r="5" fill="{col}"/>')
    total, current, longest, best, top_month, active = stats(days)
    out.append(f'<text x="{W/2}" y="20" fill="{DIM}" font-size="11" text-anchor="middle">'
               f'contributions — {total} in the last year</text>')

    # month labels
    seen = set()
    for idx, d in enumerate(days):
        dt = date.fromisoformat(d["date"])
        col = (idx + offset) // 7
        if dt.day <= 7 and (dt.year, dt.month) not in seen and col < ncols - 1:
            seen.add((dt.year, dt.month))
            out.append(f'<text x="{LEFT + col*STEP}" y="{TOP - 10}" fill="{DIM}" font-size="10">{MONTHS[dt.month-1]}</text>')
    for row, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{LEFT - 8}" y="{TOP + row*STEP + 10}" fill="{DIM}" font-size="10" text-anchor="end">{lab}</text>')

    # cells, revealed along the diagonal
    for idx, d in enumerate(days):
        col, row = divmod(idx + offset, 7)
        lvl = level_for(d["count"], maxc)
        delay = "" if STATIC else f' style="animation-delay:{(col + row) * 0.035:.3f}s"'
        tip = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {fmt_day(d["date"])}'
        out.append(f'<rect class="c"{delay} x="{LEFT + col*STEP}" y="{TOP + row*STEP}" width="{CELL}" height="{CELL}" '
                   f'rx="3" fill="{PALETTE[lvl]}"><title>{tip}</title></rect>')

    end_delay = (ncols + 7) * 0.035
    gy = TOP + 7 * STEP + 8
    # legend
    lx = W - 20 - 6 * STEP - 70
    out.append(f'<g class="f" style="animation-delay:{end_delay:.2f}s">')
    out.append(f'<text x="{lx}" y="{gy + 10}" fill="{DIM}" font-size="10">Less</text>')
    for i, c in enumerate(PALETTE):
        out.append(f'<rect x="{lx + 32 + i*STEP}" y="{gy}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>')
    out.append(f'<text x="{lx + 36 + 6*STEP}" y="{gy + 10}" fill="{DIM}" font-size="10">More</text>')
    out.append("</g>")

    # stats footer
    ym = top_month[0]
    month_label = f"{MONTHS[int(ym[5:])-1]} {ym[:4]}" if ym else "-"
    items = [("total", f"{total}"), ("active days", f"{active}"), ("current streak", f"{current}d"),
             ("longest streak", f"{longest}d"),
             ("best day", f"{best['count']} · {fmt_day(best['date'])}" if best else "-"),
             ("top month", f"{month_label} ({top_month[1]})")]
    fy = gy + 40
    out.append(f'<line x1="20" y1="{fy - 16}" x2="{W-20}" y2="{fy - 16}" stroke="#21262d"/>')
    colw = (W - 40) / 3
    for i, (k, v) in enumerate(items):
        x = 24 + (i % 3) * colw
        y = fy + (i // 3) * 22
        out.append(f'<text class="f" style="animation-delay:{end_delay + 0.15*i + 0.2:.2f}s" x="{x}" y="{y}" font-size="12">'
                   f'<tspan fill="{ACCENT}">{k}</tspan><tspan fill="{DIM}">: </tspan><tspan fill="{FG}">{v}</tspan></text>')
    out.append(f'<text x="{W-20}" y="{H-12}" fill="#484f58" font-size="9" text-anchor="end">updated {data.get("fetched", "")}'
               f'<tspan class="cur" fill="{ACCENT}"> ▌</tspan></text>')
    out.append("</svg>")
    open(OUT, "w").write("\n".join(out))
    print(f"wrote {OUT} ({W}x{H}) total={total} current={current} longest={longest}")


if __name__ == "__main__":
    main()
