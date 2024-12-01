# Tableau-Dashboards-Showcase

## Overview

This repository contains a collection of Tableau dashboards created to analyze various datasets and demonstrate Tableau's data visualization and analytical capabilities. These dashboards showcase different techniques like time-series analysis, heatmaps, scatter plots, KPIs, and interactive filters to provide actionable insights.

---

## Repository Structure

```bash
Tableau-Dashboards-Showcase/
├── 01_ Global_Mortality_Analysis/
│   ├── Dataset/
│   │   └── IHME_GBD_2010_MORTALITY_AGE_SPECIFIC_BY_COUNTRY_1970_2010.csv
│   ├── Images/
│   │   ├── Dashboard1_Time_Series_Number_of_Deaths.png
│   │   ├── Dashboard2_Global_Mortality_Rate.png
│   ├── Global-Mortality-Rate-Dashboard.twb
│   ├── Time-Series-Dashboard.twb
│   └── README.md
├── 02_Cost_of_Care_US_State_Healthcare_Spending_Analysis/
│   ├── Dataset/
│   │   └── IHME_USA_STATE_HEALTH_SPENDING_2003_2019.xlsx
│   ├── Images/
│   │   ├──Dashboard1_Statewise_Spending_Insights_Per_Person_and_Standardized_Metrics.png
│   │   ├── Dashboard2_Healthcare_Fractional_Expenditure_by_State_and_Year.png
│   │   ├── Dashboard3_Statewise_Healthcare_Expenditure_Dental_Physician_and_Skilled_Nursing_Focus.png
│   ├── Statewise_Healthcare_Spending_Dashboards.twbx
│   └── README.md
├── LICENSE
├── .gitignore
└── README.md
```

---

## Projects

### 1. [Global Mortality Analysis](./01_Global_Mortality_Analysis/README.md)

Dashboards analyzing global mortality trends using age-specific and country-specific data.

#### Key Dashboards:

- **Global Mortality Overview**:
  - Interactive map with filters for continent, year, sex, and age group.
  - Displays global median death rates and total deaths by country.
  - Includes KPIs for quick insights.
- **Time Series Analysis**:
  - Line chart depicting trends in mortality over time.
  - Includes dynamic KPIs and year-over-year percentage change.
- **Dynamic KPIs**:
  - Tabular insights for year-over-year mortality analysis.

#### Dataset:

- **Source**: IHME Global Burden of Disease Study 2010.
- **File**: `IHME_GBD_2010_MORTALITY_AGE_SPECIFIC_BY_COUNTRY_1970_2010.csv`

---

### 2. [Cost of Care US State Healthcare Spending Analysis](./02_Cost_of_Care_US_State_Healthcare_Spending_Analysis/README.md)

Dashboards analyzing state-level healthcare expenditure trends across various categories in the United States.

#### Key Dashboards:

- **Statewise Spending and Standardized Spending Per Person**:

  - A map and treemap visualizing healthcare spending per person and standardized metrics across states.

- **Statewise Fractional Expenditure Breakdown**:

  - Heatmap and KPIs for analyzing fractional spending by state and year.

- **Category-Specific Expenditure Analysis**:
  - Bubble charts highlighting expenditure on dental care, skilled nursing, and other categories.

#### Dataset:

- **Source**: IHME USA State Health Spending Data
- **File**: `IHME_USA_STATE_HEALTH_SPENDING_2003_2019.xlsx`

---

## Skills Demonstrated

- **Interactive Visualizations**: Dynamic filters for real-time data exploration.
- **KPI Design**: Key Performance Indicators summarizing trends and insights.
- **Time-Series Analysis**: Year-over-year and trendline-based analysis.
- **Data Preparation**: Clean and preprocess raw data for visualization.
- **Heatmaps, Treemaps, and Bubble Charts**: Advanced techniques for showing density, hierarchy, and correlations.

---

## How to Explore

1. **Explore Locally**:
   - Download the `.twb` Tableau files and open them in Tableau Desktop.
2. **Online Access**:
   - Dashboards are also available on [Tableau Public](https://public.tableau.com/app/profile/satvik.praveen4534/vizzes).

---

## Contribution Guidelines

- Contributions are welcome!
- To add a new dashboard:
  1. Place your project in a dedicated folder.
  2. Include a dataset, `.twb` files, and a README.md for your project.
  3. Update the repository's main README.md to link to your project.

---

## License

This repository is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
