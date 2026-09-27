import unittest
from src.data_loader import DataLoader
from src.verification import RuleVerificationEngine

class TestVerificationEngine(unittest.TestCase):
    def setUp(self):
        self.data_loader = DataLoader()
        self.engine = RuleVerificationEngine(self.data_loader)

    def test_internal_fdp_valid(self):
        # CERT-001: Dr. Sushma B (F012), 07/07/2025 to 11/07/2025, Ramaiah Institute of Technology
        cert = {
            "FACULTY ID": "F012",
            "FACULTY NAME": "Dr. Sushma B",
            "FACULTY_MATCHED": True,
            "PROGRAM INSTITUTION": "Ramaiah Institute of Technology",
            "PROGRAM TYPE": "INTERNAL",
            "START DATE": "07/07/2025",
            "END DATE": "11/07/2025",
            "NUMBER OF DAYS": "5"
        }
        res = self.engine.verify(cert)
        self.assertEqual(res["RULE_RESULT"], "VALID")

    def test_external_fdp_ood_valid(self):
        # CERT-015: Dr. Ganeshayya Shidaganti (F011), 09/02/2026 to 13/02/2026, BMSCE, all OOD
        cert = {
            "FACULTY ID": "F011",
            "FACULTY NAME": "Dr. Ganeshayya Shidaganti",
            "FACULTY_MATCHED": True,
            "PROGRAM INSTITUTION": "BMS College of Engineering Bangalore",
            "PROGRAM TYPE": "EXTERNAL",
            "START DATE": "09/02/2026",
            "END DATE": "13/02/2026",
            "NUMBER OF DAYS": "5"
        }
        res = self.engine.verify(cert)
        self.assertEqual(res["RULE_RESULT"], "VALID")

    def test_external_casual_leave_conflict(self):
        # CERT-006: Dr. Mallegowda M. (F015), 28/07/2025 to 01/08/2025 (Casual Leave on 31/07/2025)
        cert = {
            "FACULTY ID": "F015",
            "FACULTY NAME": "Dr. Mallegowda M.",
            "FACULTY_MATCHED": True,
            "PROGRAM INSTITUTION": "EXTERNAL",
            "PROGRAM TYPE": "EXTERNAL",
            "START DATE": "28/07/2025",
            "END DATE": "01/08/2025",
            "NUMBER OF DAYS": "5"
        }
        res = self.engine.verify(cert)
        self.assertEqual(res["RULE_RESULT"], "INVALID")
        self.assertIn("casual leave", res["RULE_REASON"].lower())

    def test_external_emergency_leave_conflict(self):
        # CERT-017: Dr. Sushma B (F012), 05/11/2025 to 09/11/2025 (Emergency leave on 08/11/2025)
        cert = {
            "FACULTY ID": "F012",
            "FACULTY NAME": "Dr. Sushma B",
            "FACULTY_MATCHED": True,
            "PROGRAM INSTITUTION": "National Institute of Technology",
            "PROGRAM TYPE": "EXTERNAL",
            "START DATE": "05/11/2025",
            "END DATE": "09/11/2025",
            "NUMBER OF DAYS": "5"
        }
        res = self.engine.verify(cert)
        self.assertEqual(res["RULE_RESULT"], "INVALID")
        self.assertIn("emergency leave", res["RULE_REASON"].lower())

    def test_external_unpaid_leave_conflict(self):
        # CERT-025: Dr. Akshata S. Bhayyar (F021), 10/03/2026 to 14/03/2026 (Unpaid Leave on 12/03/2026)
        cert = {
            "FACULTY ID": "F021",
            "FACULTY NAME": "Dr. Akshata S. Bhayyar",
            "FACULTY_MATCHED": True,
            "PROGRAM INSTITUTION": "SwipeGen",
            "PROGRAM TYPE": "EXTERNAL",
            "START DATE": "10/03/2026",
            "END DATE": "14/03/2026",
            "NUMBER OF DAYS": "5"
        }
        res = self.engine.verify(cert)
        self.assertEqual(res["RULE_RESULT"], "INVALID")
        self.assertIn("UNPAID LEAVE", res["RULE_REASON"])

    def test_critical_multi_day_conflict(self):
        """
        CRITICAL TEST (Section 29):
        10/09/2026 - 12/09/2026
        10/09: OOD, 11/09: OOD, 12/09: Casual Leave
        Expected: INVALID
        """
        # Inject mock attendance into data loader for test
        self.data_loader.attendance_lookup[("F001", "10/09/2026")] = "OOD"
        self.data_loader.attendance_lookup[("F001", "11/09/2026")] = "OOD"
        self.data_loader.attendance_lookup[("F001", "12/09/2026")] = "Casual Leave"
        self.data_loader.faculty_months_available["F001"].add("09/2026")

        cert = {
            "FACULTY ID": "F001",
            "FACULTY NAME": "Dr. S. Seema",
            "FACULTY_MATCHED": True,
            "PROGRAM INSTITUTION": "EXTERNAL",
            "PROGRAM TYPE": "EXTERNAL",
            "START DATE": "10/09/2026",
            "END DATE": "12/09/2026",
            "NUMBER OF DAYS": "3"
        }
        res = self.engine.verify(cert)
        self.assertEqual(res["RULE_RESULT"], "INVALID")
        self.assertIn("Casual Leave", res["RULE_REASON"])

    def test_critical_missing_month(self):
        """
        CRITICAL TEST (Section 30):
        10/09/2026 - 12/09/2026
        September 2026 no attendance available
        Expected: NEEDS REVIEW
        Reason: Attendance records for September 2026 are unavailable.
        """
        cert = {
            "FACULTY ID": "F002",
            "FACULTY NAME": "Dr. Monica R. Mundada",
            "FACULTY_MATCHED": True,
            "PROGRAM INSTITUTION": "EXTERNAL",
            "PROGRAM TYPE": "EXTERNAL",
            "START DATE": "10/09/2026",
            "END DATE": "12/09/2026",
            "NUMBER OF DAYS": "3"
        }
        res = self.engine.verify(cert)
        self.assertEqual(res["RULE_RESULT"], "NEEDS REVIEW")
        self.assertIn("September 2026 are unavailable", res["RULE_REASON"])

    def test_critical_missing_date(self):
        """
        CRITICAL TEST (Section 31):
        10/09/2026 - 12/09/2026
        10/09: OOD, 11/09: OOD, 12/09: no record
        Expected: NEEDS REVIEW
        Reason: Attendance record for 12/09/2026 is unavailable.
        """
        self.data_loader.attendance_lookup[("F004", "10/09/2026")] = "OOD"
        self.data_loader.attendance_lookup[("F004", "11/09/2026")] = "OOD"
        self.data_loader.faculty_months_available["F004"].add("09/2026")
        if ("F004", "12/09/2026") in self.data_loader.attendance_lookup:
            del self.data_loader.attendance_lookup[("F004", "12/09/2026")]

        cert = {
            "FACULTY ID": "F004",
            "FACULTY NAME": "Dr. Geetha J.",
            "FACULTY_MATCHED": True,
            "PROGRAM INSTITUTION": "EXTERNAL",
            "PROGRAM TYPE": "EXTERNAL",
            "START DATE": "10/09/2026",
            "END DATE": "12/09/2026",
            "NUMBER OF DAYS": "3"
        }
        res = self.engine.verify(cert)
        self.assertEqual(res["RULE_RESULT"], "NEEDS REVIEW")
        self.assertIn("Attendance record for 12/09/2026 is unavailable", res["RULE_REASON"])

if __name__ == "__main__":
    unittest.main()
