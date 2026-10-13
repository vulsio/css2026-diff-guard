# 共通スタイル(論文図用)。Okabe-Ito 系の CVD 安全色 + 控えめなグリッド。
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE = "#0072B2"      # 通常データ
VERMILION = "#D55E00" # FAIL / 閾値超過の強調
GRAY = "#999999"      # 補助線・注釈

# SLIDE=1 のときはスライド用(大きめの文字、SVG を ../slide/figs/ に出力)
SLIDE = os.environ.get("SLIDE") == "1"

def setup():
    base = 13 if SLIDE else 7.5
    plt.rcParams.update({
        "font.size": base,
        "axes.labelsize": base,
        "axes.titlesize": base,
        "xtick.labelsize": base - 0.5,
        "ytick.labelsize": base - 0.5,
        "legend.fontsize": base - 0.5,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "axes.edgecolor": "#444444",
        "axes.grid": True,
        "grid.color": "#dddddd",
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "figure.dpi": 200,
    })


def figsize(paper, slide):
    """論文用とスライド用で figure サイズを切り替える."""
    return slide if SLIDE else paper


def save(fig, name):
    """論文用は ../doc/figures/<name>.pdf、スライド用は ../slide/figs/<name>.svg."""
    if SLIDE:
        os.makedirs("../slide/figs", exist_ok=True)
        out = f"../slide/figs/{name}.svg"
    else:
        out = f"../doc/figures/{name}.pdf"
    fig.savefig(out)
    print(f"wrote {out}")
