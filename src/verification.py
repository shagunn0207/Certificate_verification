from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from src.utils import (
    generate_date_range,
    extract_month_year,
    extract_month_name_year,
    parse_date_flexible
)
from src.data_loader import DataLoader

SUPPORTING_STATUSES_INTERNAL = {"PRESENT", "OOD", "HOLIDAY"}
SUPPORTING_STATUSES_EXTERNAL = {"OOD", "HOLIDAY"}

CONFLICTING_STATUSES = {
    "CASUAL LEAVE",
    "EMERGENCY LEAVE",
    "UNPAID LEAVE",
    "UNPAID LEAVE / LOSS OF PAY",
    "VACATION"
}

class RuleVerificationEngine:
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader

    def verify(self, cert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies deterministic verification rules according to project specification.
        Returns dictionary containing:
        - RULE_RESULT: 'VALID', 'INVALID', or 'NEEDS REVIEW'
        - RULE_REASON: Detailed explainable reason
        - DAILY_ATTENDANCE: List of dicts with [{'date': d, 'status': s, 'flag': f}]
        - TIMELINE_MATCH: 'Yes', 'No', or 'N/A'
        - CONFLICT_COUNT: number of conflicting days
        - MISSING_COUNT: number of missing attendance days
        - ATTENDANCE_COVERAGE: ratio of available dates to required dates
        """
        result = {
            "RULE_RESULT": "NEEDS REVIEW",
            "RULE_REASON": "",
            "DAILY_ATTENDANCE": [],
            "TIMELINE_MATCH": "N/A",
            "ACTUAL_DAYS": 0,
            "CLAIMED_DAYS": 0,
            "CONFLICT_COUNT": 0,
            "MISSING_COUNT": 0,
            "ATTENDANCE_COVERAGE": 0.0,
            "DATE_LIST": []
        }

        fid = cert_data.get("FACULTY ID", "").strip()
        faculty_matched = cert_data.get("FACULTY_MATCHED", True)

        # 1. Faculty verification
        if not faculty_matched or not fid or fid not in self.data_loader.faculty_by_id:
            result["RULE_RESULT"] = "NEEDS REVIEW"
            result["RULE_REASON"] = "Faculty could not be reliably matched with the Faculty Master."
            return result

        # 2. Date extraction validation
        start_str = cert_data.get("START DATE", "").strip()
        end_str = cert_data.get("END DATE", "").strip()

        if not start_str or not end_str:
            result["RULE_RESULT"] = "NEEDS REVIEW"
            result["RULE_REASON"] = "FDP start/end date could not be determined."
            return result

        try:
            date_list, actual_days = generate_date_range(start_str, end_str)
            result["DATE_LIST"] = date_list
            result["ACTUAL_DAYS"] = actual_days
        except ValueError as e:
            err_msg = str(e)
            result["RULE_RESULT"] = "INVALID"
            if "earlier than start date" in err_msg.lower():
                result["RULE_REASON"] = "Certificate contains an invalid FDP date range."
            else:
                result["RULE_REASON"] = f"Invalid date format: {err_msg}"
            result["TIMELINE_MATCH"] = "No"
            return result

        # 3. Timeline matching (actual duration vs claimed duration)
        claimed_days_raw = cert_data.get("NUMBER OF DAYS", "")
        claimed_days = -1
        try:
            if claimed_days_raw:
                claimed_days = int(claimed_days_raw)
                result["CLAIMED_DAYS"] = claimed_days
        except ValueError:
            claimed_days = -1

        if claimed_days > 0 and actual_days != claimed_days:
            result["TIMELINE_MATCH"] = "No"
            result["RULE_RESULT"] = "INVALID"
            result["RULE_REASON"] = f"Calculated duration ({actual_days} days) does not match claimed duration ({claimed_days} days)."
            # Still record daily attendance for complete evidence
        else:
            result["TIMELINE_MATCH"] = "Yes"

        # 4. Check entire month attendance availability first (Case 1)
        # Check every month touched by the FDP date range
        months_in_fdp = {}
        for d in date_list:
            my = extract_month_year(d)
            m_name = extract_month_name_year(d)
            if my and my not in months_in_fdp:
                months_in_fdp[my] = m_name

        for my, m_name in months_in_fdp.items():
            if not self.data_loader.is_month_available(fid, my):
                result["RULE_RESULT"] = "NEEDS REVIEW"
                result["RULE_REASON"] = f"Attendance records for {m_name} are unavailable. The certificate cannot be automatically verified against attendance data."
                # Fill missing for dates
                for d in date_list:
                    result["DAILY_ATTENDANCE"].append({
                        "date": d,
                        "status": "UNAVAILABLE (MONTH MISSING)",
                        "flag": "MISSING_MONTH"
                    })
                result["MISSING_COUNT"] = len(date_list)
                result["ATTENDANCE_COVERAGE"] = 0.0
                return result

        # 5. Daily Attendance Verification across all dates
        is_internal = cert_data.get("PROGRAM TYPE", "EXTERNAL").upper() == "INTERNAL"
        supporting_set = SUPPORTING_STATUSES_INTERNAL if is_internal else SUPPORTING_STATUSES_EXTERNAL

        daily_records = []
        missing_dates = []
        conflicts = []
        available_days = 0

        for d in date_list:
            status = self.data_loader.get_attendance(fid, d)

            if status is None:
                missing_dates.append(d)
                daily_records.append({
                    "date": d,
                    "status": "NO RECORD",
                    "flag": "MISSING_DATE"
                })
                continue

            available_days += 1
            status_clean = status.strip()
            status_upper = status_clean.upper()

            # Check if this status is a conflict
            is_conflict = False
            conflict_label = status_clean

            if status_upper in CONFLICTING_STATUSES:
                is_conflict = True
            elif not is_internal and status_upper == "PRESENT":
                # External FDP requires OOD / HOLIDAY; PRESENT on campus indicates a conflict
                is_conflict = True
                conflict_label = "Present on campus (Conflict with external FDP)"
            elif status_upper not in supporting_set:
                is_conflict = True

            if is_conflict:
                conflicts.append((d, status_clean))
                daily_records.append({
                    "date": d,
                    "status": status_clean,
                    "flag": "CONFLICT"
                })
            else:
                daily_records.append({
                    "date": d,
                    "status": status_clean,
                    "flag": "VALID"
                })

        result["DAILY_ATTENDANCE"] = daily_records
        result["CONFLICT_COUNT"] = len(conflicts)
        result["MISSING_COUNT"] = len(missing_dates)
        result["ATTENDANCE_COVERAGE"] = available_days / len(date_list) if date_list else 0.0

        # Prioritize timeline mismatch if already detected
        if result["TIMELINE_MATCH"] == "No":
            return result

        # 6. Evaluate Rule Results
        # Case 2: Month exists, but individual required date is missing -> NEEDS REVIEW
        if missing_dates:
            result["RULE_RESULT"] = "NEEDS REVIEW"
            if len(missing_dates) == 1:
                result["RULE_REASON"] = f"Attendance record for {missing_dates[0]} is unavailable. The complete FDP period could not be verified."
            else:
                missing_str = ", ".join(missing_dates)
                result["RULE_REASON"] = f"Attendance records for {missing_str} are unavailable. The complete FDP period could not be verified."
            return result

        # If any conflicts detected -> INVALID
        if conflicts:
            result["RULE_RESULT"] = "INVALID"
            first_date, first_status = conflicts[0]
            if len(conflicts) == 1:
                result["RULE_REASON"] = f"Attendance record shows {first_status} on {first_date}, which conflicts with the FDP attendance period."
            else:
                conflict_details = "; ".join([f"{st} on {dt}" for dt, st in conflicts])
                result["RULE_REASON"] = f"Attendance conflicts detected: {conflict_details}, which conflict with the FDP attendance period."
            return result

        # All required dates exist and match supporting statuses -> VALID
        result["RULE_RESULT"] = "VALID"
        result["RULE_REASON"] = "Timeline consistent and all required dates verified in attendance records."
        return result
