import pandas as pd
import numpy as np
from typing import Dict, Any, List

FEATURE_COLUMNS = [
    "is_internal",
    "duration_days",
    "claimed_days",
    "timeline_match",
    "faculty_matched",
    "cert_details_completeness",
    "ood_count",
    "present_count",
    "holiday_count",
    "casual_leave_count",
    "emergency_leave_count",
    "unpaid_leave_count",
    "vacation_count",
    "conflict_days_count",
    "missing_days_count",
    "is_month_missing",
    "attendance_coverage"
]

class FeatureEngineer:
    def __init__(self):
        self.feature_columns = FEATURE_COLUMNS

    def extract_features(self, cert_data: Dict[str, Any], rule_output: Dict[str, Any]) -> Dict[str, float]:
        """
        Extracts tabular numerical features from raw certificate data and attendance verification state.
        Avoids target leakage: does NOT include RULE_RESULT or FINAL_RESULT.
        """
        is_internal = 1.0 if str(cert_data.get("PROGRAM TYPE", "")).upper() == "INTERNAL" else 0.0
        actual_days = float(rule_output.get("ACTUAL_DAYS", 0) or 0)
        
        claimed_days_raw = cert_data.get("NUMBER OF DAYS", 0)
        try:
            claimed_days = float(claimed_days_raw) if claimed_days_raw else actual_days
        except ValueError:
            claimed_days = 0.0

        timeline_match = 1.0 if rule_output.get("TIMELINE_MATCH") == "Yes" else 0.0
        faculty_matched = 1.0 if cert_data.get("FACULTY_MATCHED", True) else 0.0

        # Completeness of extracted certificate fields
        key_fields = ["FACULTY ID", "FACULTY NAME", "FDP / PROGRAM NAME", "PROGRAM INSTITUTION", "START DATE", "END DATE"]
        filled_count = sum(1 for f in key_fields if str(cert_data.get(f, "")).strip())
        completeness = filled_count / len(key_fields)

        # Count attendance statuses
        daily_records = rule_output.get("DAILY_ATTENDANCE", [])
        ood_count = 0.0
        present_count = 0.0
        holiday_count = 0.0
        casual_leave_count = 0.0
        emergency_leave_count = 0.0
        unpaid_leave_count = 0.0
        vacation_count = 0.0

        for r in daily_records:
            st = str(r.get("status", "")).upper()
            if "OOD" in st:
                ood_count += 1.0
            elif "PRESENT" in st:
                present_count += 1.0
            elif "HOLIDAY" in st:
                holiday_count += 1.0
            elif "CASUAL" in st:
                casual_leave_count += 1.0
            elif "EMERGENCY" in st:
                emergency_leave_count += 1.0
            elif "UNPAID" in st or "LOSS OF PAY" in st:
                unpaid_leave_count += 1.0
            elif "VACATION" in st:
                vacation_count += 1.0

        conflict_count = float(rule_output.get("CONFLICT_COUNT", 0))
        missing_count = float(rule_output.get("MISSING_COUNT", 0))
        is_month_missing = 1.0 if any(r.get("flag") == "MISSING_MONTH" for r in daily_records) else 0.0
        attendance_coverage = float(rule_output.get("ATTENDANCE_COVERAGE", 0.0))

        feat_dict = {
            "is_internal": is_internal,
            "duration_days": actual_days,
            "claimed_days": claimed_days,
            "timeline_match": timeline_match,
            "faculty_matched": faculty_matched,
            "cert_details_completeness": completeness,
            "ood_count": ood_count,
            "present_count": present_count,
            "holiday_count": holiday_count,
            "casual_leave_count": casual_leave_count,
            "emergency_leave_count": emergency_leave_count,
            "unpaid_leave_count": unpaid_leave_count,
            "vacation_count": vacation_count,
            "conflict_days_count": conflict_count,
            "missing_days_count": missing_count,
            "is_month_missing": is_month_missing,
            "attendance_coverage": attendance_coverage
        }
        return feat_dict

    def to_dataframe(self, feature_dicts: List[Dict[str, float]]) -> pd.DataFrame:
        df = pd.DataFrame(feature_dicts)
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0.0
        return df[self.feature_columns]
