"""Presentation-ready annual global sepsis mortality; published Table S6.

Run: python figures/sepsis_global/plot_sepsis.py
Input: data/sepsis_deaths_1990_2021.csv; appearance: style.json.
Transparent PNG and editable SVG, plus outlined SVG and white README preview.
"""
from pathlib import Path
import csv
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import MultipleLocator

ROOT = Path(__file__).resolve().parent


def main():
    style = json.loads((ROOT / "style.json").read_text())
    with (ROOT / "data/sepsis_deaths_1990_2021.csv").open() as file:
        data = [{k: int(v) for k, v in r.items()} for r in csv.DictReader(file)]
    assert [r["year"] for r in data] == list(range(1990, 2022))
    for r in data:
        assert r["total_ui95_lower"] < r["total_deaths"] < r["total_ui95_upper"]
        assert r["sum_rounded_components"] == r["infectious_deaths"] + r["noninfectious_deaths"]
    year = np.array([r["year"] for r in data])
    # Use the directly published total, avoiding rounding errors from categories.
    total, low, high = [np.array([r[k] for r in data]) / 1e6 for k in
                        ["total_deaths", "total_ui95_lower", "total_ui95_upper"]]
    plt.rcParams.update({
        "font.family": style["font_family"], "font.size": 10,
        "text.color": style["text_color"], "axes.labelcolor": style["muted_color"],
        "xtick.color": style["muted_color"], "ytick.color": style["muted_color"],
        "svg.fonttype": "none", "svg.hashsalt": "sepsis-global-s6-v1",
        "axes.unicode_minus": False, "savefig.transparent": True,
    })
    fig = plt.figure(figsize=(style["width_inches"], style["height_inches"]))
    ax = fig.add_axes([0.078, 0.255, 0.865, 0.505])
    fig.text(0.078, 0.927, style["title"], fontsize=25, weight="bold")
    fig.text(0.078, 0.880, style["subtitle"], fontsize=9.5, color=style["muted_color"])
    fig.text(0.078, 0.800, "Число смертей в год, млн", fontsize=10.5, weight="medium")

    # The rectangle groups ANNUAL estimates 2020 and 2021, not exact daily dates.
    ax.add_patch(Rectangle((2019.5, 0), 2, style["y_max_millions"],
                          facecolor=style["covid_color"], alpha=style["covid_fill_alpha"], zorder=0))
    ax.add_patch(Rectangle((2019.5, 0), 2, style["y_max_millions"],
                          fill=False, edgecolor=style["covid_color"], linewidth=0.9,
                          alpha=0.75, zorder=1, clip_on=False))
    ax.fill_between(year, low, high, color=style["ribbon_color"],
                    alpha=style["ribbon_alpha"], linewidth=0, zorder=2)
    ax.plot(year, total, color=style["line_color"], lw=style["line_width"],
            solid_capstyle="round", solid_joinstyle="round", zorder=3)
    # Continuous curve with its final portion emphasized, not a second series.
    ax.plot(year[-3:], total[-3:], color=style["covid_color"],
            lw=style["line_width"], solid_capstyle="round", zorder=4)
    for index in [0, 29, 30, 31]:
        color = style["covid_color"] if index >= 30 else style["line_color"]
        ax.scatter(year[index], total[index], s=38, facecolor=color,
                   edgecolor="white", lw=1.0, zorder=5)
    # Explicit labels for the start, pre-pandemic low and both pandemic years.
    labels = [(0, (8, 15), "left"), (29, (-13, -25), "right"),
              (30, (-17, 12), "right"), (31, (-10, 15), "right")]
    for index, offset, align in labels:
        ax.annotate(f"{total[index]:.1f}".replace(".", ","),
                    (year[index], total[index]), xytext=offset,
                    textcoords="offset points", ha=align, fontsize=16, weight="bold",
                    color=style["covid_color"] if index >= 30 else style["line_color"], zorder=6)
    ax.text(2020.5, 26.2, "COVID-19", ha="center", va="bottom", fontsize=12,
            color=style["covid_color"], weight="bold", clip_on=False)
    ax.text(2020.5, 25.35, "2020–2021", ha="center", va="bottom", fontsize=9,
            color=style["covid_color"], clip_on=False)

    ax.set(xlim=(1989.6, 2021.8), ylim=(0, style["y_max_millions"]))
    ax.set_xticks([1990, 1995, 2000, 2005, 2010, 2015, 2019, 2020, 2021])
    ax.set_yticks([0, 5, 10, 15, 20, 25])
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.tick_params(axis="both", which="major", length=0, pad=10, labelsize=10)
    ax.tick_params(axis="x", which="minor", length=3, color="#A8B5C1")
    for label in ax.get_xticklabels()[-3:]:
        label.set_fontsize(8.5)
    ax.grid(axis="y", color="#9CAEBF", alpha=0.24, linewidth=0.7)
    ax.set_axisbelow(True)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#A8B5C1")
    ax.spines["bottom"].set_linewidth(0.7)
    ax.set_xlabel("Год", loc="right", labelpad=13, fontsize=10)
    ax.legend(handles=[
        Line2D([0], [0], color=style["line_color"], lw=3, label="Суммарное число смертей"),
        Patch(facecolor=style["ribbon_color"], alpha=style["ribbon_alpha"],
              edgecolor="none", label="95% интервал неопределённости"),
    ], loc="lower left", bbox_to_anchor=(0.0, 0.035), frameon=False,
       ncol=1, fontsize=9, handlelength=2.7, labelspacing=0.8)

    # Date context makes the end of the observation series unambiguous.
    fig.text(0.078, 0.143, "COVID-19: ВОЗ охарактеризовала вспышку как пандемию 11.03.2020.",
             fontsize=9, color=style["covid_color"])
    fig.text(0.078, 0.116,
             "Красная область — 2020–2021: два года в данных; наблюдение заканчивается в 2021 году.",
             fontsize=8.7, color=style["muted_color"])
    fig.text(0.078, 0.069,
             "Источник: GBD 2021 Global Sepsis Collaborators. Lancet Glob Health. 2025;13:e2013–e2026. Приложение 1, табл. S6.",
             fontsize=7.5, color=style["muted_color"])
    fig.text(0.078, 0.046,
             "doi:10.1016/S2214-109X(25)00356-0 · Опубликованные модельные оценки; значения округлены авторами.",
             fontsize=7.5, color=style["muted_color"])
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    stem = "sepsis_global_total_1990_2021"
    meta = {"Title": style["title"], "Description":
            "Adapted from GBD 2021 Global Sepsis Collaborators (2025), Supplementary appendix 1, Table S6. "
            "DOI:10.1016/S2214-109X(25)00356-0. All causes combined; annual published estimates and 95% UI."}
    fig.savefig(out / f"{stem}.svg", transparent=True, metadata=meta)
    fig.savefig(out / f"{stem}.png", dpi=style["png_dpi"], transparent=True,
                metadata={"Title": style["title"], "Source": meta["Description"]})
    with plt.rc_context({"svg.fonttype": "path"}):
        fig.savefig(out / f"{stem}_outlined.svg", transparent=True, metadata=meta)
    fig.savefig(out / f"{stem}_preview.png", dpi=150, transparent=False, facecolor="white")
    summary = {
        "years": [int(year[0]), int(year[-1])], "annual_points": len(year),
        "data_source": "Supplementary appendix 1, Table S6, All Causes, Death Counts (95% UI)",
        "covid_annual_highlight": [2020, 2021], "pandemic_characterized_by_who": "2020-03-11",
        "global_emergency_ended": "2023-05-05",
        "covid_note": "Highlight ends at last study year, not at the end of the pandemic.",
        "png_dimensions": [round(style["width_inches"] * style["png_dpi"]),
                           round(style["height_inches"] * style["png_dpi"])],
        "png_dpi": style["png_dpi"], "png_background": "transparent",
        "svg_text_editable": True,
        "key_years": {str(r["year"]): r for r in data if r["year"] in [1990, 2019, 2020, 2021]},
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    plt.close(fig)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
