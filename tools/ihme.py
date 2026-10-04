"""Readers for the two IHME source files.

The readers return plain Python records and never modify the source files.
They intentionally avoid pandas/openpyxl so that the audit has no third-party
dependencies.
"""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import paths

# --------------------------------------------------------------------------- #
# GBD 2010 mortality (CSV)
# --------------------------------------------------------------------------- #

MORTALITY_COLUMNS = [
    "Country Code",
    "Country Name",
    "Year",
    "Age Group",
    "Sex",
    "Number of Deaths",
    "Death Rate Per 100,000",
]

# Aggregate members that are sums of other members of the same dimension.
SEX_TOTAL = "Both"
AGE_TOTAL = "All ages"


@dataclass(frozen=True)
class MortalityRow:
    country_code: str
    country_name: str
    year: int
    age_group: str
    sex: str
    deaths: float
    rate_per_100k: float

    @property
    def is_canonical_total(self) -> bool:
        """True for the single row that represents a country-year total."""
        return self.sex == SEX_TOTAL and self.age_group == AGE_TOTAL

    @property
    def is_leaf(self) -> bool:
        """True for rows that are not aggregates of other rows."""
        return self.sex != SEX_TOTAL and self.age_group != AGE_TOTAL


def _to_float(text: str) -> float:
    """Parse IHME's thousands-separated numbers such as ``"1,264.90"``."""
    return float(text.replace(",", ""))


def read_mortality(path: Path = paths.MORTALITY_CSV) -> List[MortalityRow]:
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != MORTALITY_COLUMNS:
            raise ValueError(f"Unexpected mortality columns: {reader.fieldnames}")
        return [
            MortalityRow(
                country_code=row["Country Code"],
                country_name=row["Country Name"],
                year=int(row["Year"]),
                age_group=row["Age Group"],
                sex=row["Sex"],
                deaths=_to_float(row["Number of Deaths"]),
                rate_per_100k=_to_float(row["Death Rate Per 100,000"]),
            )
            for row in reader
        ]


# --------------------------------------------------------------------------- #
# US state health spending (XLSX data tables e9a-e9e)
# --------------------------------------------------------------------------- #

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

# "$40.2 B ($39.4 B - $40.9 B)", "$8170 ($8020 - $8320)", "27% (27% - 28%)",
# "-1.75% (-18.26% - 10.39%)"
_ESTIMATE = re.compile(
    r"^\s*(?P<point>-?\$?-?[\d.]+)\s*(?P<unit>[BM%]?)\s*"
    r"\(\s*(?P<lower>-?\$?-?[\d.]+)\s*[BM%]?\s*-\s*(?P<upper>-?\$?-?[\d.]+)\s*[BM%]?\s*\)\s*$"
)


@dataclass(frozen=True)
class Estimate:
    """A point estimate with its 95% uncertainty interval, as published."""

    point: float
    lower: float
    upper: float
    unit: str  # "B" (billions USD), "%" or "" (USD)

    @property
    def interval_contains_point(self) -> bool:
        return self.lower <= self.point <= self.upper


def parse_estimate(text: str) -> Estimate:
    match = _ESTIMATE.match(text)
    if not match:
        raise ValueError(f"Not an IHME estimate string: {text!r}")

    def num(group: str) -> float:
        return float(match.group(group).replace("$", ""))

    return Estimate(num("point"), num("lower"), num("upper"), match.group("unit"))


def read_xlsx_sheets(path: Path = paths.SPENDING_XLSX) -> Dict[str, List[List[Optional[str]]]]:
    """Return ``{sheet name: rows}`` with every cell rendered as text."""
    with zipfile.ZipFile(path) as archive:
        shared: List[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(_NS + "t")) for si in root.findall(_NS + "si")]

        rels = {rel.get("Id"): rel.get("Target") for rel in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets: Dict[str, List[List[Optional[str]]]] = {}
        for sheet in workbook.find(_NS + "sheets"):
            target = rels[sheet.get(_REL_NS + "id")].lstrip("/")
            target = target if target.startswith("xl/") else "xl/" + target
            data = ET.fromstring(archive.read(target)).find(_NS + "sheetData")
            rows: List[List[Optional[str]]] = []
            for row in data:
                cells: List[Optional[str]] = []
                for cell in row:
                    value = cell.find(_NS + "v")
                    if value is None:
                        inline = cell.find(_NS + "is")
                        text = "".join(t.text or "" for t in inline.iter(_NS + "t")) if inline is not None else None
                    elif cell.get("t") == "s":
                        text = shared[int(value.text)]
                    else:
                        text = value.text
                    cells.append(text)
                rows.append(cells)
            sheets[sheet.get("name")] = rows
    return sheets


@dataclass(frozen=True)
class SpendingTable:
    name: str
    header: List[str]
    records: List[Dict[str, object]]  # numeric columns parsed to Estimate
    footnote: Optional[str]


def read_spending(path: Path = paths.SPENDING_XLSX) -> Dict[str, SpendingTable]:
    """Parse tables e9a-e9e into records keyed by their column headers."""
    tables: Dict[str, SpendingTable] = {}
    for name, rows in read_xlsx_sheets(path).items():
        header = [h or "" for h in rows[0]]
        records: List[Dict[str, object]] = []
        footnote: Optional[str] = None
        for row in rows[1:]:
            if len(row) == 1 and row[0] and row[0].startswith("*"):
                footnote = row[0]
                continue
            record: Dict[str, object] = {}
            for column, value in zip(header, row):
                if column == "State":
                    record[column] = value
                elif column == "Year":
                    record[column] = int(value)
                else:
                    record[column] = parse_estimate(value)
            records.append(record)
        tables[name] = SpendingTable(name, header, records, footnote)
    return tables


def coverage(records: List[Dict[str, object]]) -> Tuple[int, List[int]]:
    """Number of distinct states and the sorted list of years in a table."""
    states = {r["State"] for r in records}
    years = sorted({r["Year"] for r in records if "Year" in r})
    return len(states), years
