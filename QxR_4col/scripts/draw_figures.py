#!/usr/bin/env python3
"""Draw the seven contradiction panels and the proper four-coloring."""
import json
import math
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

(ROOT / "figures").mkdir(exist_ok=True)

data = json.loads((ROOT / "data/qr23.json").read_text())
certificate = json.loads((ROOT / "data/qr23_proof_certificate.json").read_text())
coords = [
    (v[0] / data["denominator"],
     sum(a * math.sqrt(r) for a, r in zip(v[1:], data["radicands"]))
     / data["denominator"])
    for v in data["vertices"]
]
edges = [(a - 1, b - 1) for a, b in data["edges_1based"]]
order = sorted(range(len(coords)), key=lambda i: (coords[i][1], coords[i][0]))
labels = {old: new for new, old in enumerate(order, start=1)}
palette = ["#3B6FB6", "#E69F00", "#269E6A"]
red = "#C51B2D"

for case_number, case in enumerate(certificate["leaves"], start=1):
    colors = case["colors"]
    sequence = [int(v) - 1 for v in certificate["root_colors"]]
    for line in case["trace"]:
        match = re.match(r"(?:ASSUME )?V(\d+)=", line)
        if match:
            sequence.append(int(match[1]) - 1)
    assert len(set(sequence)) == len(sequence)
    assert set(sequence) == {v for v, c in enumerate(colors) if c >= 0}
    u, v, color = case["conflict"]
    u -= 1
    v -= 1

    fig, ax = plt.subplots(figsize=(8.6, 7.2))
    for a, b in edges:
        if {a, b} == {u, v}:
            continue
        ax.plot([coords[a][0], coords[b][0]], [coords[a][1], coords[b][1]],
                color="0.77", lw=0.9, zorder=1)
    ax.plot([coords[u][0], coords[v][0]], [coords[u][1], coords[v][1]],
            color=red, lw=2.8, zorder=2)
    ax.scatter([x for x, y in coords], [y for x, y in coords], s=230,
               c=[palette[c] if c >= 0 else "#D9D9D9" for c in colors],
               edgecolors="black", linewidths=0.7, zorder=3)
    ax.scatter([coords[u][0], coords[v][0]], [coords[u][1], coords[v][1]],
               s=330, facecolors="none", edgecolors=red, linewidths=1.9, zorder=4)
    for step, old in enumerate(sequence, start=1):
        x, y = coords[old]
        ax.text(x, y, str(step), ha="center", va="center", fontsize=8.5,
                fontweight="bold", color="white", zorder=5)
    for old, (x, y) in enumerate(coords):
        ax.text(x + 0.028, y + 0.04, str(labels[old]), ha="left", va="bottom",
                fontsize=11, color="black",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.65, pad=0.15),
                zorder=6)
    assumptions = ", ".join(
        rf"$c(v_{{{labels[old - 1]}}})={c}$" for old, c in case["assumptions"]
    )
    ax.set_title(
        f"Case {case_number}: {assumptions}\n"
        rf"contradiction on edge $v_{{{labels[u]}}}v_{{{labels[v]}}}$ (color {color})",
        fontsize=12,
    )
    ax.set_aspect("equal", adjustable="datalim")
    ax.axis("off")
    ax.margins(0.09)
    fig.tight_layout()
    fig.canvas.draw()
    tight = fig.get_tightbbox(fig.canvas.get_renderer())
    # Keep exactly the same PDF dimensions as the existing four-color panel.
    width, height = 606.24 / 72, 504.64 / 72
    bbox = Bbox.from_bounds((tight.x0 + tight.x1 - width) / 2,
                           (tight.y0 + tight.y1 - height) / 2, width, height)
    out = ROOT / "figures" / f"qr23_case_{case_number}"
    fig.savefig(out.with_suffix(".pdf"), bbox_inches=bbox)
    fig.savefig(out.with_suffix(".png"), dpi=350, bbox_inches=bbox)
    plt.close(fig)
print("Drew all seven contradiction panels with lowercase vertex notation.")


# Draw the proper four-coloring with the same coordinates and dimensions.
colors = data["colors_0_to_3"]
assert all(colors[a] != colors[b] for a, b in edges)

# The first three colors and all plotting dimensions match the existing
# qr23_case_* panels. Purple is the fourth color.
palette = ["#3B6FB6", "#E69F00", "#269E6A", "#9B59B6"]
fig, ax = plt.subplots(figsize=(8.6, 7.2))
for a, b in edges:
    ax.plot([coords[a][0], coords[b][0]], [coords[a][1], coords[b][1]],
            color="0.77", lw=0.9, zorder=1)
ax.scatter([x for x, y in coords], [y for x, y in coords], s=230,
           c=[palette[c] for c in colors], edgecolors="black",
           linewidths=0.7, zorder=3)
for old, (x, y) in enumerate(coords):
    ax.text(x + 0.028, y + 0.04, str(labels[old]), ha="left", va="bottom",
            fontsize=11, color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.65, pad=0.15),
            zorder=6)
ax.set_title("A proper four-coloring of G\nvertex colors: 0, 1, 2, 3", fontsize=12)
ax.set_aspect("equal", adjustable="datalim")
ax.axis("off")
ax.margins(0.09)
fig.tight_layout()
out = ROOT / "figures" / "qr23_four_coloring"
fig.canvas.draw()
tight = fig.get_tightbbox(fig.canvas.get_renderer())
width, height = 606.24 / 72, 504.64 / 72
bbox = Bbox.from_bounds((tight.x0 + tight.x1 - width) / 2,
                       (tight.y0 + tight.y1 - height) / 2, width, height)
fig.savefig(out.with_suffix(".pdf"), bbox_inches=bbox)
fig.savefig(out.with_suffix(".png"), dpi=350, bbox_inches=bbox)
plt.close(fig)
print(f"Wrote {out.name}.pdf and .png; all 45 edges have distinct endpoint colors.")
