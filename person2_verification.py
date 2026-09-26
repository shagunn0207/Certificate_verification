import csv
from datetime import datetime, timedelta

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def generate_date_range(start_str, end_str):
    start_date = datetime.strptime(start_str, "%d/%m/%Y")
    end_date = datetime.strptime(end_str, "%d/%m/%Y")

    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime("%d/%m/%Y"))
        current_date += timedelta(days=1)

    return date_list, (end_date - start_date).days + 1

def normalize_institution(inst_str):
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

def run_verification(faculty_csv_path, attendance_csv_path, certificate_csv_path, output_csv_path=None):
    # Load data
    faculty_records = load_data(faculty_csv_path)
    attendance_records = load_data(attendance_csv_path)
    certificate_records = load_data(certificate_csv_path)

    # 1. Faculty matching setup
    valid_faculty_ids = {row['FACULTY ID'] for row in faculty_records}

    # Pre-process attendance into a fast lookup dictionary: (faculty_id, date) -> status
    attendance_lookup = {}
    for row in attendance_records:
        fid = row['FACULTY ID']
        d = row['DATE']
        status = row['ATTENDANCE STATUS']
        # If there are duplicates, we keep the last one or handle it as needed.
        # Assuming one record per faculty per date.
        attendance_lookup[(fid, d)] = status

    supporting_statuses = ["OOD", "PRESENT", "HOLIDAY"]
    conflicting_statuses = [
        "CASUAL LEAVE",
        "EMERGENCY LEAVE",
        "UNPAID LEAVE",
        "UNPAID LEAVE / LOSS OF PAY",
        "VACATION"
    ]

    for cert in certificate_records:
        fid = cert['FACULTY ID']

        # 1. Faculty ID verification
        if fid not in valid_faculty_ids:
            cert['VERIFICATION RESULT'] = "Invalid - Faculty Not Found"
            cert['VERIFICATION REASON'] = "FACULTY ID not found in master database."
            continue

        # 2 & 3. Internal / External classification
        original_institution = cert.get('PROGRAM INSTITUTION', '').strip()
        normalized_inst = normalize_institution(original_institution)
        cert['PROGRAM INSTITUTION'] = normalized_inst

        if normalized_inst == "Ramaiah Institute of Technology":
            cert['PROGRAM TYPE'] = "INTERNAL"
        else:
            cert['PROGRAM TYPE'] = "EXTERNAL"

        # 4. Timeline verification
        try:
            start_date_str = cert['START DATE'].strip()
            end_date_str = cert['END DATE'].strip()
            dates, actual_days = generate_date_range(start_date_str, end_date_str)
        except ValueError:
            cert['VERIFICATION RESULT'] = "Invalid - Timeline Mismatch"
            cert['VERIFICATION REASON'] = "Invalid date format."
            continue

        try:
            claimed_days = int(cert['NUMBER OF DAYS'])
        except ValueError:
            claimed_days = -1

        if actual_days != claimed_days:
            cert['TIMELINE MATCH'] = "No"
            cert['VERIFICATION RESULT'] = "Invalid - Timeline Mismatch"
            cert['VERIFICATION REASON'] = f"Calculated duration ({actual_days} days) does not match claimed duration ({claimed_days} days)."
            continue

        cert['TIMELINE MATCH'] = "Yes"

        # 5 & 6. Daily attendance verification
        conflict_detected = False
        missing_detected = False
        reason = ""
        found_statuses = set()

        for d in dates:
            status = attendance_lookup.get((fid, d))

            if status is None:
                missing_detected = True
                found_statuses.add("MISSING")
                if not reason:
                    reason = f"Missing attendance data for {d}."
                continue

            status_upper = status.upper()
            found_statuses.add(status_upper)

            # Check if it's a conflict
            if status_upper in conflicting_statuses or status_upper not in supporting_statuses:
                if not conflict_detected:
                    conflict_detected = True
                    # Use title case or original case for the output reason, or standardize it
                    # Using the exact original string for the reason
                    reason = f"Conflict detected: {status} on {d}."

        cert['ATTENDANCE STATUS'] = ", ".join(sorted(found_statuses))

        # 7. VERIFICATION RESULT + VERIFICATION REASON
        if missing_detected:
            cert['VERIFICATION RESULT'] = "Invalid - Missing Attendance"
            cert['VERIFICATION REASON'] = reason
        elif conflict_detected:
            cert['VERIFICATION RESULT'] = "Invalid - Conflicting Leave"
            cert['VERIFICATION REASON'] = reason
        else:
            cert['VERIFICATION RESULT'] = "Valid / Verified"
            cert['VERIFICATION REASON'] = "Timeline consistent and all dates marked as OOD."

    # Write output if requested
    if output_csv_path:
        if certificate_records:
            fieldnames = certificate_records[0].keys()
            with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(certificate_records)

    return certificate_records

if __name__ == "__main__":
    import os
    from pathlib import Path
    base_dir = str(Path(__file__).resolve().parent / "fdp_data")
    faculty_file = os.path.join(base_dir, "faculty_master.csv")
    attendance_file = os.path.join(base_dir, "attendance_sheet.csv")
    tracker_file = os.path.join(base_dir, "certificate_tracker.csv")
    output_file = os.path.join(base_dir, "certificate_tracker_verified.csv")

    if os.path.exists(tracker_file):
        print("Running verification...")
        verified_data = run_verification(faculty_file, attendance_file, tracker_file, output_file)
        print(f"Verification complete. Updated data written to {output_file}")

        # Print a few sample results
        print("\nSample Results:")
        for row in verified_data[:5]:
            print(f"Cert: {row['CERTIFICATE ID']} | Result: {row['VERIFICATION RESULT']} | Reason: {row['VERIFICATION REASON']}")
    else:
        print("Data files not found.")
