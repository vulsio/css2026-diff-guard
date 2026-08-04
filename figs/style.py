# 共通スタイル(論文図用)。Okabe-Ito 系の CVD 安全色 + 控えめなグリッド。
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BLUE = "#0072B2"      # 通常データ
VERMILION = "#D55E00" # FAIL / 閾値超過の強調
GRAY = "#999999"      # 補助線・注釈

def setup():
    plt.rcParams.update({
        "font.size": 7.5,
        "axes.labelsize": 7.5,
        "axes.titlesize": 7.5,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "axes.edgecolor": "#444444",
        "axes.grid": True,
        "grid.color": "#dddddd",
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "pdf.fonttype": 42,
        "figure.dpi": 200,
    })
