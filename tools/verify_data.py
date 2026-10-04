"""Verify the integrity and internal consistency of the source datasets.

Run from the repository root::

    python -m tools.verify_data
    python -m tools.verify_data --write-checksums   # after an intentional change

Exit status is non-zero if any check fails. The checks are deliberately
strict about structure (columns, coverage) and tolerant only where IHME's
published rounding makes exact equality impossible; each tolerance is stated
next to the check that uses it.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable, List, Tuple

from . import ihme, paths

CheckResult = Tuple[str, bool, str]

# Published counts are rounded to whole deaths, so a sex total can differ from
# Male + Female by at most 1, and an all-ages total (20 rounded components)
# by at most 10.
SEX_SUM_TOLERANCE = 1.0
AGE_SUM_TOLERANCE = 10.0

EXPECTED_MORTALITY = {
    "countries": 187,
    "years": [1970, 1980, 1990, 2000, 2010],
    "age_groups": 21,  # 20 age bands + "All ages"
    "sexes": ["Both", "Female", "Male"],
}
EXPECTED_SPENDING = {
    "Table e9a": (51, [2015, 2016, 2017, 2018, 2019]),
    "Table e9b": (51, [2015, 2016, 2017, 2018, 2019]),
    "Table e9c": (51, [2015, 2016, 2017, 2018, 2019]),
    "Table e9d": (51, []),
    "Table e9e": (51, []),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_checksums() -> List[CheckResult]:
    results: List[CheckResult] = []
    for line in paths.CHECKSUMS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        expected, relative = line.split(maxsplit=1)
        target = paths.REPO_ROOT / relative.lstrip("*")
        if not target.exists():
            results.append((f"sha256 {relative}", False, "file missing"))
            continue
        actual = sha256(target)
        results.append((f"sha256 {relative}", actual == expected, actual[:12]))
    return results


# Files pinned by the manifest, relative to the repository root.
TRACKED_SUFFIXES = {".csv", ".xlsx", ".twb"}


def write_checksums() -> int:
    """Rewrite the manifest, keeping its comment header."""
    header = [line for line in paths.CHECKSUMS.read_text(encoding="utf-8").splitlines() if line.startswith("#")]
    tracked = sorted(
        path.relative_to(paths.REPO_ROOT).as_posix()
        for directory in (paths.MORTALITY_DIR, paths.SPENDING_DIR)
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in TRACKED_SUFFIXES
    )
    lines = header + [f"{sha256(paths.REPO_ROOT / relative)}  {relative}" for relative in tracked]
    paths.CHECKSUMS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(tracked)} entries to {paths.CHECKSUMS.relative_to(paths.REPO_ROOT)}.")
    return 0


def check_mortality() -> List[CheckResult]:
    rows = ihme.read_mortality()
    exp = EXPECTED_MORTALITY
    countries = {r.country_code for r in rows}
    years = sorted({r.year for r in rows})
    ages = {r.age_group for r in rows}
    sexes = sorted({r.sex for r in rows})
    expected_rows = exp["countries"] * len(exp["years"]) * exp["age_groups"] * len(exp["sexes"])
    keys = {(r.country_code, r.year, r.age_group, r.sex) for r in rows}

    index = {(r.country_code, r.year, r.age_group, r.sex): r.deaths for r in rows}
    sex_gap = max(
        abs(index[(c, y, a, "Both")] - index[(c, y, a, "Male")] - index[(c, y, a, "Female")]) for c, y, a, _ in keys
    )
    age_sums = defaultdict(float)
    for r in rows:
        if r.age_group != ihme.AGE_TOTAL:
            age_sums[(r.country_code, r.year, r.sex)] += r.deaths
    age_gap = max(abs(index[(c, y, ihme.AGE_TOTAL, s)] - total) for (c, y, s), total in age_sums.items())

    return [
        ("mortality: country count", len(countries) == exp["countries"], str(len(countries))),
        ("mortality: years", years == exp["years"], str(years)),
        ("mortality: age groups", len(ages) == exp["age_groups"], str(len(ages))),
        ("mortality: sexes", sexes == exp["sexes"], str(sexes)),
        ("mortality: complete grid, no duplicates", len(rows) == len(keys) == expected_rows, f"{len(rows)} rows"),
        ("mortality: no negative deaths or rates", all(r.deaths >= 0 and r.rate_per_100k >= 0 for r in rows), ""),
        (
            f"mortality: Both = Male + Female (|gap| <= {SEX_SUM_TOLERANCE:g})",
            sex_gap <= SEX_SUM_TOLERANCE,
            f"max gap {sex_gap:g}",
        ),
        (
            f"mortality: All ages = sum of age bands (|gap| <= {AGE_SUM_TOLERANCE:g})",
            age_gap <= AGE_SUM_TOLERANCE,
            f"max gap {age_gap:g}",
        ),
    ]


def check_spending() -> List[CheckResult]:
    tables = ihme.read_spending()
    results: List[CheckResult] = [
        ("spending: sheet names", sorted(tables) == sorted(EXPECTED_SPENDING), str(sorted(tables)))
    ]
    for name, (n_states, years) in EXPECTED_SPENDING.items():
        table = tables[name]
        states, found_years = ihme.coverage(table.records)
        results.append(
            (
                f"spending: {name} coverage",
                (states, found_years) == (n_states, years),
                f"{states} states, years {found_years}",
            )
        )
        estimates = [v for rec in table.records for v in rec.values() if isinstance(v, ihme.Estimate)]
        results.append(
            (
                f"spending: {name} intervals contain point estimate",
                all(e.interval_contains_point for e in estimates),
                f"{len(estimates)} estimates",
            )
        )
    for name in ("Table e9b", "Table e9c"):
        totals = [sum(v.point for k, v in rec.items() if isinstance(v, ihme.Estimate)) for rec in tables[name].records]
        # Shares are published as whole percents, so rows may sum to 100 +/- 2.
        results.append(
            (
                f"spending: {name} shares sum to 100% (+/- 2 pp)",
                all(98 <= t <= 102 for t in totals),
                f"range {min(totals):g}-{max(totals):g}",
            )
        )
    return results


def run(checks: List[Callable[[], List[CheckResult]]]) -> int:
    failures = 0
    for check in checks:
        for label, ok, detail in check():
            failures += not ok
            print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail else ""))
    print(f"\n{'All checks passed.' if not failures else f'{failures} check(s) failed.'}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write-checksums", action="store_true", help="regenerate data/CHECKSUMS.sha256")
    if parser.parse_args().write_checksums:
        return write_checksums()
    return run([check_checksums, check_mortality, check_spending])


if __name__ == "__main__":
    sys.exit(main())
