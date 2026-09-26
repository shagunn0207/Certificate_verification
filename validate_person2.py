import os
import csv
from person2_verification import run_verification, generate_date_range

def main():
    from pathlib import Path
    base_dir = str(Path(__file__).resolve().parent / "fdp_data")
    faculty_file = os.path.join(base_dir, "faculty_master.csv")
    attendance_file = os.path.join(base_dir, "attendance_sheet.csv")
    tracker_file = os.path.join(base_dir, "certificate_tracker.csv")
    output_file = os.path.join(base_dir, "certificate_tracker_verified.csv")

    # Check if original is modified (using stat mtime)
    original_mtime = os.stat(tracker_file).st_mtime

    verified_data = run_verification(faculty_file, attendance_file, tracker_file, output_file)

    new_mtime = os.stat(tracker_file).st_mtime
    original_modified = (original_mtime != new_mtime)

    total = len(verified_data)
    counts = {
        "Valid / Verified": 0,
        "Invalid - Conflicting Leave": 0,
        "Invalid - Missing Attendance": 0,
        "Invalid - Timeline Mismatch": 0,
        "Invalid - Faculty Not Found": 0
    }

    print("--- FULL CERTIFICATE REPORT ---")
    for row in verified_data:
        res = row.get('VERIFICATION RESULT', '')
        if res in counts:
            counts[res] += 1
        elif res.startswith("Invalid - Conflicting Leave"):
            counts["Invalid - Conflicting Leave"] += 1

        try:
            _, calc_days = generate_date_range(row['START DATE'].strip(), row['END DATE'].strip())
        except:
            calc_days = "N/A"

        print(f"CERT ID: {row['CERTIFICATE ID']}")
        print(f"  FACULTY ID: {row['FACULTY ID']}")
        print(f"  PROGRAM TYPE: {row.get('PROGRAM TYPE', 'N/A')}")
        print(f"  START DATE: {row['START DATE']}")
        print(f"  END DATE: {row['END DATE']}")
        print(f"  NUMBER OF DAYS: {row['NUMBER OF DAYS']}")
        print(f"  CALCULATED DAYS: {calc_days}")
        print(f"  RESULT: {row.get('VERIFICATION RESULT', 'N/A')}")
        print(f"  REASON: {row.get('VERIFICATION REASON', 'N/A')}")
        print("-" * 40)

    print("\n--- SUMMARY ---")
    print(f"Total certificates processed: {total}")
    for k, v in counts.items():
        print(f"{k}: {v}")

    print(f"\nOriginal certificate_tracker.csv modified: {original_modified}")

if __name__ == "__main__":
    main()
