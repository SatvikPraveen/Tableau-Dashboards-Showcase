# Data Licensing and Attribution

The [MIT License](./LICENSE) in this repository covers **original work only**:
the Tableau workbooks (`*.twb`), dashboard images, documentation and the audit
tooling under `tools/`. It does **not** cover the third-party datasets.

## Third-party datasets

Both datasets were produced by the Institute for Health Metrics and Evaluation
(IHME), University of Washington, and are governed by the
[IHME Free-of-Charge Non-Commercial User Agreement](https://www.healthdata.org/data-tools-practices/data-practices/ihme-free-charge-non-commercial-user-agreement).

| Project | File | Dataset | Citation |
|---|---|---|---|
| 01 | `IHME_GBD_2010_MORTALITY_AGE_SPECIFIC_BY_COUNTRY_1970_2010.csv` | GBD 2010 Mortality Results 1970-2010 | Global Burden of Disease Collaborative Network. *Global Burden of Disease Study 2010 (GBD 2010) Mortality Results 1970-2010.* Seattle, United States of America: Institute for Health Metrics and Evaluation (IHME), 2012. |
| 02 | `IHME_USA_STATE_HEALTH_SPENDING_2003_2019_DATA_TABLES_Y2022M08D23.XLSX` | US Health Expenditure by State, Payer, and Type of Care, 2003-2019 | Institute for Health Metrics and Evaluation (IHME). *United States Health Expenditure by State, Payer, and Type of Care, 2003-2019.* Seattle, United States of America: IHME, 2022. |

Primary publication for the mortality estimates:

> Wang H, Dwyer-Lindgren L, Lofgren KT, Rajaratnam JK, Marcus JR,
> Levin-Rector A, Levitz CE, Lopez AD, Murray CJL. Age-specific and sex-specific
> mortality in 187 countries, 1970-2010: a systematic analysis for the Global
> Burden of Disease Study 2010. *The Lancet* 2012; 380(9859): 2071-2094.
> doi:[10.1016/S0140-6736(12)61719-X](https://doi.org/10.1016/S0140-6736(12)61719-X)

Source records on the IHME Global Health Data Exchange (GHDx):

- <https://ghdx.healthdata.org/record/ihme-data/gbd-2010-mortality-results-1970-2010>
- <https://ghdx.healthdata.org/record/ihme-data/united-states-health-spending-by-state-payer-type-service-2003-2019>

## Redistribution notice

The IHME agreement restricts non-commercial users from offering third parties
the ability to download IHME data sets from user-provided hosting, and asks
that users link to IHME's own download facilities instead. The raw files in
the `Dataset/` folders are kept here so that the workbooks open without
modification and so that every reported number can be re-derived. The
maintainer should confirm that this is compatible with the agreement, or
replace the raw files with download instructions plus the SHA-256 manifest in
[`data/CHECKSUMS.sha256`](./data/CHECKSUMS.sha256), which lets anyone verify a
fresh download against the exact bytes used here.

Use of either dataset for commercial purposes is not permitted under the IHME
agreement, regardless of the license on this repository.
