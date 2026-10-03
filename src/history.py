import os
import csv
import re
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
    "Reason",
    "Fingerprint"
]

FEEDBACK_HEADERS = [
    "Feedback ID",
    "Timestamp",
    "Verification ID",
    "Certificate ID",
    "Faculty Name",
    "FDP Name",
    "Feedback Type",
    "Comment",
    "Is Duplicate Context"
]


def _normalize_for_fingerprint(value: str) -> str:
    """
    Normalizes a string for fingerprint comparison:
    - Lowercases
    - Strips leading/trailing whitespace
    - Collapses multiple spaces to single space
    - Removes common honorifics for name fields
    """
    if not value:
        return ""
    clean = value.strip().lower()
    clean = re.sub(r'\s+', ' ', clean)
    return clean


def _normalize_name_for_fingerprint(name: str) -> str:
    """
    Normalize a faculty name for duplicate comparison.
    Removes honorifics, extra spaces, punctuation differences.
    """
    if not name:
        return ""
    clean = name.strip().lower()
    # Remove common honorifics
    clean = re.sub(r'^(dr\.?\s*|prof\.?\s*|mr\.?\s*|ms\.?\s*|mrs\.?\s*)', '', clean, flags=re.IGNORECASE)
    # Remove punctuation
    clean = re.sub(r'[.\-,]', ' ', clean)
    # Collapse whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


def _normalize_date_for_fingerprint(date_str: str) -> str:
    """Normalize date to a consistent format for comparison."""
    if not date_str:
        return ""
    clean = date_str.strip()
    # Already in DD/MM/YYYY format from the pipeline
    return clean


def compute_certificate_fingerprint(cert_data: Dict[str, Any]) -> str:
    """
    Computes a robust fingerprint for a certificate based on extracted data.
    Uses: faculty name + institution + FDP name + start date + end date + certificate number.
    
    This ensures duplicate detection is NOT based on filename, but on the actual
    certificate content extracted by the system.
    """
    parts = [
        _normalize_name_for_fingerprint(str(cert_data.get("FACULTY NAME", ""))),
        _normalize_for_fingerprint(str(cert_data.get("FACULTY ID", ""))),
        _normalize_for_fingerprint(str(cert_data.get("PROGRAM INSTITUTION", ""))),
        _normalize_for_fingerprint(str(cert_data.get("FDP / PROGRAM NAME", ""))),
        _normalize_date_for_fingerprint(str(cert_data.get("START DATE", ""))),
        _normalize_date_for_fingerprint(str(cert_data.get("END DATE", ""))),
        _normalize_for_fingerprint(str(cert_data.get("CERTIFICATE ID", ""))),
    ]
    # Join with a delimiter that won't appear in certificate data
    fingerprint = "||".join(parts)
    return fingerprint


class VerificationHistoryManager:
    def __init__(self, results_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.results_dir = os.path.join(base_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)

        self.results_file = results_path or os.path.join(self.results_dir, "verification_results.csv")
        self.feedback_file = os.path.join(self.results_dir, "feedback.csv")
        self._ensure_file_exists()
        self._ensure_feedback_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.results_file):
            with open(self.results_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(HISTORY_HEADERS)
        else:
            # Migrate existing file: add Fingerprint column if missing
            self._migrate_add_fingerprint_column()

    def _migrate_add_fingerprint_column(self):
        """Add Fingerprint column to existing verification_results.csv if missing."""
        try:
            with open(self.results_file, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header and "Fingerprint" not in header:
                    # Need to add the column
                    rows = []
                    rows.append(header + ["Fingerprint"])
                    for row in reader:
                        # Compute fingerprint from existing fields
                        # Map header to values
                        row_dict = dict(zip(header, row))
                        fp_parts = [
                            _normalize_name_for_fingerprint(row_dict.get("Faculty Name", "")),
                            _normalize_for_fingerprint(row_dict.get("Faculty ID", "")),
                            _normalize_for_fingerprint(row_dict.get("Institution", "")),
                            _normalize_for_fingerprint(row_dict.get("FDP Name", "")),
                            _normalize_date_for_fingerprint(row_dict.get("Start Date", "")),
                            _normalize_date_for_fingerprint(row_dict.get("End Date", "")),
                            _normalize_for_fingerprint(row_dict.get("Certificate ID", "")),
                        ]
                        fingerprint = "||".join(fp_parts)
                        row.append(fingerprint)
                        rows.append(row)

                    with open(self.results_file, mode='w', newline='', encoding='utf-8') as wf:
                        writer = csv.writer(wf)
                        writer.writerows(rows)
        except Exception:
            pass  # Don't break on migration errors

    def _ensure_feedback_file_exists(self):
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(FEEDBACK_HEADERS)

    def find_duplicate(self, cert_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Checks if a certificate with the same fingerprint already exists
        in the verification history.
        
        Returns the matching existing record if duplicate found, None otherwise.
        """
        new_fingerprint = compute_certificate_fingerprint(cert_data)
        if not new_fingerprint or new_fingerprint == "||||||":
            # All fields empty — cannot reliably detect duplicates
            return None

        records = self.get_all_records()
        for record in records:
            existing_fp = record.get("Fingerprint", "")
            if not existing_fp:
                # Compute fingerprint from record fields for backward compatibility
                existing_fp_parts = [
                    _normalize_name_for_fingerprint(record.get("Faculty Name", "")),
                    _normalize_for_fingerprint(record.get("Faculty ID", "")),
                    _normalize_for_fingerprint(record.get("Institution", "")),
                    _normalize_for_fingerprint(record.get("FDP Name", "")),
                    _normalize_date_for_fingerprint(record.get("Start Date", "")),
                    _normalize_date_for_fingerprint(record.get("End Date", "")),
                    _normalize_for_fingerprint(record.get("Certificate ID", "")),
                ]
                existing_fp = "||".join(existing_fp_parts)

            if new_fingerprint == existing_fp:
                return record

        return None

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

        fingerprint = compute_certificate_fingerprint(cert_data)

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
            "Reason": final_reason,
            "Fingerprint": fingerprint
        }

        with open(self.results_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=HISTORY_HEADERS)
            writer.writerow(row)

        return row

    def record_feedback(self, verification_id: str, certificate_id: str,
                        faculty_name: str, fdp_name: str,
                        feedback_type: str, comment: str = "",
                        is_duplicate_context: bool = False) -> Dict[str, Any]:
        """
        Records user feedback persistently to results/feedback.csv.
        """
        feedback_id = f"FB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = {
            "Feedback ID": feedback_id,
            "Timestamp": ts,
            "Verification ID": verification_id,
            "Certificate ID": certificate_id,
            "Faculty Name": faculty_name,
            "FDP Name": fdp_name,
            "Feedback Type": feedback_type,
            "Comment": comment,
            "Is Duplicate Context": "Yes" if is_duplicate_context else "No"
        }

        with open(self.feedback_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FEEDBACK_HEADERS)
            writer.writerow(row)

        return row

    def get_all_feedback(self) -> List[Dict[str, str]]:
        """Retrieves all feedback records."""
        if not os.path.exists(self.feedback_file):
            return []
        with open(self.feedback_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def get_all_records(self) -> List[Dict[str, str]]:
        """
        Retrieves all verification history records.
        """
        if not os.path.exists(self.results_file):
            return []
        with open(self.results_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def get_unique_records(self) -> List[Dict[str, str]]:
        """
        Returns only unique verification records, deduplicating by fingerprint.
        Keeps the FIRST occurrence of each unique fingerprint.
        This is used for statistics to ensure counts are correct.
        """
        records = self.get_all_records()
        seen_fingerprints = set()
        unique = []
        for r in records:
            fp = r.get("Fingerprint", "")
            if not fp:
                # Compute for backward compatibility
                fp_parts = [
                    _normalize_name_for_fingerprint(r.get("Faculty Name", "")),
                    _normalize_for_fingerprint(r.get("Faculty ID", "")),
                    _normalize_for_fingerprint(r.get("Institution", "")),
                    _normalize_for_fingerprint(r.get("FDP Name", "")),
                    _normalize_date_for_fingerprint(r.get("Start Date", "")),
                    _normalize_date_for_fingerprint(r.get("End Date", "")),
                    _normalize_for_fingerprint(r.get("Certificate ID", "")),
                ]
                fp = "||".join(fp_parts)
            if fp not in seen_fingerprints:
                seen_fingerprints.add(fp)
                unique.append(r)
        return unique

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
        Uses UNIQUE records (deduplicated by fingerprint) so that duplicate uploads
        do not inflate counts.
        Never hardcodes any statistics.
        """
        # Use unique records for statistics to prevent duplicate inflation
        records = self.get_unique_records()
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
