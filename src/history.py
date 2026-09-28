import os
import csv
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

HISTORY_HEADERS = [
    "Verification ID",
    "Timestamp",
    "Certificate ID",
    "Faculty ID",
    "Faculty Name",
    "FDP Name",
    "Institution",
    "Internal/External",
    "Start Date",
    "End Date",
    "Duration (Days)",
    "ML Prediction",
    "ML Confidence",
    "Rule Result",
    "Final Result",
    "Tracker Original Result",
    "Agreement",
    "Reason"
]

class VerificationHistoryManager:
    def __init__(self, results_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(base_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)

        self.results_file = results_path or os.path.join(self.results_dir, "verification_results.csv")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.results_file):
            with open(self.results_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(HISTORY_HEADERS)

    def record_verification(self, cert_data: Dict[str, Any], rule_output: Dict[str, Any], ml_output: Dict[str, Any], final_result: str, final_reason: str) -> Dict[str, Any]:
        """
        Appends a new verification event to verification_results.csv.
        Never modifies the original certificate_tracker.csv.
        """
        verif_id = f"VERIF-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        tracker_original = cert_data.get("TRACKER_ORIGINAL_RESULT", "").strip().upper()
        final_upper = final_result.strip().upper()
        if tracker_original:
            agreement = "YES" if final_upper == tracker_original else "NO (DISAGREE)"
        else:
            agreement = "N/A (no tracker ref)"

        row = {
            "Verification ID": verif_id,
            "Timestamp": ts,
            "Certificate ID": cert_data.get("CERTIFICATE ID", ""),
            "Faculty ID": cert_data.get("FACULTY ID", ""),
            "Faculty Name": cert_data.get("FACULTY NAME", ""),
            "FDP Name": cert_data.get("FDP / PROGRAM NAME", ""),
            "Institution": cert_data.get("PROGRAM INSTITUTION", ""),
            "Internal/External": cert_data.get("PROGRAM TYPE", ""),
            "Start Date": cert_data.get("START DATE", ""),
            "End Date": cert_data.get("END DATE", ""),
            "Duration (Days)": rule_output.get("ACTUAL_DAYS", cert_data.get("NUMBER OF DAYS", "")),
            "ML Prediction": ml_output.get("prediction", "N/A"),
            "ML Confidence": f"{ml_output.get('confidence', 0.0) * 100:.1f}%",
            "Rule Result": rule_output.get("RULE_RESULT", "N/A"),
            "Final Result": final_result,
            "Tracker Original Result": tracker_original,
            "Agreement": agreement,
            "Reason": final_reason
        }

        with open(self.results_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=HISTORY_HEADERS)
            writer.writerow(row)

        return row

    def get_all_records(self) -> List[Dict[str, str]]:
        """
        Retrieves all verification history records.
        """
        if not os.path.exists(self.results_file):
            return []
        with open(self.results_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def filter_records(
        self,
        faculty_query: Optional[str] = None,
        result_query: Optional[str] = None,
        type_query: Optional[str] = None,
        month_query: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Filters verification history records according to specified criteria.
        """
        records = self.get_all_records()
        filtered = []

        for r in records:
            if faculty_query and faculty_query != "All":
                if faculty_query.lower() not in r.get("Faculty ID", "").lower() and faculty_query.lower() not in r.get("Faculty Name", "").lower():
                    continue

            if result_query and result_query != "All":
                if r.get("Final Result", "").upper() != result_query.upper():
                    continue

            if type_query and type_query != "All":
                if r.get("Internal/External", "").upper() != type_query.upper():
                    continue

            if month_query and month_query != "All":
                # Check start date or timestamp month
                st_date = r.get("Start Date", "")
                if month_query not in st_date:
                    continue

            if search_query:
                sq = search_query.lower()
                combined = f"{r.get('Faculty Name', '')} {r.get('FDP Name', '')} {r.get('Institution', '')} {r.get('Reason', '')}".lower()
                if sq not in combined:
                    continue

            filtered.append(r)

        return filtered

    def get_statistics(self) -> Dict[str, Any]:
        """
        Calculates dynamic dashboard metrics directly from recorded verifications.
        Never hardcodes any statistics.
        """
        records = self.get_all_records()
        total = len(records)

        valid_count = 0
        invalid_count = 0
        needs_review_count = 0

        internal_count = 0
        external_count = 0

        ood_cases = 0
        casual_leave_conflicts = 0
        emergency_leave_conflicts = 0
        holiday_conflicts = 0
        unpaid_leave_conflicts = 0
        missing_attendance_cases = 0

        faculty_breakdown = {}
        month_breakdown = {}

        for r in records:
            res = r.get("Final Result", "").upper()
            if "VALID" in res and "INVALID" not in res:
                valid_count += 1
            elif "INVALID" in res:
                invalid_count += 1
            elif "NEEDS REVIEW" in res or "REVIEW" in res:
                needs_review_count += 1

            ptype = r.get("Internal/External", "").upper()
            if ptype == "INTERNAL":
                internal_count += 1
            elif ptype == "EXTERNAL":
                external_count += 1

            reason_lower = r.get("Reason", "").lower()
            if "casual leave" in reason_lower:
                casual_leave_conflicts += 1
            if "emergency leave" in reason_lower:
                emergency_leave_conflicts += 1
            if "holiday" in reason_lower:
                holiday_conflicts += 1
            if "unpaid" in reason_lower or "loss of pay" in reason_lower:
                unpaid_leave_conflicts += 1
            if "missing" in reason_lower or "unavailable" in reason_lower:
                missing_attendance_cases += 1
            if "ood" in reason_lower or (res == "VALID" and ptype == "EXTERNAL"):
                ood_cases += 1

            # Faculty breakdown
            fname = r.get("Faculty Name", "") or r.get("Faculty ID", "Unknown")
            faculty_breakdown[fname] = faculty_breakdown.get(fname, 0) + 1

            # Month breakdown from Start Date (e.g. MM/YYYY)
            st_date = r.get("Start Date", "")
            if len(st_date) == 10 and "/" in st_date:
                parts = st_date.split("/")
                if len(parts) == 3:
                    m_key = f"{parts[1]}/{parts[2]}"
                    month_breakdown[m_key] = month_breakdown.get(m_key, 0) + 1

        total_leave_conflicts = casual_leave_conflicts + emergency_leave_conflicts + unpaid_leave_conflicts

        return {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "needs_review": needs_review_count,
            "internal": internal_count,
            "external": external_count,
            "ood_cases": ood_cases,
            "casual_leave_conflicts": casual_leave_conflicts,
            "emergency_leave_conflicts": emergency_leave_conflicts,
            "holiday_conflicts": holiday_conflicts,
            "unpaid_leave_conflicts": unpaid_leave_conflicts,
            "total_leave_conflicts": total_leave_conflicts,
            "missing_attendance_cases": missing_attendance_cases,
            "faculty_breakdown": faculty_breakdown,
            "month_breakdown": month_breakdown
        }
