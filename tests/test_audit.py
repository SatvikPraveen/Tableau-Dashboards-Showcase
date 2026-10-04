"""Regression tests: the audit must reproduce the numbers in the screenshots.

If one of these fails, either the data changed (see tools.verify_data) or the
diagnosis of how the workbook aggregates is wrong.
"""

import unittest

from tools import audit, ihme


class ReproducePublishedNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, stats = audit.build()
        cls.m = stats["mortality"]
        cls.s = stats["spending"]

    def test_time_series_totals_match_screenshot(self):
        for year, published in audit.PUBLISHED["mortality_total_by_year"].items():
            with self.subTest(year=year):
                self.assertEqual(round(self.m["naive_by_year"][year]), published)

    def test_naive_totals_are_four_times_correct_totals(self):
        for year, correct in self.m["correct_by_year"].items():
            with self.subTest(year=year):
                self.assertAlmostEqual(self.m["naive_by_year"][year] / correct, 4.0, places=4)

    def test_correct_2010_total(self):
        self.assertEqual(round(self.m["correct_by_year"][2010]), 52_641_951)

    def test_total_deaths_kpi_matches_screenshot(self):
        self.assertEqual(round(self.m["naive_total"]), audit.PUBLISHED["mortality_total_deaths_kpi"])

    def test_median_kpi_matches_screenshot(self):
        self.assertEqual(self.m["median_pooled"], audit.PUBLISHED["mortality_median_rate_kpi"])

    def test_decadal_percent_change_rounds_to_published(self):
        for year, published in audit.PUBLISHED["mortality_pct_change"].items():
            with self.subTest(year=year):
                self.assertEqual(round(self.m["pct_naive"][year]), published)
                self.assertAlmostEqual(self.m["pct_naive"][year], self.m["pct_correct"][year], places=2)

    def test_spending_legends_match_screenshot(self):
        self.assertEqual(self.s["legend_pp"], audit.PUBLISHED["spending_per_person_legend"])
        self.assertEqual(self.s["legend_std"], audit.PUBLISHED["spending_standardized_legend"])

    def test_spending_kpis_match_screenshot(self):
        self.assertEqual(self.s["kpi_pp_2015"], audit.PUBLISHED["spending_kpi_2015_per_person"])
        self.assertEqual(self.s["kpi_std_2015"], audit.PUBLISHED["spending_kpi_2015_standardized"])

    def test_dashboard2_kpis_match_raw_shares(self):
        published = {k: float(v) for k, v in audit.PUBLISHED["spending_dashboard2_alaska_2015"].items()}
        self.assertEqual(self.s["alaska_2015"], published)

    def test_growth_rate_fields_are_unused(self):
        self.assertEqual(len(self.s["unused_growth_fields"]), 10)

    def test_spending_coverage(self):
        self.assertEqual(self.s["years"], [2015, 2016, 2017, 2018, 2019])
        self.assertEqual(self.s["states"], 51)


class ContinentMappingTests(unittest.TestCase):
    def test_unmapped_countries(self):
        mapping, default = audit.continent_mapping()
        names = {r.country_name for r in ihme.read_mortality()}
        self.assertEqual(default, "Other")
        self.assertEqual(sorted(n for n in names if n not in mapping), ["Swaziland", "Taiwan"])

    def test_known_assignments(self):
        mapping, _ = audit.continent_mapping()
        self.assertEqual(mapping["United States"], "North America")
        self.assertEqual(mapping["Zimbabwe"], "Africa")


class GeneratedDocsAreCurrent(unittest.TestCase):
    def test_audit_report_is_up_to_date(self):
        self.assertEqual(audit.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
