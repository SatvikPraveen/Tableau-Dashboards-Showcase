"""Quantitative audit of the published dashboards against the source data.

For every headline number visible in the committed dashboard screenshots, this
module (1) reproduces the number from the raw IHME file using the aggregation
the workbook actually performs, and (2) computes the value an analyst would
report with the aggregation the data's structure requires. Agreement in (1)
is the evidence that the diagnosis of the workbook's behaviour is correct.

    python -m tools.audit            # print the report
    python -m tools.audit --write    # regenerate docs/analytical_audit.md
    python -m tools.audit --check    # fail if the committed report is stale
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import ihme, paths

OUTPUT = paths.DOCS_DIR / "analytical_audit.md"

# Values read off the committed screenshots. Each is a regression target:
# tests/test_audit.py asserts the audit reproduces it exactly.
PUBLISHED = {
    "mortality_total_by_year": {  # Images/Dashboard1_Time_Series_Number_of_Deaths.png
        1970: 172_866_152,
        1980: 175_767_051,
        1990: 185_702_142,
        2000: 204_052_611,
        2010: 210_567_809,
    },
    "mortality_pct_change": {1980: 2, 1990: 6, 2000: 10, 2010: 3},  # same image, rounded
    "mortality_total_deaths_kpi": 948_955_765,  # Images/Dashboard2_Global_Mortality_Rate.png
    "mortality_median_rate_kpi": 825.0,  # same image
    "spending_per_person_legend": (35_090, 70_790),  # Images/Dashboard1_Statewise_...png
    "spending_standardized_legend": (44_710, 69_830),  # same image
    "spending_kpi_2015_per_person": 483_460,  # same image, truncated to "483,46"
    "spending_kpi_2015_standardized": 519_250,  # same image, truncated to "519,25"
    # Images/Dashboard2_Healthcare_Fractional_Expenditure_by_State_and_Year.png (Year 2015, Alaska)
    "spending_dashboard2_alaska_2015": {
        "Fraction Private": 31,
        "Fraction Medicare": 9,
        "Fraction Medicaid": 17,
        "Fraction OOP": 43,
    },
}

MORTALITY_IMG_TS = "01_Global_Mortality_Analysis/Images/Dashboard1_Time_Series_Number_of_Deaths.png"
MORTALITY_IMG_MAP = "01_Global_Mortality_Analysis/Images/Dashboard2_Global_Mortality_Rate.png"
SPENDING_IMG_2 = (
    "02_Cost_of_Care_US_State_Healthcare_Spending_Analysis/Images/"
    "Dashboard2_Healthcare_Fractional_Expenditure_by_State_and_Year.png"
)
SPENDING_WORKBOOK = paths.SPENDING_DIR / "Statewise_Healthcare_Spending_Analysis.twb"
SPENDING_IMG_1 = (
    "02_Cost_of_Care_US_State_Healthcare_Spending_Analysis/Images/"
    "Dashboard1_Statewise_Spending_Insights_Per_Person_and_Standardized_Metrics.png"
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def continent_mapping(workbook=paths.MORTALITY_DIR / "Global_Mortality_Analysis.twb") -> Tuple[Dict[str, str], str]:
    """Evaluate the workbook's ``Continent`` calculated field.

    Returns ``(first-match mapping, default label)``. The formula is an
    ``IF [Country Name] IN (...) THEN "X" ELSEIF ... ELSE "Other" END`` chain;
    Tableau uses the first branch that matches, and so does this function.
    """
    root = ET.parse(workbook).getroot()
    formula = next(
        c.find("calculation").get("formula")
        for c in root.iter("column")
        if c.get("caption") == "Continent" and c.find("calculation") is not None
    )
    mapping: Dict[str, str] = {}
    pending: List[str] = []
    in_list = False
    for token in re.finditer(r'IN\s*\(|"[^"]*"|\)|THEN\s*"([^"]*)"|ELSE\s*"([^"]*)"\s*END', formula):
        text = token.group(0)
        if text.startswith("IN"):
            in_list, pending = True, []
        elif in_list and text.startswith('"'):
            pending.append(text.strip('"'))
        elif text == ")":
            in_list = False
        elif token.group(1) is not None:
            for name in pending:
                mapping.setdefault(name, token.group(1))
        elif token.group(2) is not None:
            return mapping, token.group(2)
    return mapping, "Other"


def worksheets_using(field_ref: str, workbook=paths.MORTALITY_DIR / "Global_Mortality_Analysis.twb") -> List[str]:
    """Names of worksheets whose XML references ``field_ref`` (e.g. ``sum:Number of Deaths``)."""
    root = ET.parse(workbook).getroot()
    return sorted(ws.get("name") for ws in root.iter("worksheet") if field_ref in ET.tostring(ws, encoding="unicode"))


def calculated_field_usage(workbook=SPENDING_WORKBOOK) -> Dict[str, List[str]]:
    """Map each calculated field caption to the worksheets that reference it."""
    root = ET.parse(workbook).getroot()
    internal: Dict[str, str] = {}
    for column in root.iter("column"):
        if column.get("caption") and column.find("calculation") is not None:
            internal.setdefault(column.get("caption"), column.get("name", "").strip("[]"))
    sheets = {ws.get("name"): ET.tostring(ws, encoding="unicode") for ws in root.iter("worksheet")}
    return {
        caption: sorted(name for name, xml in sheets.items() if f":{ref}:" in xml) for caption, ref in internal.items()
    }


def _code_list(names: List[str]) -> str:
    return ", ".join(f"`{n}`" for n in names)


def fmt(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}"


@dataclass
class Finding:
    ident: str
    title: str
    severity: str  # "High" | "Medium" | "Low" | "Info"
    status: str  # "Confirmed" | "Verified OK" | "Caveat"
    where: str
    evidence: List[str]
    table: Optional[List[List[str]]] = None
    remedy: str = ""


# --------------------------------------------------------------------------- #
# Mortality findings
# --------------------------------------------------------------------------- #


def mortality_findings(rows: List[ihme.MortalityRow]) -> Tuple[List[Finding], Dict[str, object]]:
    naive = defaultdict(float)
    correct = defaultdict(float)
    for r in rows:
        naive[r.year] += r.deaths
        if r.is_canonical_total:
            correct[r.year] += r.deaths
    years = sorted(correct)
    ratios = {y: naive[y] / correct[y] for y in years}

    pct_naive = {y: 100 * (naive[y] - naive[p]) / naive[p] for p, y in zip(years, years[1:])}
    pct_correct = {y: 100 * (correct[y] - correct[p]) / correct[p] for p, y in zip(years, years[1:])}

    median_pooled = statistics.median(r.rate_per_100k for r in rows)
    max_rate = max(r.rate_per_100k for r in rows)
    sum_deaths_sheets = worksheets_using("sum:Number of Deaths")
    sum_rate_sheets = worksheets_using("sum:Death Rate Per 100,000")
    median_country_year = statistics.median(r.rate_per_100k for r in rows if r.is_canonical_total)
    median_2010 = statistics.median(r.rate_per_100k for r in rows if r.is_canonical_total and r.year == 2010)

    summed_rate = defaultdict(float)
    for r in rows:
        summed_rate[r.country_name] += r.rate_per_100k
    worst_country, worst_sum = max(summed_rate.items(), key=lambda kv: kv[1])

    mapping, default = continent_mapping()
    in_data = sorted({r.country_name for r in rows})
    unmapped = [c for c in in_data if c not in mapping]
    unmapped_deaths_2010 = {
        r.country_name: r.deaths for r in rows if r.country_name in unmapped and r.is_canonical_total and r.year == 2010
    }

    stats = {
        "naive_by_year": dict(naive),
        "correct_by_year": dict(correct),
        "naive_total": sum(naive.values()),
        "correct_total": sum(correct.values()),
        "pct_naive": pct_naive,
        "pct_correct": pct_correct,
        "median_pooled": median_pooled,
        "median_country_year": median_country_year,
        "median_2010": median_2010,
        "max_summed_rate": (worst_country, worst_sum),
        "unmapped": unmapped,
        "unmapped_label": default,
    }

    findings = [
        Finding(
            "M1",
            "Default filters count every death four times",
            "High",
            "Confirmed",
            "Every worksheet that uses `SUM([Number of Deaths])`: "
            + _code_list(sum_deaths_sheets)
            + ". The Sex and Age Group quick filters default to *(All)*.",
            [
                "The CSV stores aggregates alongside their components: `Sex = Both` is the sum of "
                "`Male` and `Female`, and `Age Group = All ages` is the sum of the 20 age bands "
                "(`python -m tools.verify_data` confirms both identities to within rounding).",
                "With both filters on *(All)*, `SUM([Number of Deaths])` adds Male + Female + Both "
                "(2x) across age bands + All ages (2x), i.e. 4x the true count up to rounding.",
                f"The audit reproduces every published value to the death (`{MORTALITY_IMG_TS}`).",
            ],
            [["Year", "Published", "Reproduced (all rows)", "Correct (Both, All ages)", "Ratio"]]
            + [
                [
                    str(y),
                    fmt(PUBLISHED["mortality_total_by_year"][y]),
                    fmt(naive[y]),
                    fmt(correct[y]),
                    f"{ratios[y]:.3f}",
                ]
                for y in years
            ],
            "Make `Sex` and `Age Group` single-value filters without an *(All)* option, defaulting "
            "to `Both` and `All ages`; or exclude the aggregate members with a data-source filter "
            "and let Tableau sum the leaves.",
        ),
        Finding(
            "M2",
            '"Total Deaths" KPI sums snapshot years and double counts',
            "High",
            "Confirmed",
            f"`KPIs-Death_Rate` (`{MORTALITY_IMG_MAP}`)",
            [
                f"Published: **{fmt(PUBLISHED['mortality_total_deaths_kpi'])}**. "
                f"Reproduced as the sum of every row: **{fmt(stats['naive_total'])}**.",
                f"Removing the 4x duplication gives {fmt(stats['correct_total'])}, but that is still "
                "the sum of five single-year snapshots (1970, 1980, 1990, 2000, 2010). It is not the "
                "number of deaths between 1970 and 2010, which would need all 41 years.",
            ],
            remedy="Report deaths for one selected year, or label the KPI explicitly as a sum of "
            "snapshot years after fixing M1.",
        ),
        Finding(
            "M3",
            '"Global Median Death Rate" pools ages, sexes and years',
            "Medium",
            "Confirmed",
            f"`KPIs-Death_Rate` (`{MORTALITY_IMG_MAP}`)",
            [
                f"Published: **{PUBLISHED['mortality_median_rate_kpi']:.1f}**. Reproduced as the median of "
                f"all 58,905 row-level rates: **{median_pooled:.1f}**.",
                "That pool mixes neonatal rates (annualised over a 7-day interval, up to "
                f"{fmt(max_rate, 1)} per 100,000) with adult and all-age rates, so it has no "
                "population interpretation.",
                f"Median all-age, both-sex crude rate across country-years: {median_country_year:.1f}; "
                f"for 2010 alone: {median_2010:.1f}. Both are unweighted medians across countries and are "
                "crude (not age-standardised) rates, so they partly reflect population age structure.",
            ],
            remedy="Compute the median over the `Both` / `All ages` rows for a single year, and state "
            "that it is an unweighted cross-country median of crude rates.",
        ),
        Finding(
            "M4",
            "Death rates are summed",
            "High",
            "Confirmed",
            "Every worksheet that uses `SUM([Death Rate Per 100,000])`: " + _code_list(sum_rate_sheets),
            [
                "Rates are not additive. Summing them across sexes, age bands and years yields "
                f"values such as {fmt(worst_sum)} per 100,000 for {worst_country}, i.e. more than "
                "the population many times over.",
                "The *Countries: Mortality Rate* bar chart and the scatter plot's x axis in the "
                "time-series screenshot run into the millions per 100,000, which is consistent "
                "with these summed rates.",
            ],
            remedy="Use `AVG` only within a single sex/age/year cell, or recompute a rate as "
            "`SUM(deaths) / SUM(population)` with population derived as `deaths / rate * 100000`.",
        ),
        Finding(
            "M5",
            'Two countries fall into the "Other" continent',
            "Low",
            "Confirmed",
            "Calculated field `Continent`",
            [
                "The field is a hard-coded `IF ... IN (...)` list. Evaluating it against the 187 "
                f"country names in the data leaves {', '.join(f'`{c}`' for c in unmapped)} mapped to "
                f'`"{default}"`.',
                "The formula lists `Eswatini`, but the GBD 2010 file uses the earlier name `Swaziland`. "
                "`Taiwan` is not listed at all.",
                "All-age, both-sex deaths affected in 2010: "
                + ", ".join(f"{k} {fmt(v)}" for k, v in sorted(unmapped_deaths_2010.items()))
                + ".",
            ],
            remedy='Add `"Swaziland"` to the Africa list and `"Taiwan"` to the Asia list, or join a '
            "country-to-region lookup keyed on the ISO3 `Country Code` instead of names.",
        ),
        Finding(
            "M6",
            '"% Change in Deaths" is decade-on-decade, not year-over-year',
            "Info",
            "Verified OK",
            "Calculated field `% Change in Deaths`",
            [
                "`LOOKUP(..., -1)` compares adjacent rows, which are 10 years apart in this dataset. "
                "The project documentation previously described it as year-over-year.",
                "Because the 4x duplication in M1 is uniform across years, the percentages are "
                "unaffected by it (table below).",
            ],
            [["Decade ending", "Published (rounded)", "From workbook totals", "From correct totals"]]
            + [
                [str(y), str(PUBLISHED["mortality_pct_change"][y]), f"{pct_naive[y]:.2f}", f"{pct_correct[y]:.2f}"]
                for y in years[1:]
            ],
            'Label the column "% change vs. previous decade".',
        ),
    ]
    return findings, stats


# --------------------------------------------------------------------------- #
# Spending findings
# --------------------------------------------------------------------------- #


def spending_findings(tables: Dict[str, ihme.SpendingTable]) -> Tuple[List[Finding], Dict[str, object]]:
    e9a = tables["Table e9a"].records
    per_person = defaultdict(float)
    standardized = defaultdict(float)
    for rec in e9a:
        per_person[rec["State"]] += rec["Spending per Person"].point
        standardized[rec["State"]] += rec["Standardized Spending per Person"].point
    single_year = [rec["Spending per Person"].point for rec in e9a]

    by_year: Dict[int, List[dict]] = defaultdict(list)
    for rec in e9a:
        by_year[rec["Year"]].append(rec)
    kpi_pp_2015 = sum(r["Spending per Person"].point for r in by_year[2015])
    kpi_std_2015 = sum(r["Standardized Spending per Person"].point for r in by_year[2015])

    # Population is not in the file, but is implied by total / per-person.
    national: Dict[int, Tuple[float, float, float]] = {}
    for year, recs in sorted(by_year.items()):
        total_usd = sum(r["Total Spending"].point * 1e9 for r in recs)
        population = sum(r["Total Spending"].point * 1e9 / r["Spending per Person"].point for r in recs)
        unweighted = statistics.mean(r["Spending per Person"].point for r in recs)
        national[year] = (total_usd / population, unweighted, population)

    def crosses_zero(table: str) -> Dict[str, Tuple[int, int]]:
        out: Dict[str, Tuple[int, int]] = {}
        for column in tables[table].header[1:]:
            ests = [rec[column] for rec in tables[table].records]
            out[column] = (sum(e.lower <= 0 <= e.upper for e in ests), len(ests))
        return out

    zero_d = crosses_zero("Table e9d")
    zero_e = crosses_zero("Table e9e")

    widest = max(
        (
            (rec["State"], rec["Year"], col, est)
            for rec in tables["Table e9b"].records
            for col, est in rec.items()
            if isinstance(est, ihme.Estimate)
        ),
        key=lambda t: t[3].upper - t[3].lower,
    )
    share_sums = [
        sum(v.point for v in rec.values() if isinstance(v, ihme.Estimate)) for rec in tables["Table e9c"].records
    ]
    states, years = ihme.coverage(e9a)

    usage = calculated_field_usage()
    share_fields = sorted(c for c in usage if c.endswith("_fraction_num") or c.endswith("_num_fraction"))
    summed_share_sheets = sorted({ws for c in share_fields for ws in usage[c]})
    growth_fields = sorted(
        c
        for c in usage
        if c.startswith("Num_")
        and c not in {"Num_total_spending", "Num_spending_per_person", "Num_standardized_spending_per_person"}
    )
    unused_growth = [c for c in growth_fields if not usage[c]]
    alaska = next(r for r in tables["Table e9b"].records if r["State"] == "Alaska" and r["Year"] == 2015)
    alaska_points = {k: alaska[k].point for k in PUBLISHED["spending_dashboard2_alaska_2015"]}

    stats = {
        "legend_pp": (min(per_person.values()), max(per_person.values())),
        "legend_std": (min(standardized.values()), max(standardized.values())),
        "single_year_pp": (min(single_year), max(single_year)),
        "kpi_pp_2015": kpi_pp_2015,
        "kpi_std_2015": kpi_std_2015,
        "national": national,
        "zero_d": zero_d,
        "zero_e": zero_e,
        "years": years,
        "states": states,
        "alaska_2015": alaska_points,
        "unused_growth_fields": unused_growth,
        "summed_share_sheets": summed_share_sheets,
    }

    findings = [
        Finding(
            "S1",
            "Year = *(All)* sums per-person spending across five years",
            "High",
            "Confirmed",
            f"`Statewise_Spending_Per_Person`, `State-wise_Standardized_Spending_Per_Person` (`{SPENDING_IMG_1}`)",
            [
                "`Num_spending_per_person` is aggregated with `SUM`. When the year filter is *(All)*, "
                "each state's value is the sum of its five annual per-capita figures.",
            ],
            [
                ["Measure", "Published legend", "Reproduced (sum over 2015-2019)", "Actual single-year range"],
                [
                    "Spending per person (USD)",
                    "{} - {}".format(*map(fmt, PUBLISHED["spending_per_person_legend"])),
                    "{} - {}".format(*map(fmt, stats["legend_pp"])),
                    "{} - {}".format(*map(fmt, stats["single_year_pp"])),
                ],
                [
                    "Standardized spending per person (USD)",
                    "{} - {}".format(*map(fmt, PUBLISHED["spending_standardized_legend"])),
                    "{} - {}".format(*map(fmt, stats["legend_std"])),
                    "n/a",
                ],
            ],
            "Use `AVG` for per-capita measures, or make Year a single-value filter.",
        ),
        Finding(
            "S2",
            "`KPIs_a` adds per-capita values across states",
            "High",
            "Confirmed",
            f"`KPIs_a` (`{SPENDING_IMG_1}`)",
            [
                f"Published 2015 cells (truncated in the screenshot) `483,46...` and `519,25...` equal the "
                f"sum over 51 states: {fmt(kpi_pp_2015)} and {fmt(kpi_std_2015)}. A sum of per-capita "
                "values has no interpretation.",
                "A population-weighted national figure can be recovered without external data, "
                "because population = total spending / spending per person:",
            ],
            [["Year", "Population-weighted USD per person", "Unweighted mean of states", "Implied population (M)"]]
            + [[str(y), fmt(v[0]), fmt(v[1]), fmt(v[2] / 1e6, 1)] for y, v in national.items()],
            "Replace the KPI with `SUM(total spending) / SUM(implied population)`. Totals are "
            "published to 0.1 B USD, so implied populations of the smallest states carry about 1% "
            "rounding error.",
        ),
        Finding(
            "S3",
            "The data file covers 2015-2019 only",
            "Medium",
            "Confirmed",
            "`Dataset/` and project documentation",
            [
                f"Tables e9a-e9c contain {states} states (50 + DC) x years {years[0]}-{years[-1]}. The "
                "file name and earlier documentation say 2003-2019; that is the span of the parent "
                "IHME release, not of this extract.",
                "According to the IHME GHDx record description (not independently re-checked here), "
                "values for 2015-2019 are IHME estimates rather than CMS State Health Expenditure "
                "Accounts figures, which end in 2014.",
            ],
            remedy="Describe the dashboards as 2015-2019 and treat the values as modelled estimates.",
        ),
        Finding(
            "S4",
            "Uncertainty intervals are discarded",
            "Medium",
            "Caveat",
            "All `Num_*` / `*_fraction` calculated fields",
            [
                "Every published value is `point (lower - upper)`; the calculated fields keep only the point estimate.",
                f"Widest payer-share interval: {widest[0]} {widest[1]}, {widest[2]} "
                f"{widest[3].point:g}% ({widest[3].lower:g}%-{widest[3].upper:g}%).",
                "For the growth-rate tables, the share of state intervals that include zero is "
                "shown below. Most payer-specific state growth rates are not distinguishable from "
                "zero, so ranking states by them is not supported by the data.",
            ],
            [["Column", "Table e9d: intervals including 0", "Table e9e: intervals including 0"]]
            + [[col, f"{zero_d[col][0]}/{zero_d[col][1]}", f"{zero_e[col][0]}/{zero_e[col][1]}"] for col in zero_d],
            "Parse `lower` and `upper` as well and show them as error bars or reference bands; "
            "flag states whose interval includes zero.",
        ),
        Finding(
            "S5",
            "Shares are whole percentages",
            "Low",
            "Verified OK",
            "Calculated fields `*_fraction_num`",
            [
                "`INT(LEFT(...))` parsing is lossless: all e9b/e9c cells are integer percentages "
                "(checked by `tools.verify_data`).",
                f"Because of that rounding, a state's service-type shares sum to "
                f"{min(share_sums):g}-{max(share_sums):g}% rather than exactly 100%. Differences of 1-2 "
                "percentage points between states are within rounding.",
            ],
        ),
        Finding(
            "S6",
            "Growth-rate tables need their definitions alongside them",
            "Info",
            "Caveat",
            "Tables e9d / e9e (`Num_*` fields)",
            [
                'The sheets have no title row. Their footnotes read: e9d, "'
                + (tables["Table e9d"].footnote or "").lstrip("* ")
                + '"; e9e, "'
                + (tables["Table e9e"].footnote or "").lstrip("* ")
                + '"',
                "The reference period of the growth rates is not stated in the file. Confirm it "
                "against the IHME codebook before interpreting the values.",
                (
                    f"None of the {len(growth_fields)} calculated fields defined on these tables is used by "
                    f"any worksheet: {_code_list(unused_growth)}."
                    if len(unused_growth) == len(growth_fields)
                    else f"{len(unused_growth)} of the {len(growth_fields)} calculated fields defined on these "
                    f"tables are not used by any worksheet: {_code_list(unused_growth)}."
                ),
            ],
            remedy="Either remove the unused fields, or build a growth-rate view that shows the intervals (see S4).",
        ),
        Finding(
            "S7",
            "Payer and service shares are correct for a single year",
            "Low",
            "Verified OK",
            f"{_code_list(summed_share_sheets)} (`{SPENDING_IMG_2}`)",
            [
                "With Year = 2015 and State = Alaska, as in the screenshot, the KPI tiles show "
                + ", ".join(
                    f"{k.replace('Fraction ', '')} {v}%"
                    for k, v in PUBLISHED["spending_dashboard2_alaska_2015"].items()
                )
                + ". The raw table e9b gives "
                + ", ".join(f"{k.replace('Fraction ', '')} {v:g}%" for k, v in alaska_points.items())
                + ".",
                "These worksheets aggregate the share fields with `SUM`, as in S1. They are correct "
                "only while a single year is selected. With Year = *(All)* each cell becomes the sum "
                "of five annual shares, roughly 5x the true value.",
            ],
            remedy="Use `AVG` for shares, or remove the *(All)* option from the year filter.",
        ),
    ]
    return findings, stats


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


def _table(rows: List[List[str]]) -> List[str]:
    header, *body = rows
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in body]
    return out


def render(findings: List[Finding]) -> str:
    lines = [
        "# Analytical Audit of the Published Dashboards",
        "",
        "<!-- Generated by `python -m tools.audit --write`. Do not edit by hand. -->",
        "",
        "This report checks every headline number in the committed dashboard screenshots",
        "against the raw IHME data. For each finding, the audit first reproduces the",
        "published number using the aggregation the workbook performs. An exact match is",
        "the evidence that the diagnosis is right. It then computes the value that the",
        "structure of the data supports.",
        "",
        "**Scope and evidence.** Findings are based on the workbook XML, the raw data files",
        "and the screenshots in `Images/`. The workbooks were not opened in Tableau Desktop,",
        "and the Tableau Public versions were not inspected. The workbooks are left",
        "unmodified so that they continue to match the published vizzes; the remedies",
        "below are recommendations.",
        "",
        "## Summary",
        "",
        "| ID | Finding | Severity | Status |",
        "|---|---|---|---|",
    ]
    for f in findings:
        lines.append(f"| [{f.ident}](#{f.ident.lower()}) | {f.title} | {f.severity} | {f.status} |")
    lines.append("")
    for f in findings:
        lines += [f'<a id="{f.ident.lower()}"></a>', "", f"## {f.ident}. {f.title}", ""]
        lines += [f"**Severity:** {f.severity} | **Status:** {f.status} | **Where:** {f.where}", ""]
        lines += [f"- {e}" for e in f.evidence]
        lines.append("")
        if f.table:
            lines += _table(f.table) + [""]
        if f.remedy:
            lines += [f"**Remedy.** {f.remedy}", ""]
    lines += [
        "## Reproducing this report",
        "",
        "```bash",
        "python -m tools.verify_data   # checksums, schema and aggregate identities",
        "python -m tools.audit         # recompute every number in this report",
        "python -m unittest            # regression tests pinned to the published values",
        "```",
    ]
    return "\n".join(lines).rstrip() + "\n"


def build() -> Tuple[str, Dict[str, object]]:
    m_findings, m_stats = mortality_findings(ihme.read_mortality())
    s_findings, s_stats = spending_findings(ihme.read_spending())
    return render(m_findings + s_findings), {"mortality": m_stats, "spending": s_stats}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    text, _ = build()
    rel = OUTPUT.relative_to(paths.REPO_ROOT)
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(text, encoding="utf-8")
        print(f"wrote {rel}")
    elif args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != text:
            print(f"{rel} is stale; run `python -m tools.audit --write`.")
            return 1
        print(f"{rel} is up to date.")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
