# Changelog

All notable changes to this repository are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-04

This release makes the repository reproducible and documents the analytical
limitations of the published dashboards. The Tableau workbooks, screenshots and
raw data are unchanged byte-for-byte.

### Added

- `tools/`: standard-library Python tooling that reads the raw IHME files,
  verifies their integrity, inventories the workbooks and audits the dashboards.
- `docs/analytical_audit.md`: a generated report that reproduces every headline
  number in the screenshots from the raw data. It lists 13 findings: 8 confirmed
  issues, 2 caveats and 3 checks that came back clean.
- `docs/workbook_inventory.md`: a generated listing of data connections,
  worksheets, dashboards and calculated-field formulas.
- `data/CHECKSUMS.sha256`: SHA-256 hashes pinning the exact data and workbooks.
- Regression tests that pin the published values, with negative controls.
- `DATA_LICENSE.md`, `CITATION.cff`, `CONTRIBUTING.md`, issue and pull request
  templates, `Makefile`, `pyproject.toml`, `.gitattributes` and `.editorconfig`.
- A GitHub Actions workflow in `.github/workflows/ci.yml` that verifies the
  data, runs the tests, checks generated docs are current and lints the code.

### Changed

- Rewrote all READMEs, adding research questions, provenance, data
  dictionaries, methods and known limitations.
- Corrected the documented coverage of the spending data to 2015-2019.
- Corrected references to `.twbx` files and data file names that do not exist.
- Described `% Change in Deaths` as decade-on-decade, not year-over-year.
- Set the copyright holder to Satvik Praveen.

## [1.0.0] - 2024-11-30

### Added

- Global Mortality Analysis dashboards (GBD 2010, 1970-2010).
- Cost of Care US State Healthcare Spending dashboards (IHME, 2015-2019).
