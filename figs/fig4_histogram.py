#!/usr/bin/env python3
"""図4: 全 FAIL 行(1,040行)の変動率ヒストグラム(対数軸).

データ: ../data/guard-failures.tsv。パースは stats.py と同一ロジック
(行ごとに rate 抽出、DB 行は detection/KB の max)。
"""
import csv
import re

import numpy as np
from style import setup, BLUE, GRAY
import matplotlib.pyplot as plt

rates = []
with open("../data/guard-failures.tsv") as f:
    rd = csv.reader(f, delimiter="\t")
    next(rd)
    for row in rd:
        run_id, wf, created, event, kind, checks, fail_rows, digest = row[:8]
        if kind != "guard-trip":
            continue
        for ent in fail_rows.split(";;"):
            ent = ent.strip()
            if not ent:
                continue
            m = re.match(r"^(DB|DET_MASTER|DET_OLD)?:(\S+)\s+(.*)$", ent)
            if not m:
                continue
            check = m.group(1) or "PERSRC"
            rest = m.group(3).split()
            if rest and not rest[0].endswith("%") and not rest[0].replace(".", "").isdigit():
                rest = rest[1:]
            rs = [float(x[:-1]) for x in rest if x.endswith("%")]
            if check == "DB":
                rate = max(rs[:2]) if len(rs) >= 2 else (rs[0] if rs else 0.0)
            else:
                rate = rs[0] if rs else 0.0
            rates.append(rate)

print(f"parsed {len(rates)} FAIL rows")
assert len(rates) == 1465, len(rates)

setup()
fig, ax = plt.subplots(figsize=(3.3, 1.28))

vals = np.array([max(r, 0.1) for r in rates])
bins = np.logspace(np.log10(1), np.log10(4000), 40)
ax.hist(vals, bins=bins, color=BLUE, linewidth=0)

for thr, lab, ha, xoff in [(5, "5%", "right", 0.93), (10, "10%", "left", 1.07)]:
    ax.axvline(thr, color=GRAY, linewidth=0.8, linestyle="--")
    ax.text(thr * xoff, ax.get_ylim()[1] * 0.97, lab, ha=ha, va="top",
            fontsize=6.5, color="#555555")

ax.set_xscale("log")
ax.set_xticks([1, 5, 10, 100, 1000])
ax.set_xticklabels(["1", "5", "10", "100", "1000"])
ax.set_xlabel("change rate of FAIL rows (%)")
ax.set_ylabel("rows")
ax.grid(axis="x", visible=False)

fig.tight_layout(pad=0.3)
fig.savefig("../doc/figures/fig4-histogram.pdf")
print("wrote fig4-histogram.pdf")
