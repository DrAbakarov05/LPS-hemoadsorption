"""Recover annual central-curve values from the publisher's Figure 2A.

These are approximate digitized values, not the authors' underlying dataset.
Three published text values replace the corresponding digitized estimates.
Run with an already downloaded figure PNG to avoid a network request.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import urllib.request
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
URL = "https://media.springernature.com/full/springer-static/image/art%3A10.1186%2Fs13054-026-06024-7/MediaObjects/13054_2026_6024_Fig2_HTML.png"
ANCHORS = {2000: 9.15, 2023: 12.77, 2050: 20.32}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--figure", type=Path)
    args = parser.parse_args()
    path = args.figure
    if path is None:
        path = ROOT / "sources/critical_care_figure2_download.png"
        path.write_bytes(urllib.request.urlopen(URL, timeout=40).read())
    raw = path.read_bytes()
    im = np.asarray(Image.open(path).convert("RGB")).astype(float)
    if im.shape[:2] != (2064, 1985):
        raise ValueError("Calibration applies only to the publisher's 1985 x 2064 PNG.")
    # Tick centres inspected on the original raster. Fit linear calibrations.
    xt = np.array([418.5, 711.5, 1006.5, 1301.5, 1596.5, 1891.5])
    years = np.arange(2000, 2051, 10)
    yt = np.array([1041.5, 849.5, 659.0, 466.5, 276.5])
    rates = np.array([0, 20, 40, 60, 80])
    xfit = np.polyfit(years - 2000, xt, 1)
    yfit = np.polyfit(yt, rates, 1)
    records = []
    for year in range(2000, 2051):
        x = int(round(np.polyval(xfit, year - 2000)))
        # Central curve is the darkest saturated blue line. Pale country lines
        # and the uncertainty ribbon have much lower blue-channel contrast.
        strip = im[760:995, x - 2:x + 3]
        contrast = np.maximum(0, strip[:, :, 2] - strip[:, :, 0])
        contrast += np.maximum(0, strip[:, :, 2] - strip[:, :, 1])
        score = np.median(contrast, axis=1)
        peak = int(np.argmax(score))
        local = np.arange(max(0, peak - 3), min(len(score), peak + 4))
        weights = np.maximum(score[local] - score[peak] * 0.45, 0)
        py = float(np.average(local, weights=weights)) + 760
        digitized = float(np.polyval(yfit, py))
        value = ANCHORS.get(year, round(digitized, 1))
        records.append({
            "year": year, "asr_per_100000": value,
            "period": "historical" if year <= 2023 else "projected",
            "value_source": "published_text" if year in ANCHORS else "digitized_figure2A_approximate",
            "pixel_x": x, "pixel_y": round(py, 3),
            "raw_digitized_value": round(digitized, 4),
        })
    out = ROOT / "data/critical_care_asr_2000_2050.csv"
    with out.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    provenance = {
        "article_doi": "10.1186/s13054-026-06024-7", "figure": "2A",
        "figure_url": URL, "figure_sha256": hashlib.sha256(raw).hexdigest(),
        "retrieved_date": "2026-10-18", "source_dimensions": [1985, 2064],
        "x_tick_pixels": xt.tolist(), "x_tick_years": years.tolist(),
        "y_tick_pixels": yt.tolist(), "y_tick_rates": rates.tolist(),
        "published_exact_anchors": ANCHORS,
        "intermediate_precision": "0.1 per 100000; approximate figure digitization, not raw data",
        "forecast_starts": 2024, "historical_ends": 2023,
        "population": "adults age >=20; 79 countries; WHO Mortality Database",
        "definition": "explicit sepsis underlying/primary cause; age-standardized rate",
        "uncertainty": "No confidence or prediction ribbon is drawn. Digitization error has not been estimated as a statistical CI.",
        "method": "Linear axis calibration; median blue contrast over a 5-pixel strip; weighted line-centre estimate; three published anchors override pixels.",
    }
    (ROOT / "sources/critical_care_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(records)} annual values, 48 digitized and 3 published anchors.")


if __name__ == "__main__":
    main()
