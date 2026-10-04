import unittest

from tools import ihme


class ParseEstimateTests(unittest.TestCase):
    def test_billions(self):
        est = ihme.parse_estimate("$40.2 B ($39.4 B - $40.9 B)")
        self.assertEqual((est.point, est.lower, est.upper, est.unit), (40.2, 39.4, 40.9, "B"))

    def test_dollars_without_unit(self):
        est = ihme.parse_estimate("$8170 ($8020 - $8320)")
        self.assertEqual((est.point, est.lower, est.upper, est.unit), (8170, 8020, 8320, ""))

    def test_percent_with_negative_bounds(self):
        est = ihme.parse_estimate("-1.75% (-18.26% - 10.39%)")
        self.assertEqual((est.point, est.lower, est.upper, est.unit), (-1.75, -18.26, 10.39, "%"))

    def test_negative_upper_bound(self):
        est = ihme.parse_estimate("-3% (-5% - -1%)")
        self.assertEqual((est.lower, est.upper), (-5, -1))

    def test_rejects_malformed_text(self):
        for bad in ["", "27%", "$8170", "n/a", "27% (27%)"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                ihme.parse_estimate(bad)


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mortality = ihme.read_mortality()
        cls.spending = ihme.read_spending()

    def test_mortality_numbers_strip_thousands_separators(self):
        first = self.mortality[0]
        self.assertEqual(
            (first.country_code, first.year, first.age_group, first.sex), ("AFG", 1970, "0-6 days", "Male")
        )
        self.assertEqual(first.deaths, 19241)
        self.assertAlmostEqual(first.rate_per_100k, 318292.9)

    def test_one_canonical_total_per_country_year(self):
        totals = [r for r in self.mortality if r.is_canonical_total]
        self.assertEqual(len(totals), 187 * 5)

    def test_spending_footnotes_are_not_parsed_as_records(self):
        self.assertTrue(self.spending["Table e9d"].footnote.startswith("*"))
        self.assertEqual(len(self.spending["Table e9d"].records), 51)


if __name__ == "__main__":
    unittest.main()
