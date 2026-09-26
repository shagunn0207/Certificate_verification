import csv
from datetime import datetime, timedelta

class Person2Verifier:
    def __init__(self, faculty_csv_path, attendance_csv_path):
        """
        Initializes the Person 2 Verification module by pre-loading
        the master faculty and attendance datasets into memory.
        This avoids reloading the CSVs for every single certificate.
        """
        self.valid_faculty_ids = set()
        self.attendance_lookup = {}

        self._load_master_data(faculty_csv_path, attendance_csv_path)

        self.supporting_statuses = ["OOD", "PRESENT", "HOLIDAY"]
        self.conflicting_statuses = [
            "CASUAL LEAVE",
            "EMERGENCY LEAVE",
            "UNPAID LEAVE",
            "UNPAID LEAVE / LOSS OF PAY",
            "VACATION"
        ]

    def _load_master_data(self, faculty_csv_path, attendance_csv_path):
        # Load faculty
        with open(faculty_csv_path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                self.valid_faculty_ids.add(row['FACULTY ID'].strip())

        # Load attendance
        with open(attendance_csv_path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                fid = row['FACULTY ID'].strip()
                date = row['DATE'].strip()
                status = row['ATTENDANCE STATUS'].strip()
                self.attendance_lookup[(fid, date)] = status

    def _generate_date_range(self, start_str, end_str):
        start_date = datetime.strptime(start_str, "%d/%m/%Y")
        end_date = datetime.strptime(end_str, "%d/%m/%Y")

        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)

        return date_list, (end_date - start_date).days + 1

    def _normalize_institution(self, inst_str):
        """
        Normalize institution name aliases for Ramaiah Institute of Technology.
        Known aliases: MSRIT, RIT, M.S. Ramaiah Institute of Technology,
        MSRIT Bangalore, etc.
        Does NOT merge genuinely different Ramaiah institutions such as
        Ramaiah University of Applied Sciences or Ramaiah Institute of Management.
        """
        normalized = inst_str.upper().replace('.', '').strip()
        condensed = normalized.replace(' ', '')

        # Exact condensed matches for known abbreviations/aliases
        internal_aliases = {
            "MSRIT",
            "MSRITBANGALORE",
            "RIT",
            "RAMAIAHINSTITUTEOFTECHNOLOGY",
            "MSRAMAIAHINSTITUTEOFTECHNOLOGY",
        }

        if condensed in internal_aliases:
            return "Ramaiah Institute of Technology"

        # Substring check for longer variations containing the full name
        if "RAMAIAH INSTITUTE OF TECHNOLOGY" in normalized:
            return "Ramaiah Institute of Technology"

        return inst_str.strip()

    def verify_single_certificate(self, cert_data: dict) -> dict:
        """
        Takes a single extracted certificate dictionary from Person 1,
        applies the Person 2 verification rules, and returns the augmented dictionary
        with the verification results.
        """
        # Create a copy to avoid mutating the original input unexpectedly
        result_data = cert_data.copy()

        fid = result_data.get('FACULTY ID', '').strip()

        # 1. Faculty ID verification
        if fid not in self.valid_faculty_ids:
            result_data['VERIFICATION RESULT'] = "Invalid - Faculty Not Found"
            result_data['VERIFICATION REASON'] = "FACULTY ID not found in master database."
            result_data['PROGRAM TYPE'] = "N/A"
            result_data['TIMELINE MATCH'] = "N/A"
            return result_data

        # 2. Internal / External classification
        original_institution = result_data.get('PROGRAM INSTITUTION', '').strip()
        normalized_inst = self._normalize_institution(original_institution)
        result_data['PROGRAM INSTITUTION'] = normalized_inst

        if normalized_inst == "Ramaiah Institute of Technology":
            result_data['PROGRAM TYPE'] = "INTERNAL"
        else:
            result_data['PROGRAM TYPE'] = "EXTERNAL"

        # 3. Timeline verification
        try:
            start_date_str = result_data.get('START DATE', '').strip()
            end_date_str = result_data.get('END DATE', '').strip()
            dates, actual_days = self._generate_date_range(start_date_str, end_date_str)
        except ValueError:
            result_data['VERIFICATION RESULT'] = "Invalid - Timeline Mismatch"
            result_data['VERIFICATION REASON'] = "Invalid date format."
            result_data['TIMELINE MATCH'] = "No"
            return result_data

        try:
            claimed_days = int(result_data.get('NUMBER OF DAYS', -1))
        except ValueError:
            claimed_days = -1

        if actual_days != claimed_days:
            result_data['TIMELINE MATCH'] = "No"
            result_data['VERIFICATION RESULT'] = "Invalid - Timeline Mismatch"
            result_data['VERIFICATION REASON'] = f"Calculated duration ({actual_days} days) does not match claimed duration ({claimed_days} days)."
            return result_data

        result_data['TIMELINE MATCH'] = "Yes"

        # 4. Daily attendance verification
        conflict_detected = False
        missing_detected = False
        reason = ""
        found_statuses = set()

        for d in dates:
            status = self.attendance_lookup.get((fid, d))

            if status is None:
                missing_detected = True
                found_statuses.add("MISSING")
                if not reason:
                    reason = f"Missing attendance data for {d}."
                continue

            status_upper = status.upper()
            found_statuses.add(status_upper)

            if status_upper in self.conflicting_statuses or status_upper not in self.supporting_statuses:
                if not conflict_detected:
                    conflict_detected = True
                    reason = f"Conflict detected: {status} on {d}."

        result_data['ATTENDANCE STATUS'] = ", ".join(sorted(found_statuses))

        # 5. VERIFICATION RESULT + VERIFICATION REASON
        if missing_detected:
            result_data['VERIFICATION RESULT'] = "Invalid - Missing Attendance"
            result_data['VERIFICATION REASON'] = reason
        elif conflict_detected:
            result_data['VERIFICATION RESULT'] = "Invalid - Conflicting Leave"
            result_data['VERIFICATION REASON'] = reason
        else:
            result_data['VERIFICATION RESULT'] = "Valid / Verified"
            result_data['VERIFICATION REASON'] = "Timeline consistent and all dates marked as OOD."

        return result_data
