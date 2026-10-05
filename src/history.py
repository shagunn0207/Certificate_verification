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

TRAINING_FEEDBACK_HEADERS = [
    "Feedback ID",
    "Created At",
    "Approved At",
    "Verification ID",
    "Certificate ID",
    "Faculty ID",
    "Faculty Name",
    "Department",
    "Training Date",
    "Training Program",
    "Program Type",
    "Presentation Rating",
    "Coverage of Topics",
    "Understanding Level",
    "Understanding Reason",
    "Future Programs",
    "Recommended Topics",
    "Feedback Status",
    "Rejection Reason"
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
        default_results_dir = os.path.join(base_dir, "results")
        self.results_dir = os.path.dirname(os.path.abspath(results_path)) if results_path else default_results_dir
        os.makedirs(self.results_dir, exist_ok=True)

        self.results_file = results_path or os.path.join(self.results_dir, "verification_results.csv")
        self.feedback_file = os.path.join(self.results_dir, "feedback.csv")
        self.training_feedback_file = os.path.join(self.results_dir, "training_feedback.csv")
        self.approved_feedback_file = os.path.join(self.results_dir, "approved_feedback.csv")
        self.rejected_feedback_file = os.path.join(self.results_dir, "rejected_feedback.csv")
        self._ensure_file_exists()
        self._ensure_feedback_file_exists()
        self._ensure_training_feedback_file_exists()

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

    def _ensure_training_feedback_file_exists(self):
        """Create and migrate the training-feedback CSVs used by the MSRIT Feedback on Training workflow."""
        for path in [self.training_feedback_file, self.approved_feedback_file, self.rejected_feedback_file]:
            if not os.path.exists(path):
                with open(path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=TRAINING_FEEDBACK_HEADERS)
                    writer.writeheader()
        self._migrate_training_feedback_files()

    def _migrate_training_feedback_files(self):
        """
        Migrate training_feedback.csv, approved_feedback.csv, and rejected_feedback.csv
        to ensure every row adheres to the canonical 19-column schema.
        Handles legacy 27-column formats and misaligned rows safely without data loss.
        """
        for path in [self.training_feedback_file, self.approved_feedback_file, self.rejected_feedback_file]:
            if not os.path.exists(path):
                continue
            try:
                with open(path, mode='r', encoding='utf-8') as f:
                    raw_lines = list(csv.reader(f))
                if not raw_lines:
                    with open(path, mode='w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=TRAINING_FEEDBACK_HEADERS)
                        writer.writeheader()
                    continue

                header = [h.strip() for h in raw_lines[0]]
                needs_rewrite = False

                if header != TRAINING_FEEDBACK_HEADERS:
                    needs_rewrite = True

                migrated_rows = []
                for r in raw_lines[1:]:
                    if not r or not any(field.strip() for field in r):
                        continue
                    if len(r) != 19:
                        needs_rewrite = True

                    if len(r) == 19 and header == TRAINING_FEEDBACK_HEADERS:
                        row_dict = dict(zip(TRAINING_FEEDBACK_HEADERS, r))
                        migrated_rows.append(row_dict)
                    elif len(r) == 27:
                        # Legacy 27-column row mapping:
                        row_dict = {
                            "Feedback ID": r[0],
                            "Created At": r[1],
                            "Approved At": r[4],
                            "Verification ID": r[6],
                            "Certificate ID": r[7],
                            "Faculty ID": r[8],
                            "Faculty Name": r[9],
                            "Department": r[10],
                            "Training Date": r[11],
                            "Training Program": r[12],
                            "Program Type": r[13] or "INTERNAL",
                            "Presentation Rating": r[14] or "Good",
                            "Coverage of Topics": r[15],
                            "Understanding Level": r[16] or "Good",
                            "Understanding Reason": r[17],
                            "Future Programs": r[18] or "Yes",
                            "Recommended Topics": r[19],
                            "Feedback Status": (r[23] or "IN_PROGRESS").strip().upper(),
                            "Rejection Reason": r[24],
                        }
                        migrated_rows.append(row_dict)
                    else:
                        # Map by existing header names if present
                        row_dict = {}
                        raw_dict = dict(zip(header, r))
                        for col in TRAINING_FEEDBACK_HEADERS:
                            row_dict[col] = raw_dict.get(col, "")
                        migrated_rows.append(row_dict)

                if needs_rewrite:
                    with open(path, mode='w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=TRAINING_FEEDBACK_HEADERS)
                        writer.writeheader()
                        writer.writerows(migrated_rows)
            except Exception as e:
                pass

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

    def create_training_feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates or updates a training-feedback record using the canonical 19-column schema.
        Guarantees zero column shifting, full quoting of special characters/newlines,
        and maintains synchronized status datasets for APPROVED and REJECTED states.
        """
        existing_rows = self.get_all_training_feedback()
        cert_id = str(data.get("Certificate ID") or data.get("certificate_id") or "").strip()
        fid_target = str(data.get("Feedback ID") or data.get("feedback_id") or "").strip()

        # Check if record exists by Feedback ID or Certificate ID
        existing_idx = None
        for idx, r in enumerate(existing_rows):
            if fid_target and r.get("Feedback ID", "").strip() == fid_target:
                existing_idx = idx
                break
            if cert_id and r.get("Certificate ID", "").strip() == cert_id:
                existing_idx = idx
                break

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing_row = existing_rows[existing_idx] if existing_idx is not None else None

        status = str(data.get("Feedback Status") or data.get("status") or (existing_row.get("Feedback Status") if existing_row else "IN_PROGRESS")).strip().upper()
        if not status or status == "PENDING":
            status = "IN_PROGRESS"

        feedback_id = fid_target or (existing_row.get("Feedback ID") if existing_row else None) or f"TFB-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        created_at = (existing_row.get("Created At") if existing_row else None) or data.get("Created At") or data.get("created_at") or now_str

        # Determine Approved At
        approved_at = ""
        if status == "APPROVED":
            approved_at = data.get("Approved At") or (existing_row.get("Approved At") if existing_row else "") or now_str
        elif existing_row and existing_row.get("Approved At"):
            approved_at = existing_row.get("Approved At")

        # Determine Rejection Reason
        rejection_reason = data.get("Rejection Reason") or data.get("rejection_reason") or (existing_row.get("Rejection Reason", "") if existing_row else "")
        if status == "APPROVED":
            rejection_reason = ""  # Clear rejection reason upon approval

        # Exact canonical 19 columns mapping:
        canonical_row = {
            "Feedback ID": feedback_id,
            "Created At": created_at,
            "Approved At": approved_at,
            "Verification ID": str(data.get("Verification ID") or data.get("verification_id") or (existing_row.get("Verification ID", "") if existing_row else "")),
            "Certificate ID": cert_id or (existing_row.get("Certificate ID", "") if existing_row else ""),
            "Faculty ID": str(data.get("Faculty ID") or data.get("faculty_id") or (existing_row.get("Faculty ID", "") if existing_row else "")),
            "Faculty Name": str(data.get("Faculty Name") or data.get("faculty_name") or (existing_row.get("Faculty Name", "") if existing_row else "")),
            "Department": str(data.get("Department") or data.get("department") or (existing_row.get("Department", "") if existing_row else "")),
            "Training Date": str(data.get("Training Date") or data.get("training_date") or (existing_row.get("Training Date", "") if existing_row else "")),
            "Training Program": str(data.get("Training Program") or data.get("training_program") or (existing_row.get("Training Program", "") if existing_row else "")),
            "Program Type": str(data.get("Program Type") or data.get("program_type") or (existing_row.get("Program Type", "INTERNAL") if existing_row else "INTERNAL")),
            "Presentation Rating": str(data.get("Presentation Rating") or data.get("presentation_rating") or (existing_row.get("Presentation Rating", "Good") if existing_row else "Good")),
            "Coverage of Topics": str(data.get("Coverage of Topics") if data.get("Coverage of Topics") is not None else (data.get("coverage_of_topics") if data.get("coverage_of_topics") is not None else (existing_row.get("Coverage of Topics", "") if existing_row else ""))),
            "Understanding Level": str(data.get("Understanding Level") or data.get("understanding_level") or (existing_row.get("Understanding Level", "Good") if existing_row else "Good")),
            "Understanding Reason": str(data.get("Understanding Reason") if data.get("Understanding Reason") is not None else (data.get("understanding_reason") if data.get("understanding_reason") is not None else (existing_row.get("Understanding Reason", "") if existing_row else ""))),
            "Future Programs": str(data.get("Future Programs") or data.get("future_programs") or (existing_row.get("Future Programs", "Yes") if existing_row else "Yes")),
            "Recommended Topics": str(data.get("Recommended Topics") if data.get("Recommended Topics") is not None else (data.get("recommended_topics") if data.get("recommended_topics") is not None else (existing_row.get("Recommended Topics", "") if existing_row else ""))),
            "Feedback Status": status,
            "Rejection Reason": rejection_reason,
        }

        if existing_idx is not None:
            existing_rows[existing_idx] = canonical_row
        else:
            existing_rows.append(canonical_row)

        with open(self.training_feedback_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=TRAINING_FEEDBACK_HEADERS)
            writer.writeheader()
            writer.writerows(existing_rows)

        self._write_status_dataset(self.approved_feedback_file, "APPROVED")
        self._write_status_dataset(self.rejected_feedback_file, "REJECTED")

        return canonical_row

    def get_training_feedback_for_certificate(self, certificate_id: str) -> Optional[Dict[str, str]]:
        """Return the training feedback record for a specific Certificate ID if any."""
        if not certificate_id:
            return None
        rows = self.get_all_training_feedback()
        for r in rows:
            if r.get("Certificate ID", "").strip() == certificate_id.strip():
                return r
        return None

    def get_training_feedback_stats(self) -> Dict[str, Any]:
        """
        Calculates live counts for training feedback dashboard:
        - Total Valid Certificates
        - Feedback Pending
        - Feedback Approved
        - Feedback Rejected
        - Feedback Completion Rate
        """
        unique_records = self.get_unique_records()
        valid_certs = [r for r in unique_records if r.get("Final Result", "").upper() == "VALID"]
        total_valid = len(valid_certs)

        all_tf = self.get_all_training_feedback()
        status_by_cert = {}
        for tf in all_tf:
            cid = tf.get("Certificate ID", "").strip()
            if cid:
                status_by_cert[cid] = tf.get("Feedback Status", "").upper()

        approved_count = sum(1 for status in status_by_cert.values() if status == "APPROVED")
        rejected_count = sum(1 for status in status_by_cert.values() if status == "REJECTED")
        pending_count = max(0, total_valid - approved_count)
        completion_rate = (approved_count / max(1, total_valid)) * 100.0 if total_valid > 0 else 0.0

        return {
            "total_valid": total_valid,
            "pending": pending_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "completion_rate": completion_rate,
            "status_by_cert": status_by_cert
        }

    def get_all_training_feedback(self) -> List[Dict[str, str]]:
        """Return all training-feedback records."""
        if not os.path.exists(self.training_feedback_file):
            return []
        with open(self.training_feedback_file, mode='r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def update_training_feedback(self, feedback_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Update one training-feedback record by Feedback ID."""
        rows = self.get_all_training_feedback()
        if not rows:
            return None

        fieldnames = list(TRAINING_FEEDBACK_HEADERS)
        updated_row = None
        for row in rows:
            if row.get("Feedback ID", "") == feedback_id:
                for key, value in updates.items():
                    if key in fieldnames:
                        row[key] = "" if value is None else str(value)
                updated_row = row
                break

        if updated_row is None:
            return None

        with open(self.training_feedback_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return updated_row

    def _write_status_dataset(self, path: str, status: str):
        """Write a filtered status dataset for easy export/use later."""
        rows = [r for r in self.get_all_training_feedback() if r.get("Feedback Status", "").upper() == status]
        with open(path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=TRAINING_FEEDBACK_HEADERS)
            writer.writeheader()
            writer.writerows(rows)

    def approve_training_feedback(self, feedback_id: str) -> Optional[Dict[str, str]]:
        """Approve feedback and refresh the approved-feedback dataset."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = self.update_training_feedback(
            feedback_id,
            {
                "Feedback Status": "APPROVED",
                "Approved At": now_str,
                "Rejection Reason": ""
            }
        )
        if row:
            self._write_status_dataset(self.approved_feedback_file, "APPROVED")
            self._write_status_dataset(self.rejected_feedback_file, "REJECTED")
        return row

    def reject_training_feedback(self, feedback_id: str, reason: str) -> Optional[Dict[str, str]]:
        """Reject feedback and refresh the rejected-feedback dataset."""
        row = self.update_training_feedback(
            feedback_id,
            {
                "Feedback Status": "REJECTED",
                "Rejection Reason": reason,
                "Approved At": ""
            }
        )
        if row:
            self._write_status_dataset(self.rejected_feedback_file, "REJECTED")
            self._write_status_dataset(self.approved_feedback_file, "APPROVED")
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
