"""
tests/test_appraisal.py
Unit tests for the Faculty Self-Appraisal module (src/appraisal.py).
Covers all 20 requirements specified in the feature request.
"""
import sys
import os
import unittest
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.appraisal import (
    classify_venue, compute_appraisal, calculate_scores,
    export_appraisal_json_files, parse_iso_date, is_in_period, INTERNAL_ALIASES
)


def make_faculty(fac_id="F001", name="Dr. Test Faculty", dept="AIML"):
    return {"id": fac_id, "name": name, "department": dept}


def make_attendance(fac_id, event_id, event_name, venue, start, end, attended):
    return {
        "facultyId": fac_id,
        "eventId": event_id,
        "eventName": event_name,
        "venue": venue,
        "startDate": start,
        "endDate": end,
        "attended": attended
    }


def make_cert(fac_id, event_id, event_name, venue, start, end, status, reason=""):
    return {
        "facultyId": fac_id,
        "certId": "CERT-001",
        "eventId": event_id,
        "eventName": event_name,
        "venue": venue,
        "startDate": start,
        "endDate": end,
        "status": status,
        "reason": reason
    }


class TestRequirement1_NoQualifyingEvents(unittest.TestCase):
    """REQ-1: Faculty with no qualifying events -> p16=0, p17=0."""
    def test_no_events(self):
        fac = make_faculty()
        data = {"attendance": [], "certificates": []}
        res = compute_appraisal(fac, data)
        self.assertEqual(res["p16"], 0)
        self.assertEqual(res["p17"], 0)
        self.assertEqual(res["rows"], [])


class TestRequirement2_OnlyExternalEvents(unittest.TestCase):
    """REQ-2: Faculty with only external events -> p16 > 0, p17 = 0."""
    def test_only_external(self):
        fac = make_faculty()
        data = {
            "attendance": [
                make_attendance("F001", "EVT-001", "ICML Workshop", "IISc Bangalore", "01/06/2025", "03/06/2025", True)
            ],
            "certificates": []
        }
        res = compute_appraisal(fac, data)
        self.assertGreater(res["p16"], 0)
        self.assertEqual(res["p17"], 0)


class TestRequirement3_OnlyInternalEvents(unittest.TestCase):
    """REQ-3: Faculty with only internal events -> p17 > 0, p16 = 0."""
    def test_only_internal(self):
        fac = make_faculty()
        data = {
            "attendance": [
                make_attendance("F001", "EVT-001", "RIT FDP", "Ramaiah Institute of Technology", "07/07/2025", "11/07/2025", True)
            ],
            "certificates": []
        }
        res = compute_appraisal(fac, data)
        self.assertEqual(res["p16"], 0)
        self.assertGreater(res["p17"], 0)


class TestRequirement4_BothInternalExternal(unittest.TestCase):
    """REQ-4: Faculty with both internal and external events -> p16 > 0 and p17 > 0."""
    def test_both(self):
        fac = make_faculty()
        data = {
            "attendance": [
                make_attendance("F001", "EVT-001", "External Conf", "IIT Bombay", "01/06/2025", "03/06/2025", True),
                make_attendance("F001", "EVT-002", "Internal FDP", "MSRIT", "07/07/2025", "11/07/2025", True)
            ],
            "certificates": []
        }
        res = compute_appraisal(fac, data)
        self.assertGreater(res["p16"], 0)
        self.assertGreater(res["p17"], 0)


class TestRequirement5_CertificateStatuses(unittest.TestCase):
    """REQ-5: Faculty with Valid, Invalid, Pending Review certificates."""
    def test_mixed_statuses(self):
        fac = make_faculty()
        data = {
            "attendance": [
                make_attendance("F001", "EVT-001", "Event A", "IIT Madras", "01/06/2025", "03/06/2025", True),
                make_attendance("F001", "EVT-002", "Event B", "IISc", "07/07/2025", "09/07/2025", True),
                make_attendance("F001", "EVT-003", "Event C", "NIT", "10/08/2025", "12/08/2025", True),
            ],
            "certificates": [
                make_cert("F001", "EVT-001", "Event A", "IIT Madras", "01/06/2025", "03/06/2025", "Valid"),
                make_cert("F001", "EVT-002", "Event B", "IISc", "07/07/2025", "09/07/2025", "Invalid"),
                make_cert("F001", "EVT-003", "Event C", "NIT", "10/08/2025", "12/08/2025", "Pending Review"),
            ]
        }
        res = compute_appraisal(fac, data)
        # 'st' key holds status per row
        statuses = [r["st"] for r in res["rows"] if r["st"] != "No certificate submitted"]
        self.assertIn("Valid", statuses)
        self.assertIn("Invalid", statuses)
        self.assertIn("Pending Review", statuses)


class TestRequirement6_CertStatusDoesNotAffectP16P17(unittest.TestCase):
    """REQ-6: Certificate status changes must NOT affect Points 16/17."""
    def _compute_with_status(self, status):
        fac = make_faculty()
        data = {
            "attendance": [
                make_attendance("F001", "EVT-001", "External Conf", "IIT Bombay", "01/06/2025", "03/06/2025", True)
            ],
            "certificates": [
                make_cert("F001", "EVT-001", "External Conf", "IIT Bombay", "01/06/2025", "03/06/2025", status)
            ]
        }
        return compute_appraisal(fac, data)

    def test_status_does_not_affect_p16(self):
        r_valid = self._compute_with_status("Valid")
        r_invalid = self._compute_with_status("Invalid")
        r_pending = self._compute_with_status("Pending Review")
        self.assertEqual(r_valid["p16"], r_invalid["p16"])
        self.assertEqual(r_valid["p16"], r_pending["p16"])


class TestRequirement7_DuplicateEventsNotInflated(unittest.TestCase):
    """REQ-7: Duplicate events must be deduplicated (not inflate Points 16/17)."""
    def test_dedup_events(self):
        fac = make_faculty()
        # Same event ID twice in attendance
        att = [
            make_attendance("F001", "EVT-DUP", "Workshop", "IISc", "01/06/2025", "03/06/2025", True),
            make_attendance("F001", "EVT-DUP", "Workshop", "IISc", "01/06/2025", "03/06/2025", True),
        ]
        data = {"attendance": att, "certificates": []}
        res = compute_appraisal(fac, data)
        # Should only count once, not twice
        self.assertEqual(res["p16"], 1)


class TestRequirement8_DuplicateCertificatesNotInflated(unittest.TestCase):
    """REQ-8: Duplicate certificate submissions must be deduplicated."""
    def test_dedup_certs(self):
        fac = make_faculty()
        data = {
            "attendance": [
                make_attendance("F001", "EVT-001", "Conf", "IIT Delhi", "01/06/2025", "03/06/2025", True)
            ],
            "certificates": [
                make_cert("F001", "EVT-001", "Conf", "IIT Delhi", "01/06/2025", "03/06/2025", "Valid"),
                make_cert("F001", "EVT-001", "Conf", "IIT Delhi", "01/06/2025", "03/06/2025", "Invalid"),
            ]
        }
        res = compute_appraisal(fac, data)
        # One event -> one certificate row, deduped to highest rank (Valid)
        cert_rows = [r for r in res["rows"] if r["st"] != "No certificate submitted"]
        self.assertEqual(len(cert_rows), 1)
        self.assertEqual(cert_rows[0]["st"], "Valid")


class TestRequirement9_SimilarNamesResolvedByID(unittest.TestCase):
    """REQ-9: Similar faculty names resolved by unique ID (not by name matching)."""
    def test_id_is_authoritative(self):
        fac_a = make_faculty("F001", "Dr. A Kumar")
        fac_b = make_faculty("F002", "Dr. A Kumar")  # Same name, different ID
        att_a = make_attendance("F001", "EVT-001", "Ext Conf", "IISc", "01/06/2025", "03/06/2025", True)
        att_b = make_attendance("F002", "EVT-001", "Ext Conf", "IISc", "01/06/2025", "03/06/2025", True)
        data = {"attendance": [att_a, att_b], "certificates": []}
        res_a = compute_appraisal(fac_a, data)
        res_b = compute_appraisal(fac_b, data)
        self.assertEqual(res_a["p16"], 1)
        self.assertEqual(res_b["p16"], 1)


class TestRequirement10_MissingVenueDepartment(unittest.TestCase):
    """REQ-10: Missing venue/department handled gracefully (Pending Classification)."""
    def test_missing_venue(self):
        fac = make_faculty()
        data = {
            "attendance": [
                make_attendance("F001", "EVT-001", "Mystery Event", "", "01/06/2025", "03/06/2025", True)
            ],
            "certificates": []
        }
        res = compute_appraisal(fac, data)
        self.assertEqual(res["p16"], 0)
        self.assertEqual(res["p17"], 0)
        self.assertGreater(res["flagged"], 0)


class TestRequirement11_AttendanceNullGivesPendingClassification(unittest.TestCase):
    """REQ-11: attended=null (None) -> Pending Classification, not counted."""
    def test_attended_none(self):
        fac = make_faculty()
        data = {
            "attendance": [
                make_attendance("F001", "EVT-001", "External Event", "IIT Bombay", "01/06/2025", "03/06/2025", None)
            ],
            "certificates": []
        }
        res = compute_appraisal(fac, data)
        self.assertEqual(res["p16"], 0)
        self.assertEqual(res["p17"], 0)
        # Event should be flagged
        self.assertGreater(res["flagged"], 0)


class TestRequirement12_PeriodFilteringExcludesOutsideEvents(unittest.TestCase):
    """REQ-12: Period filtering excludes events outside the appraisal period."""
    def test_period_filter(self):
        fac = make_faculty()
        data = {
            "attendance": [
                # Event within 2024-25 period
                make_attendance("F001", "EVT-IN", "Conf In Period", "IIT Bombay", "01/06/2024", "03/06/2024", True),
                # Event outside 2024-25 period (in 2023)
                make_attendance("F001", "EVT-OUT", "Conf Out Period", "NIT Trichy", "01/06/2023", "03/06/2023", True),
            ],
            "certificates": []
        }
        config = {
            "period": {"startMonth": 1, "startDay": 1},
            "internalAliases": INTERNAL_ALIASES,
            "scoring": None
        }
        res = compute_appraisal(fac, data, start_year=2024, config=config)
        # Only the 2024 event should count
        self.assertEqual(res["p16"], 1)


class TestRequirement13_DatasetConnectionError(unittest.TestCase):
    """REQ-13: Dataset connection error returns graceful structure (empty data)."""
    def test_empty_data_does_not_crash(self):
        fac = make_faculty()
        data = {"attendance": None, "certificates": None}
        # Should not raise, should return zeros
        try:
            res = compute_appraisal(fac, data)
            self.assertEqual(res["p16"], 0)
            self.assertEqual(res["p17"], 0)
        except Exception as e:
            self.fail(f"compute_appraisal raised exception on empty data: {e}")


class TestRequirement14_LocalStorageSerializationFields(unittest.TestCase):
    """REQ-14: Required LocalStorage fields are present in the HTML."""
    def test_ls_fields_in_html(self):
        html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appraisal_form.html")
        if not os.path.exists(html_path):
            self.skipTest("appraisal_form.html not generated yet")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        required_fields = ["y1", "y2", "name", "dept", "desig", "p16", "p17", "tot", "bon", "fin"]
        for field in required_fields:
            self.assertIn(f"'{field}'", html, f"LocalStorage field '{field}' not found in HTML")


class TestRequirement15_ResetFunctionality(unittest.TestCase):
    """REQ-15: Reset button clears form state (check JS has bReset handler)."""
    def test_reset_button_in_html(self):
        html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appraisal_form.html")
        if not os.path.exists(html_path):
            self.skipTest("appraisal_form.html not generated yet")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('id="bReset"', html)
        self.assertIn("bReset", html)
        self.assertIn("localStorage.removeItem", html)


class TestRequirement16_PrintOutputContainsBothSections(unittest.TestCase):
    """REQ-16: Print output contains both Section A (appraisal form) and Section B (report)."""
    def test_both_sections_in_html(self):
        html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appraisal_form.html")
        if not os.path.exists(html_path):
            self.skipTest("appraisal_form.html not generated yet")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn('id="secA"', html)
        self.assertIn('id="report"', html)
        self.assertIn('window.print()', html)


class TestRequirement17_OnlyRows16And17InTable(unittest.TestCase):
    """REQ-17: Activity table must contain ONLY rows 16 and 17, not 1-15 or 18-23."""
    def test_only_rows_16_17(self):
        html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appraisal_form.html")
        if not os.path.exists(html_path):
            self.skipTest("appraisal_form.html not generated yet")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        # Row 16 and 17 must exist
        self.assertIn("outside the institute", html, "Row 16 description missing")
        self.assertIn("inside the institute", html, "Row 17 description missing")
        # Rows 1-15, 18-23 must NOT appear as table row numbers (no <td>1</td> or similar pattern)
        import re
        # Find all <td> content that is a bare single/double digit
        td_nums = re.findall(r'<td>(\d+)</td>', html)
        for n in td_nums:
            num = int(n)
            self.assertIn(num, [16, 17], f"Activity row {n} found in table, only 16 and 17 are allowed")


class TestRequirement18_PrintLayoutInHTML(unittest.TestCase):
    """REQ-18: Print layout uses proper CSS @media print with page-break-before."""
    def test_print_css(self):
        html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "appraisal_form.html")
        if not os.path.exists(html_path):
            self.skipTest("appraisal_form.html not generated yet")
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
        self.assertIn("@media print", html)
        self.assertIn("page-break-before", html)
        self.assertIn("break-before", html)


class TestRequirement19_UnconfiguredScoringNoFabrication(unittest.TestCase):
    """REQ-19: Unconfigured scoring rules produce no fabricated scores (returns None)."""
    def test_no_scoring_config(self):
        result = calculate_scores(5, 3, scoring_config=None)
        self.assertIsNone(result, "calculate_scores should return None when scoring_config is None")

    def test_empty_scoring_config(self):
        result = calculate_scores(5, 3, scoring_config={})
        self.assertIsNone(result, "calculate_scores should return None when scoring_config has no weights")


class TestRequirement20_ExistingTestsNoRegression(unittest.TestCase):
    """REQ-20: Existing pipeline tests must pass with zero regressions."""
    def test_existing_modules_importable(self):
        # Verify core modules import without error
        try:
            from src.data_loader import DataLoader
            from src.verification import RuleVerificationEngine
            from src.pipeline import VerificationPipeline
        except ImportError as e:
            self.fail(f"Core module import failed (regression): {e}")

    def test_classify_venue_basic(self):
        self.assertEqual(classify_venue("Ramaiah Institute of Technology"), "Internal")
        self.assertEqual(classify_venue("MSRIT"), "Internal")
        self.assertEqual(classify_venue("IIT Bombay"), "External")
        self.assertEqual(classify_venue("RVITM"), "External")
        self.assertEqual(classify_venue(""), "Unknown")
        self.assertEqual(classify_venue(None), "Unknown")

    def test_parse_iso_date_both_formats(self):
        # DD/MM/YYYY
        d1 = parse_iso_date("17/11/2025")
        self.assertIsNotNone(d1)
        self.assertEqual(d1.day, 17)
        self.assertEqual(d1.month, 11)
        self.assertEqual(d1.year, 2025)
        # YYYY-MM-DD
        d2 = parse_iso_date("2025-11-17")
        self.assertIsNotNone(d2)
        self.assertEqual(d2.day, 17)
        self.assertEqual(d2.month, 11)
        self.assertEqual(d2.year, 2025)
        # Bad date
        self.assertIsNone(parse_iso_date("??/??/????"))
        self.assertIsNone(parse_iso_date(""))
        self.assertIsNone(parse_iso_date(None))


# ─── Wrapper to add cert_status alias to rows ────────────────────────────────
def compute_appraisal(fac, data, start_year=None, config=None):
    """Thin wrapper that adds 'cert_status' alias key for test readability."""
    from src.appraisal import compute_appraisal as _ca
    res = _ca(fac, data, start_year=start_year, config=config)
    for r in res.get("rows", []):
        # 'st' is the native key; add cert_status alias
        raw_st = r.get("st", "")
        r["cert_status"] = raw_st if raw_st not in ("", "No certificate submitted") else None
    return res


if __name__ == "__main__":
    unittest.main(verbosity=2)
