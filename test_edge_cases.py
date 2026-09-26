import os
from person2_verification import run_verification
import csv

def test_cases():
    from pathlib import Path
    base_dir = str(Path(__file__).resolve().parent / "scratch_tests")
    os.makedirs(base_dir, exist_ok=True)

    faculty_file = os.path.join(base_dir, "test_faculty.csv")
    attendance_file = os.path.join(base_dir, "test_attendance.csv")
    tracker_file = os.path.join(base_dir, "test_tracker.csv")

    # 1. Faculty
    with open(faculty_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["FACULTY ID", "FACULTY NAME"])
        writer.writeheader()
        writer.writerow({"FACULTY ID": "F001", "FACULTY NAME": "Test User"})

    # 2. Attendance
    attendance_data = [
        # all OOD (C1)
        {"FACULTY ID": "F001", "DATE": "01/01/2026", "ATTENDANCE STATUS": "OOD"},
        {"FACULTY ID": "F001", "DATE": "02/01/2026", "ATTENDANCE STATUS": "OOD"},
        # Casual Leave (C2)
        {"FACULTY ID": "F001", "DATE": "03/01/2026", "ATTENDANCE STATUS": "OOD"},
        {"FACULTY ID": "F001", "DATE": "04/01/2026", "ATTENDANCE STATUS": "CASUAL LEAVE"},
        # Emergency Leave (C3)
        {"FACULTY ID": "F001", "DATE": "05/01/2026", "ATTENDANCE STATUS": "EMERGENCY LEAVE"},
        # Holiday (C4)
        {"FACULTY ID": "F001", "DATE": "06/01/2026", "ATTENDANCE STATUS": "HOLIDAY"},
        # Unpaid Leave (C5)
        {"FACULTY ID": "F001", "DATE": "07/01/2026", "ATTENDANCE STATUS": "UNPAID LEAVE / LOSS OF PAY"},
        # Vacation (C6)
        {"FACULTY ID": "F001", "DATE": "08/01/2026", "ATTENDANCE STATUS": "VACATION"},
        # Mixed (C7)
        {"FACULTY ID": "F001", "DATE": "09/01/2026", "ATTENDANCE STATUS": "PRESENT"},
        {"FACULTY ID": "F001", "DATE": "10/01/2026", "ATTENDANCE STATUS": "CASUAL LEAVE"},
        # Missing date C8 misses 12/01/2026
        {"FACULTY ID": "F001", "DATE": "11/01/2026", "ATTENDANCE STATUS": "OOD"},
        # C9: Timeline mismatch
        {"FACULTY ID": "F001", "DATE": "13/01/2026", "ATTENDANCE STATUS": "OOD"},
        {"FACULTY ID": "F001", "DATE": "14/01/2026", "ATTENDANCE STATUS": "OOD"},
        # Institution alias tests (C11-C16): single-day OOD each
        {"FACULTY ID": "F001", "DATE": "20/01/2026", "ATTENDANCE STATUS": "OOD"},
        {"FACULTY ID": "F001", "DATE": "21/01/2026", "ATTENDANCE STATUS": "OOD"},
        {"FACULTY ID": "F001", "DATE": "22/01/2026", "ATTENDANCE STATUS": "OOD"},
        {"FACULTY ID": "F001", "DATE": "23/01/2026", "ATTENDANCE STATUS": "OOD"},
        {"FACULTY ID": "F001", "DATE": "24/01/2026", "ATTENDANCE STATUS": "OOD"},
        {"FACULTY ID": "F001", "DATE": "25/01/2026", "ATTENDANCE STATUS": "OOD"},
    ]
    with open(attendance_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["FACULTY ID", "DATE", "ATTENDANCE STATUS"])
        writer.writeheader()
        writer.writerows(attendance_data)

    # 3. Tracker
    tracker_data = [
        {"CERTIFICATE ID": "C1", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "Ramaiah Institute of Technology", "START DATE": "01/01/2026", "END DATE": "02/01/2026", "NUMBER OF DAYS": "2"},
        {"CERTIFICATE ID": "C2", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "03/01/2026", "END DATE": "04/01/2026", "NUMBER OF DAYS": "2"},
        {"CERTIFICATE ID": "C3", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "05/01/2026", "END DATE": "05/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C4", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "06/01/2026", "END DATE": "06/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C5", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "07/01/2026", "END DATE": "07/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C6", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "08/01/2026", "END DATE": "08/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C7", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "09/01/2026", "END DATE": "10/01/2026", "NUMBER OF DAYS": "2"},
        {"CERTIFICATE ID": "C8", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "11/01/2026", "END DATE": "12/01/2026", "NUMBER OF DAYS": "2"},
        {"CERTIFICATE ID": "C9", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "13/01/2026", "END DATE": "14/01/2026", "NUMBER OF DAYS": "4"},
        {"CERTIFICATE ID": "C10", "FACULTY ID": "F999", "PROGRAM INSTITUTION": "EXTERNAL", "START DATE": "15/01/2026", "END DATE": "15/01/2026", "NUMBER OF DAYS": "1"},
        # Institution alias edge cases
        {"CERTIFICATE ID": "C11", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "MSRIT", "START DATE": "20/01/2026", "END DATE": "20/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C12", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "RIT", "START DATE": "21/01/2026", "END DATE": "21/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C13", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "MSRIT Bangalore", "START DATE": "22/01/2026", "END DATE": "22/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C14", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "M.S. Ramaiah Institute of Technology", "START DATE": "23/01/2026", "END DATE": "23/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C15", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "Ramaiah University of Applied Sciences", "START DATE": "24/01/2026", "END DATE": "24/01/2026", "NUMBER OF DAYS": "1"},
        {"CERTIFICATE ID": "C16", "FACULTY ID": "F001", "PROGRAM INSTITUTION": "NIT Patna", "START DATE": "25/01/2026", "END DATE": "25/01/2026", "NUMBER OF DAYS": "1"},
    ]
    with open(tracker_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["CERTIFICATE ID", "FACULTY ID", "PROGRAM INSTITUTION", "START DATE", "END DATE", "NUMBER OF DAYS"])
        writer.writeheader()
        writer.writerows(tracker_data)

    results = run_verification(faculty_file, attendance_file, tracker_file)

    print("--- EDGE CASE TESTS ---")
    tests = [
        ("C1", "Valid / Verified", "All OOD"),
        ("C2", "Invalid - Conflicting Leave", "Casual Leave overlap"),
        ("C3", "Invalid - Conflicting Leave", "Emergency Leave overlap"),
        ("C4", "Valid / Verified", "Holiday overlap"),
        ("C5", "Invalid - Conflicting Leave", "Unpaid Leave / Loss of Pay overlap"),
        ("C6", "Invalid - Conflicting Leave", "Vacation overlap"),
        ("C7", "Invalid - Conflicting Leave", "Mixed OOD + leave (partial conflict)"),
        ("C8", "Invalid - Missing Attendance", "Missing attendance date in the middle"),
        ("C9", "Invalid - Timeline Mismatch", "Timeline mismatch"),
        ("C10", "Invalid - Faculty Not Found", "Invalid Faculty ID")
    ]

    res_dict = {r["CERTIFICATE ID"]: r for r in results}
    for cid, expected_res, desc in tests:
        actual = res_dict[cid]["VERIFICATION RESULT"]
        if actual == expected_res:
            print(f"PASS : {desc} ({actual})")
        else:
            print(f"FAIL : {desc}. Expected '{expected_res}', got '{actual}'")

    # Institution alias tests: check PROGRAM TYPE
    print("\n--- INSTITUTION ALIAS TESTS ---")
    alias_tests = [
        ("C11", "INTERNAL", "MSRIT -> INTERNAL"),
        ("C12", "INTERNAL", "RIT -> INTERNAL"),
        ("C13", "INTERNAL", "MSRIT Bangalore -> INTERNAL"),
        ("C14", "INTERNAL", "M.S. Ramaiah Institute of Technology -> INTERNAL"),
        ("C15", "EXTERNAL", "Ramaiah University of Applied Sciences -> EXTERNAL"),
        ("C16", "EXTERNAL", "NIT Patna -> EXTERNAL"),
    ]
    for cid, expected_type, desc in alias_tests:
        actual_type = res_dict[cid].get("PROGRAM TYPE", "N/A")
        if actual_type == expected_type:
            print(f"PASS : {desc} ({actual_type})")
        else:
            print(f"FAIL : {desc}. Expected '{expected_type}', got '{actual_type}'")

if __name__ == "__main__":
    test_cases()
