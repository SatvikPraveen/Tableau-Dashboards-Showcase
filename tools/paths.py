"""Canonical locations of the artifacts audited by this package."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MORTALITY_DIR = REPO_ROOT / "01_Global_Mortality_Analysis"
SPENDING_DIR = REPO_ROOT / "02_Cost_of_Care_US_State_Healthcare_Spending_Analysis"

MORTALITY_CSV = MORTALITY_DIR / "Dataset" / "IHME_GBD_2010_MORTALITY_AGE_SPECIFIC_BY_COUNTRY_1970_2010.csv"
SPENDING_XLSX = SPENDING_DIR / "Dataset" / "IHME_USA_STATE_HEALTH_SPENDING_2003_2019_DATA_TABLES_Y2022M08D23.XLSX"

CHECKSUMS = REPO_ROOT / "data" / "CHECKSUMS.sha256"
DOCS_DIR = REPO_ROOT / "docs"
