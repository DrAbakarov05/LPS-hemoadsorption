"""Two independent mortality series on a uniform 1990-2050 timeline.

Transparent charts and a shared scene for editable PowerPoint objects.
Right axis: adult >=20 ASR in 79 countries, NOT the GBD crude rate.
Uses checked-in CSV only. All drawing coordinates are CSS pixels.
"""
from pathlib import Path
import csv
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"


def read_csv(name):
    with (ROOT / "data" / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_scene():
    s = json.loads((ROOT / "style.json").read_text())
    counts = read_csv("sepsis_deaths_1990_2021.csv")
    rates = read_csv("critical_care_asr_2000_2050.csv")
    assert [int(r["year"]) for r in counts] == list(range(1990, 2022))
    assert [int(r["year"]) for r in rates] == list(range(2000, 2051))
    assert {int(r["year"]): float(r["asr_per_100000"]) for r in rates if r["value_source"] == "published_text"} == {2000: 9.15, 2023: 12.77, 2050: 20.32}
    x0, y0, w, h = s["plot_frame_px"]
    x = lambda year: x0 + (year - 1990) / 60 * w
    y = lambda value: y0 + h * (1 - value / s["axis_max"])
    core, labels = [], []

    def line(name, points, color, lw=1, dash=False, target=core):
        target.append(dict(kind="line", name=name, points=points, color=color, width=lw, dash=dash))

    def text(name, value, left, top, width, height, size=18, color=None, bold=False, align="left", target=labels):
        target.append(dict(kind="text", name=name, text=value, left=left, top=top,
                           width=width, height=height, size=size, color=color or s["text_color"], bold=bold, align=align))

    # Two different units, separate axes. Matching numeric limits do not convert
    # a million deaths into deaths per 100000 or make the study populations equal.
    for value in range(0, 26, 5):
        line(f"grid_{value}", [[x0, y(value)], [x0 + w, y(value)]], s["grid_color"], .65)
        text(f"left_tick_{value}", str(value), x0-48, y(value)-12, 36, 25, 17, s["count_color"], align="right", target=core)
        text(f"right_tick_{value}", str(value), x0+w+13, y(value)-12, 38, 25, 17, s["rate_color"], target=core)
    line("left_axis", [[x0,y0],[x0,y0+h]], s["count_color"], 1)
    line("right_axis", [[x0+w,y0],[x0+w,y0+h]], s["rate_color"], 1)
    line("time_axis", [[x0,y0+h],[x0+w,y0+h]], s["axis_color"], 1)
    for year in range(1990,2051):
        major = year % 5 == 0
        line(f"year_tick_{year}", [[x(year),y0+h],[x(year),y0+h+(7 if major else 3)]],s["axis_color"],.8)
        if major:
            text(f"year_label_{year}",str(year),x(year)-25,y0+h+14,50,26,16,s["text_color"],align="center",target=core)
    core.append(dict(kind="rect",name="covid_2020_2021",left=x(2019.5),top=y0,
                     width=x(2021.5)-x(2019.5),height=h,color=s["covid_color"],line_width=1.6,fill="none"))
    cp = [[x(int(r["year"])),y(int(r["total_deaths"])/1e6)] for r in counts]
    hist = [[x(int(r["year"])),y(float(r["asr_per_100000"]))] for r in rates if int(r["year"])<=2023]
    future = [[x(int(r["year"])),y(float(r["asr_per_100000"]))] for r in rates if int(r["year"])>=2023]
    line("GBD_total_deaths_1990_2021",cp,s["count_color"],s["line_width"])
    line("ASR_historical_2000_2023",hist,s["rate_color"],s["line_width"])
    line("ASR_forecast_2024_2050",future,s["rate_color"],s["line_width"],True)
    for year in [1990,2019,2020,2021]:
        core.append(dict(kind="circle",name=f"count_marker_{year}",cx=x(year),cy=y(int(counts[year-1990]["total_deaths"])/1e6),radius=4.5 if year>=2019 else 3.5,color=s["count_color"]))
    for year in [2000,2023,2050]:
        core.append(dict(kind="circle",name=f"ASR_marker_{year}",cx=x(year),cy=y(float(rates[year-2000]["asr_per_100000"])),radius=4,color=s["rate_color"]))
    text("title","Смертность, связанная с сепсисом",96,28,1100,48,32,bold=True)
    text("count_axis_title","Число смертей, млн",96,112,420,28,19,s["count_color"],True)
    text("rate_axis_title","ASR на 100 000",846,112,338,28,19,s["rate_color"],True,"right")
    text("covid_label","COVID-19, 2020–2021",x(2020.5)-130,145,260,24,16,s["covid_color"],True,"center")
    text("count_start","16,5",x(1990)+8,y(16.5)-34,90,30,21,s["count_color"],True)
    text("pre_covid_low","14,1",x(2019)-75,y(14.1)+14,65,30,21,s["count_color"],True)
    text("count_end","21,4 млн (2021)",x(2021)+20,y(21.4)-33,215,31,21,s["count_color"],True)
    line("count_end_leader",[[x(2021)+4,y(21.4)-4],[x(2021)+17,y(21.4)-17]],s["count_color"],1,target=labels)
    text("rate_start","9,15",x(2000)+10,y(9.15)+14,85,30,20,s["rate_color"],True)
    text("rate_2023","12,77 (2023)",x(2023)+12,y(12.77)+10,200,30,20,s["rate_color"],True)
    text("rate_2050","20,32 (2050)",x(2050)-184,y(20.32)-34,175,30,20,s["rate_color"],True,"right")
    text("forecast_label","Прогноз 2024–2050",845,262,270,28,19,s["rate_color"])
    text("count_caption","Число смертей: GBD / Lancet, все возрасты",96,594,535,30,17,s["count_color"])
    text("rate_caption","ASR: Critical Care, ≥20 лет, 79 стран",662,594,555,30,17,s["rate_color"])
    text("method_note","У исследований разные определения и охват. Кривые не образуют единый ряд и не пересчитываются друг в друга.",96,637,1120,24,12.5,s["muted_color"])
    text("digitization_note","ASR: 2000, 2023 и 2050 — опубликованные числа; промежуточные точки приближённо восстановлены по рис. 2A.",96,661,1120,24,12.5,s["muted_color"])
    text("doi_note","Источники: 10.1016/S2214-109X(25)00356-0, табл. S6; 10.1186/s13054-026-06024-7, рис. 2A.",96,686,1120,23,12,s["muted_color"])
    return {"canvas":[1280,720],"style":s,"core":core,"annotations":labels}


def render(scene,mode,destination,dpi=600,transparent=True):
    plt.rcParams.update({"font.family":scene["style"]["font_family"],"svg.fonttype":"none","svg.hashsalt":"global-sepsis-two-series-v2"})
    fig=plt.figure(figsize=(1280/96,720/96),dpi=96)
    ax=fig.add_axes([0,0,1,1],xlim=(0,1280),ylim=(720,0));ax.axis("off")
    items=scene["core"] if mode=="clean" else scene["annotations"] if mode=="annotations" else scene["core"]+scene["annotations"]
    for item in items:
        k=item["kind"]
        if k=="line":
            xx,yy=zip(*item["points"])
            artist,=ax.plot(xx,yy,color=item["color"],lw=item["width"]*.75,linestyle=(0,(5,3)) if item["dash"] else "solid",solid_capstyle="round",solid_joinstyle="round")
        elif k=="rect":
            artist=Rectangle((item["left"],item["top"]),item["width"],item["height"],facecolor="none",edgecolor=item["color"],lw=item["line_width"]*.75);ax.add_patch(artist)
        elif k=="circle":
            artist=Circle((item["cx"],item["cy"]),item["radius"],facecolor=item["color"],edgecolor="white",lw=.8);ax.add_patch(artist)
        else:
            left=item["left"]+(item["width"]/2 if item["align"]=="center" else item["width"] if item["align"]=="right" else 0)
            artist=ax.text(left,item["top"]+2,item["text"],ha=item["align"],va="top",color=item["color"],fontsize=item["size"]*.75,weight="bold" if item["bold"] else "normal")
        artist.set_gid(item["name"])
    fig.savefig(destination,dpi=dpi,transparent=transparent,facecolor="none" if transparent else "white")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True);scene=make_scene()
    (OUT/"editable_scene.json").write_text(json.dumps(scene,ensure_ascii=False,indent=2)+"\n")
    for mode in ["clean","annotated"]:
        for ext in ["png","svg"]:render(scene,mode,OUT/f"sepsis_combined_{mode}.{ext}")
    render(scene,"annotations",OUT/"sepsis_annotations_only.svg")
    render(scene,"annotated",OUT/"sepsis_combined_preview.png",dpi=144,transparent=False)
    summary={"time_range":[1990,2050],"time_scale":"linear; 1 year = 18.1333333333 px on 1280px canvas","absolute_series_years":[1990,2021],"rate_series_years":[2000,2050],"historical_rate_years":[2000,2023],"forecast_rate_years":[2024,2050],"left_axis_unit":"million deaths","right_axis_unit":"age-standardized deaths per 100000","rate_population":"adults >=20, 79 countries, explicit underlying sepsis cause","counts_population":"GBD worldwide, all ages, sepsis-related deaths","png_pixels":[8000,4500],"png_dpi":600,"background":"transparent","approximation":"48 intermediate annual ASR points digitized; 3 published anchors exact to reported precision.","uncertainty_ribbons":"omitted by design; source uncertainty is not zero"}
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print("Rendered clean, annotated and annotation-only versions.")


if __name__=="__main__":main()
