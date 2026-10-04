import unittest

from tools import inspect_workbooks


class InspectWorkbooksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workbooks = {wb.path.name: wb for wb in inspect_workbooks.discover()}

    def test_all_workbooks_found(self):
        self.assertEqual(len(self.workbooks), 7)

    def test_combined_workbooks_contain_all_dashboards(self):
        self.assertEqual(len(self.workbooks["Global_Mortality_Analysis.twb"].dashboards), 2)
        self.assertEqual(len(self.workbooks["Statewise_Healthcare_Spending_Analysis.twb"].dashboards), 3)

    def test_absolute_paths_are_flagged(self):
        for name, wb in self.workbooks.items():
            with self.subTest(workbook=name):
                self.assertTrue(any(p.startswith("/Users/") for p in wb.absolute_paths))

    def test_inventory_is_up_to_date(self):
        self.assertEqual(inspect_workbooks.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
