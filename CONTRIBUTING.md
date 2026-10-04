# Contributing

Thank you for your interest in improving this project. The repository holds
Tableau dashboards, the IHME data they are built on, and a small Python
toolkit that checks the two against each other. Contributions are reviewed
for analytical correctness first and presentation second.

## Development setup

The tooling uses only the Python standard library (Python 3.9 or newer).

```bash
git clone https://github.com/SatvikPraveen/Tableau-Dashboards-Showcase.git
cd Tableau-Dashboards-Showcase
make check            # verify data, run tests, check generated docs
pip install ruff      # optional, for `make lint`
```

Tableau Desktop 2024.3 or newer is needed only to edit the workbooks.

## Ground rules

1. **Do not modify raw data.** Files under `*/Dataset/` are byte-for-byte
   IHME releases pinned in `data/CHECKSUMS.sha256`. Derived data belongs in a
   separate, clearly named file produced by a script in `tools/`.
2. **Every number in the documentation must be reproducible.** If you add a
   claim to a README, add the code that computes it to `tools/audit.py` (or
   a new module) and a regression test under `tests/`.
3. **Regenerate generated files.** `docs/analytical_audit.md` and
   `docs/workbook_inventory.md` are written by `make docs`; CI fails if they
   are stale.
4. **Respect the data license.** IHME data may only be used for
   non-commercial purposes; see [DATA_LICENSE.md](./DATA_LICENSE.md).

## Changing a workbook

- Save as `.twb` (not `.twbx`) so changes stay reviewable as XML, and keep the
  data connection pointing at the file in the project's `Dataset/` folder.
- Re-export the dashboard screenshot into `Images/` at a similar resolution.
- Update the `PUBLISHED` values in `tools/audit.py` to the new screenshot and
  confirm `make check` passes. If a fix in [the audit](./docs/analytical_audit.md)
  is applied, update that finding's status in the code.
- Refresh the checksum manifest with `make checksums` and commit it together
  with the workbook.

## Adding a new project

Create a numbered folder (`03_<Topic>/`) with `Dataset/`, `Images/`, the
workbook(s) and a `README.md` following the structure of the existing
projects: question, data provenance and license, method (calculated fields),
dashboards, known limitations, and how to reproduce. Add the dataset to
`data/CHECKSUMS.sha256`, `DATA_LICENSE.md` and `CITATION.cff`.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) prefixes
(`feat`, `fix`, `docs`, `build`, `ci`, `chore`, `test`) with an imperative
summary of at most 72 characters.
