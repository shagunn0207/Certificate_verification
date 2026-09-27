import unittest
from src.utils import (
    normalize_date_to_ddmmyyyy,
    parse_date_flexible,
    generate_date_range,
    extract_month_year,
    extract_month_name_year
)

class TestDateUtilities(unittest.TestCase):
    def test_various_date_formats(self):
        # 10/09/26 -> 10/09/2026
        self.assertEqual(normalize_date_to_ddmmyyyy("10/09/26"), "10/09/2026")
        # September 10, 2026 -> 10/09/2026
        self.assertEqual(normalize_date_to_ddmmyyyy("September 10, 2026"), "10/09/2026")
        # 10 September 2026 -> 10/09/2026
        self.assertEqual(normalize_date_to_ddmmyyyy("10 September 2026"), "10/09/2026")
        # 10th Sep 2026 -> 10/09/2026
        self.assertEqual(normalize_date_to_ddmmyyyy("10th Sep 2026"), "10/09/2026")
        # 2026-09-10 -> 10/09/2026
        self.assertEqual(normalize_date_to_ddmmyyyy("2026-09-10"), "10/09/2026")

    def test_multi_day_date_range(self):
        dates, count = generate_date_range("10/09/2026", "12/09/2026")
        self.assertEqual(count, 3)
        self.assertEqual(dates, ["10/09/2026", "11/09/2026", "12/09/2026"])

    def test_single_day_date_range(self):
        dates, count = generate_date_range("10/09/2026", "10/09/2026")
        self.assertEqual(count, 1)
        self.assertEqual(dates, ["10/09/2026"])

    def test_invalid_date_range(self):
        # End date earlier than start date
        with self.assertRaises(ValueError):
            generate_date_range("15/09/2026", "10/09/2026")

    def test_month_extraction(self):
        self.assertEqual(extract_month_year("10/09/2026"), "09/2026")
        self.assertEqual(extract_month_name_year("10/09/2026"), "September 2026")

if __name__ == "__main__":
    unittest.main()
