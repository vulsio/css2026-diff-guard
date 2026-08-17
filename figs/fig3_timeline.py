#!/usr/bin/env python3
"""図3: 82日間の発動タイムライン(source-episode 50件のガントチャート).

データ: data/episodes.tsv(stats.py の source-episode 出力).
override 導入時点(vuls-data-db の PR マージ日)を縦線で重ねる.
"""
from datetime import datetime

from style import setup, BLUE, GRAY
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

# 表示行(上から)。episodes.tsv の source 名 → 行ラベル
ROWS = [
    ("ubuntu-cve-tracker", "ubuntu"),
    ("microsoft-cvrf", "microsoft"),
    ("suse-oval", "suse"),
    ("rocky-errata", "rocky"),
    ("amazon", "amazon"),
    ("fedora-api", "fedora"),
    ("cpe(nvd/vulncheck/jvn...)", "cpe"),
    ("vulncheck-nist-nvd2", "cpe"),  # per-source 化後の cpe_* は cpe 行に併合
    ("debian-security-tracker", "debian"),
    ("alma-errata", "alma"),
    ("oracle-linux", "oracle"),
    ("redhat-vex", "redhat"),
]
LABELS = []
for _, lab in ROWS:
    if lab not in LABELS:
        LABELS.append(lab)
ROW_OF = {src: LABELS.index(lab) for src, lab in ROWS}

# override 導入(PR マージ日, UTC)。ラベルは同一高さに揃え、水平寄せで衝突回避
OVERRIDES = [
    ("2026-05-21", "seed", "right"),        # PR #152/#153 初期シード
    ("2026-05-25", "snap", "left"),        # PR #156 ubuntu:snap
    ("2026-06-11", "windows", "right"),      # PR #167 windows detection 27件
    ("2026-06-15", "rocky", "left"),         # PR #169 rocky_10
    ("2026-07-14", "per-source", "right"),   # PR #196 per-source 化
    ("2026-08-04", "grooming", "left"),      # PR #209 2026-08 grooming で override 再導出
]

episodes = []
with open("data/episodes.tsv") as f:
    header = f.readline()
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 8:
            continue
        onset = datetime.strptime(parts[0], "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"2026-{parts[1]}", "%Y-%m-%d %H:%M")
        episodes.append((onset, end, parts[2]))
assert len(episodes) == 69, len(episodes)

setup()
fig, ax = plt.subplots(figsize=(6.7, 2.1))

MIN_W = 6 / 24  # 短い episode も見えるよう最小幅 6h
for onset, end, src in episodes:
    y = ROW_OF[src]
    x0 = mdates.date2num(onset)
    w = max(mdates.date2num(end) - x0, MIN_W)
    ax.barh(y, w, left=x0, height=0.55, color=BLUE, linewidth=0)

for d, label, ha in OVERRIDES:
    x = mdates.date2num(datetime.strptime(d, "%Y-%m-%d"))
    ax.axvline(x, color=GRAY, linewidth=0.7, linestyle=":")
    dx = {"left": 0.3, "right": -0.3, "center": 0}[ha]
    ax.text(x + dx, -0.75, label, ha=ha, va="bottom",
            fontsize=6, color="#666666")

ax.set_yticks(range(len(LABELS)))
ax.set_yticklabels(LABELS)
ax.set_ylim(len(LABELS) - 0.4, -1.15)  # 上から並べ、override ラベル分の余白
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
ax.set_xlim(mdates.date2num(datetime(2026, 4, 23)),
            mdates.date2num(datetime(2026, 8, 18)))
ax.grid(axis="y", visible=False)

fig.tight_layout(pad=0.3)
fig.savefig("../docs/figures/fig3-timeline.pdf")
print("wrote fig3-timeline.pdf")
