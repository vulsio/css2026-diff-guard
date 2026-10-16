#!/usr/bin/env python3
"""図2: 導入前ベンチマーク(2026-02-15..03-29, 連続1日ペア35組)の最大変動率.

データ: diff-guard 設計ドキュメントの 44 日間ベンチマーク表(35 ペア)からの転記.
"""
from style import setup, figsize, save, BLUE, VERMILION, GRAY, SLIDE
import matplotlib.pyplot as plt

# スライド版はリニア軸(対数軸は読み慣れない聴衆に伝わりにくい)。論文版は対数のまま
LINEAR = SLIDE

# (ペア終端日ラベル, max drift %, FAIL か)
PAIRS = [
    ("02-16", 0.1, False), ("02-17", 1.6, False), ("02-18", 6.2, False),
    ("02-19", 2.6, False), ("02-20", 5.9, False), ("02-21", 0.4, False),
    ("02-22", 0.0, False), ("02-23", 0.0, False), ("02-24", 4.4, False),
    ("02-25", 3.9, False), ("02-26", 0.2, False), ("02-27", 0.2, False),
    ("02-28", 0.1, False), ("03-01", 1.0, False), ("03-02", 0.1, False),
    ("03-03", 0.2, False), ("03-04", 65.1, True), ("03-05", 2.9, False),
    ("03-06", 1.5, False), ("03-07", 16.1, True), ("03-08", 0.0, False),
    ("03-09", 0.1, False),
    # gap: 03-09..03-16 はデータ欠落(ディスク不足)
    ("03-17", 1.0, False), ("03-18", 0.6, False), ("03-19", 0.3, False),
    ("03-20", 0.3, False), ("03-21", 0.2, False), ("03-22", 0.1, False),
    ("03-23", 0.1, False), ("03-24", 2.0, False), ("03-25", 0.4, False),
    ("03-26", 0.4, False), ("03-27", 1.0, False), ("03-28", 0.2, False),
    ("03-29", 0.3, False),
]
GAP_AFTER = 21  # index of "03-09" — この後に欠測ギャップ
FLOOR = 0.05    # log 軸表示用の下駄(0.0% はこの値で描く)

setup()
fig, ax = plt.subplots(figsize=figsize((3.3, 1.22), (9.0, 2.5)))

xs, vals, colors = [], [], []
x = 0
gap_x = None
for i, (label, v, fail) in enumerate(PAIRS):
    if i == GAP_AFTER + 1:
        gap_x = (x, x + 1)
        x += 2  # 欠測ギャップぶんの空き
    xs.append(x)
    vals.append(max(v, FLOOR))
    colors.append(VERMILION if fail else BLUE)
    x += 1

ax.bar(xs, vals, width=0.75, color=colors, linewidth=0)
ax.axhline(10, color="#555555" if SLIDE else GRAY, linewidth=2.0 if SLIDE else 0.8, linestyle="--")
note_fs = 13 if SLIDE else 6.5
small_fs = 12 if SLIDE else 5.5
if SLIDE:
    ax.text(xs[-1] + 0.5, 10.8, "閾値 10%", ha="right", va="bottom",
            fontsize=15, fontweight="bold", color="#333333", fontfamily="Noto Sans JP")
else:
    ax.text(xs[-1] + 0.5, 10, "threshold 10%", ha="right", va="bottom",
            fontsize=note_fs, color="#555555")
if gap_x:
    ax.axvspan(gap_x[0] - 0.5, gap_x[1] + 0.5, color="#f0f0f0", zorder=0)
    ax.text(sum(gap_x) / 2, 28 if LINEAR else 0.09, "no\ndata", ha="center",
            va="bottom", fontsize=small_fs, color="#888888")

# FAIL 2 点の直接ラベル
for xi, (label, v, fail) in zip(xs, PAIRS):
    if fail:
        ax.text(xi, v + 1 if LINEAR else v * 1.15, f"{v}%", ha="center",
                va="bottom", fontsize=note_fs, color=VERMILION)

if LINEAR:
    ax.set_ylim(0, 75)
    ax.set_yticks([0, 10, 20, 40, 60])
    ax.set_ylabel("変動率 (%)", fontfamily="Noto Sans JP", fontsize=15)
    ax.tick_params(labelsize=15)
else:
    ax.set_yscale("log")
    ax.set_ylim(FLOOR, 300)
    ax.set_yticks([0.1, 1, 10, 100])
    ax.set_yticklabels(["0.1", "1", "10", "100"])
    ax.set_ylabel("max drift rate (%)")
tick_idx = [0, 5, 10, 16, 21, 25, 34]
ax.set_xticks([xs[i] for i in tick_idx])
ax.set_xticklabels([PAIRS[i][0] for i in tick_idx])
ax.set_xlim(-1, xs[-1] + 1)
ax.grid(axis="x", visible=False)

fig.tight_layout(pad=0.3)
save(fig, "fig2-benchmark")
