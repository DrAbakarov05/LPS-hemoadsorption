"""Extract the 32 published annual estimates from a pdftotext -layout excerpt.

The checked-in excerpt is from Supplementary appendix 1, Table S6.
This script uses only Python's standard library and makes no network requests.
"""
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parent
FIELDS = [
    "year", "total_deaths", "total_ui95_lower", "total_ui95_upper",
    "infectious_deaths", "infectious_ui95_lower", "infectious_ui95_upper",
    "noninfectious_deaths", "noninfectious_ui95_lower", "noninfectious_ui95_upper",
    "sum_rounded_components", "total_minus_sum_rounded_components",
]


def main():
    rows = []
    for line in (ROOT / "sources/table_s6_source.txt").read_text().splitlines():
        match = re.match(r"\s*((?:19|20)\d{2})\s+", line)
        if not match:
            continue
        groups = re.findall(r"(\d+)\s+\((\d+)-(\d+)\)", line)
        if len(groups) != 3:
            raise ValueError(f"Expected three death-count groups: {line}")
        values = [int(match[1])] + [int(n) for group in groups for n in group]
        component_sum = values[4] + values[7]
        values += [component_sum, values[1] - component_sum]
        rows.append(dict(zip(FIELDS, values, strict=True)))
    assert [r["year"] for r in rows] == list(range(1990, 2022))
    for row in rows:
        for stem in ["total", "infectious", "noninfectious"]:
            assert row[f"{stem}_ui95_lower"] < row[f"{stem}_deaths"] < row[f"{stem}_ui95_upper"]
    target = ROOT / "data/sepsis_deaths_1990_2021.csv"
    with target.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Extracted {len(rows)} annual rows: {target}")


if __name__ == "__main__":
    main()
