import os
import unittest
from src.pipeline import VerificationPipeline
from src.data_loader import DataLoader

class TestCompletePipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline = VerificationPipeline()
        cls.data_loader = cls.pipeline.data_loader

    def run_case(self, test_num, name, cert_dict, expected_result, expected_reason_kw=""):
        res = self.pipeline._execute_core_pipeline(cert_dict, save_to_history=False)
        actual_result = res["final_result"]
        actual_reason = res["final_reason"]
        passed = (actual_result == expected_result)
        if expected_reason_kw:
            passed = passed and (expected_reason_kw.lower() in actual_reason.lower())

        status_str = "PASS" if passed else "FAIL"
        print(f"\n[{status_str}] TEST {test_num}: {name}")
        print(f"  Input: {cert_dict.get('FACULTY ID', '')} | {cert_dict.get('START DATE', '')} to {cert_dict.get('END DATE', '')} | {cert_dict.get('PROGRAM INSTITUTION', '')}")
        print(f"  Expected: {expected_result}")
        print(f"  Actual:   {actual_result} ({actual_reason})")
        
        self.assertEqual(actual_result, expected_result, f"Test {test_num} failed: Expected {expected_result}, got {actual_result}")
        if expected_reason_kw:
            self.assertIn(expected_reason_kw.lower(), actual_reason.lower())
        return passed

    def test_all_18_cases(self):
        print("\n============================================================")
        print("EXECUTING MANDATORY 18 TEST CASES (SECTION 28)")
        print("============================================================")

        # TEST 1: Internal FDP
        self.run_case(
            1, "Internal FDP",
            {
                "FACULTY ID": "F012", "FACULTY NAME": "Dr. Sushma B", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "Ramaiah Institute of Technology", "PROGRAM TYPE": "INTERNAL",
                "START DATE": "07/07/2025", "END DATE": "11/07/2025", "NUMBER OF DAYS": "5"
            },
            "VALID"
        )

        # TEST 2: External FDP + OOD
        self.run_case(
            2, "External FDP + OOD",
            {
                "FACULTY ID": "F011", "FACULTY NAME": "Dr. Ganeshayya Shidaganti", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "BMS College of Engineering Bangalore", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "09/02/2026", "END DATE": "13/02/2026", "NUMBER OF DAYS": "5"
            },
            "VALID"
        )

        # TEST 3: External FDP + Casual Leave
        self.run_case(
            3, "External FDP + Casual Leave",
            {
                "FACULTY ID": "F015", "FACULTY NAME": "Dr. Mallegowda M.", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "EXTERNAL", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "28/07/2025", "END DATE": "01/08/2025", "NUMBER OF DAYS": "5"
            },
            "INVALID", "Casual Leave"
        )

        # TEST 4: External FDP + Emergency Leave
        self.run_case(
            4, "External FDP + Emergency Leave",
            {
                "FACULTY ID": "F012", "FACULTY NAME": "Dr. Sushma B", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "National Institute of Technology", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "05/11/2025", "END DATE": "09/11/2025", "NUMBER OF DAYS": "5"
            },
            "INVALID", "Emergency Leave"
        )

        # TEST 5: Holiday conflict / weekend support
        # CERT-030 has institutional holiday on 19/11/2025 and weekend on 22/11/2025
        self.run_case(
            5, "Holiday alignment / verification",
            {
                "FACULTY ID": "F015", "FACULTY NAME": "Dr. Mallegowda M.", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "RVITM", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "17/11/2025", "END DATE": "22/11/2025", "NUMBER OF DAYS": "6"
            },
            "VALID"
        )

        # TEST 6: Unpaid Leave conflict
        self.run_case(
            6, "Unpaid Leave conflict",
            {
                "FACULTY ID": "F021", "FACULTY NAME": "Dr. Akshata S. Bhayyar", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "SwipeGen", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "10/03/2026", "END DATE": "14/03/2026", "NUMBER OF DAYS": "5"
            },
            "INVALID", "UNPAID LEAVE"
        )

        # TEST 7: Multi-day FDP
        self.run_case(
            7, "Multi-day FDP (all verified)",
            {
                "FACULTY ID": "F027", "FACULTY NAME": "Priya K", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "JAIN", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "29/06/2026", "END DATE": "03/07/2026", "NUMBER OF DAYS": "5"
            },
            "VALID"
        )

        # TEST 8: One conflicting day in a multi-day FDP (CRITICAL TEST Section 29)
        self.data_loader.attendance_lookup[("F001", "10/09/2026")] = "OOD"
        self.data_loader.attendance_lookup[("F001", "11/09/2026")] = "OOD"
        self.data_loader.attendance_lookup[("F001", "12/09/2026")] = "Casual Leave"
        self.data_loader.faculty_months_available["F001"].add("09/2026")

        self.run_case(
            8, "One conflicting day in a multi-day FDP",
            {
                "FACULTY ID": "F001", "FACULTY NAME": "Dr. S. Seema", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "EXTERNAL", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "10/09/2026", "END DATE": "12/09/2026", "NUMBER OF DAYS": "3"
            },
            "INVALID", "Casual Leave"
        )

        # TEST 9: Wrong faculty
        self.run_case(
            9, "Wrong faculty",
            {
                "FACULTY ID": "F999", "FACULTY NAME": "NonExistent Faculty", "FACULTY_MATCHED": False,
                "PROGRAM INSTITUTION": "MSRIT", "PROGRAM TYPE": "INTERNAL",
                "START DATE": "07/07/2025", "END DATE": "11/07/2025", "NUMBER OF DAYS": "5"
            },
            "NEEDS REVIEW", "Faculty could not be reliably matched"
        )

        # TEST 10: Missing FDP date
        self.run_case(
            10, "Missing FDP date",
            {
                "FACULTY ID": "F012", "FACULTY NAME": "Dr. Sushma B", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "MSRIT", "PROGRAM TYPE": "INTERNAL",
                "START DATE": "", "END DATE": "", "NUMBER OF DAYS": "5"
            },
            "NEEDS REVIEW", "FDP start/end date could not be determined"
        )

        # TEST 11: Entire attendance month missing (CRITICAL TEST Section 30)
        self.run_case(
            11, "Entire attendance month missing",
            {
                "FACULTY ID": "F002", "FACULTY NAME": "Dr. Monica R. Mundada", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "EXTERNAL", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "10/09/2026", "END DATE": "12/09/2026", "NUMBER OF DAYS": "3"
            },
            "NEEDS REVIEW", "September 2026 are unavailable"
        )

        # TEST 12: One required attendance date missing (CRITICAL TEST Section 31)
        self.data_loader.attendance_lookup[("F005", "10/09/2026")] = "OOD"
        self.data_loader.attendance_lookup[("F005", "11/09/2026")] = "OOD"
        self.data_loader.faculty_months_available["F005"].add("09/2026")
        if ("F005", "12/09/2026") in self.data_loader.attendance_lookup:
            del self.data_loader.attendance_lookup[("F005", "12/09/2026")]

        self.run_case(
            12, "One required attendance date missing",
            {
                "FACULTY ID": "F005", "FACULTY NAME": "Nagabhushan A. M", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "EXTERNAL", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "10/09/2026", "END DATE": "12/09/2026", "NUMBER OF DAYS": "3"
            },
            "NEEDS REVIEW", "Attendance record for 12/09/2026 is unavailable"
        )

        # TEST 13: Poor quality certificate text (unparseable dates)
        self.run_case(
            13, "Poor-quality certificate text",
            {
                "FACULTY ID": "F012", "FACULTY NAME": "Dr. Sushma B", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "MSRIT", "PROGRAM TYPE": "INTERNAL",
                "START DATE": "??/??/????", "END DATE": "??/??/????", "NUMBER OF DAYS": "5"
            },
            "INVALID", "Invalid date format"
        )

        # TEST 14: Different date format (e.g. September 10, 2026)
        # Using F001 with pre-setup dates normalized
        self.data_loader.attendance_lookup[("F001", "12/09/2026")] = "OOD"
        self.run_case(
            14, "Different date format",
            {
                "FACULTY ID": "F001", "FACULTY NAME": "Dr. S. Seema", "FACULTY_MATCHED": True,
                "PROGRAM INSTITUTION": "EXTERNAL", "PROGRAM TYPE": "EXTERNAL",
                "START DATE": "September 10, 2026", "END DATE": "September 12, 2026", "NUMBER OF DAYS": "3"
            },
            "VALID"
        )

        # TEST 15: Existing certificate re-verification (CERT-001)
        existing_rows = self.data_loader.get_certificate_tracker_rows()
        c001 = next(r for r in existing_rows if r["CERTIFICATE ID"] == "CERT-001")
        res15 = self.pipeline.verify_existing_certificate(c001, save_to_history=False)
        self.assertEqual(res15["final_result"], "VALID")
        print("\n[PASS] TEST 15: Existing certificate re-verification (CERT-001 -> VALID)")

        # TEST 16: New certificate upload simulation
        test_pdf_content = b"%PDF-1.4 Mock certificate content Dr. Sushma B RIT 07/07/2025 to 11/07/2025"
        res16 = self.pipeline.verify_uploaded_certificate(
            file_bytes=test_pdf_content,
            filename="mock_cert_012.pdf",
            fallback_meta={
                "FACULTY ID": "F012", "FACULTY NAME": "Dr. Sushma B",
                "PROGRAM INSTITUTION": "Ramaiah Institute of Technology", "START DATE": "07/07/2025",
                "END DATE": "11/07/2025", "NUMBER OF DAYS": "5"
            },
            save_to_history=False
        )
        self.assertEqual(res16["final_result"], "VALID")
        print("\n[PASS] TEST 16: New certificate upload (VALID)")

        # TEST 17: Invalid file format
        with self.assertRaises(ValueError):
            self.pipeline.verify_uploaded_certificate(
                file_bytes=b"dummy exe",
                filename="certificate.exe"
            )
        print("\n[PASS] TEST 17: Invalid file format (.exe blocked with ValueError)")

        # TEST 18: Complete attendance data + all required dates present (CERT-033)
        c033 = next(r for r in existing_rows if r["CERTIFICATE ID"] == "CERT-033")
        res18 = self.pipeline.verify_existing_certificate(c033, save_to_history=False)
        self.assertEqual(res18["final_result"], "VALID")
        print("\n[PASS] TEST 18: Complete attendance data + all required dates present (CERT-033 -> VALID)")
        print("\n============================================================")
        print("ALL 18 MANDATORY TEST CASES PASSED WITH 100% ACCURACY!")
        print("============================================================")

if __name__ == "__main__":
    unittest.main()
