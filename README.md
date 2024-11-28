# Tableau-Dashboards-Showcase

## Overview
This repository contains a collection of Tableau dashboards created to analyze various datasets and demonstrate Tableau's data visualization and analytical capabilities. These dashboards showcase different techniques like time-series analysis, heatmaps, scatter plots, KPIs, and interactive filters to provide actionable insights.

---

## Repository Structure
```bash
Tableau-Dashboards-Showcase/
├── Global_Mortality_Analysis/
│   ├── Dataset/
│   │   └── IHME_GBD_2010_MORTALITY_AGE_SPECIFIC_BY_COUNTRY_1970_2010.csv
│   ├── Images/
│   │   ├── Dashboard1_Time_Series_Number_of_Deaths.png
│   │   ├── Dashboard2_Global_Mortality_Rate.png
│   ├── Global-Mortality-Rate-Dashboard.twb
│   ├── Time-Series-Dashboard.twb
│   └── README.md
├── Healthcare_Project/
│   ├── Dataset/
│   │   └── Sample_Healthcare_Data.csv
│   ├── Healthcare_Dashboard.twbx
│   └── README.md
├── LICENSE
├── .gitignore
└── README.md
```

---

## Projects

### 1. [Global Mortality Analysis](./Global_Mortality_Analysis/README.md)
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
- **Data Range**: 1970–2010

---

### 2. [Healthcare Project](./Healthcare_Project/README.md)
Dashboards visualizing healthcare data, focusing on patient admissions, hospital performance, and treatment outcomes.

#### Key Dashboards:
- **Admissions Trends**:
  - Time-series analysis of hospital admissions.
  - Comparison of admissions across departments.
- **Treatment Analysis**:
  - Visualization of treatment efficiency and outcomes.
  - KPIs summarizing patient recovery rates.

#### Dataset:
- **Source**: Sample Healthcare Data
- **File**: `Sample_Healthcare_Data.csv`

---

## Skills Demonstrated
- **Interactive Visualizations**: Dynamic filters for real-time data exploration.
- **KPI Design**: Key Performance Indicators summarizing trends and insights.
- **Time-Series Analysis**: Year-over-year and trendline-based analysis.
- **Data Preparation**: Clean and preprocess raw data for visualization.
- **Heatmaps and Scatter Plots**: Advanced techniques for showing density and correlations.

---

## How to Explore
1. **Explore Locally**:
   - Download the `.twbx` Tableau files and open them in Tableau Desktop.
2. **Online Access**:
   - Dashboards are also available on [Tableau Public](https://public.tableau.com/app/profile/satvik.praveen4534/vizzes).

---

## Contribution Guidelines
- Contributions are welcome! 
- To add a new dashboard:
  1. Place your project in a dedicated folder.
  2. Include a dataset, `.twbx` files, and a README.md for your project.
  3. Update the repository's main README.md to link to your project.

---

## License
This repository is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
