import os
import csv
from person2_integration import Person2Verifier

def main():
    from pathlib import Path
    base_dir = str(Path(__file__).resolve().parent / "fdp_data")
    faculty_file = os.path.join(base_dir, 'faculty_master.csv')
    attendance_file = os.path.join(base_dir, 'attendance_sheet.csv')
    tracker_file = os.path.join(base_dir, 'certificate_tracker.csv')
    verified_file = os.path.join(base_dir, 'certificate_tracker_verified.csv')

    # 1. Initialize Person 2
    verifier = Person2Verifier(faculty_file, attendance_file)

    # Load previously verified results for comparison
    with open(verified_file, 'r', encoding='utf-8') as f:
        verified_data = list(csv.DictReader(f))

    expected_results = {row['CERTIFICATE ID']: row['VERIFICATION RESULT'] for row in verified_data}

    # Load original tracker and process one by one
    with open(tracker_file, 'r', encoding='utf-8') as f:
        tracker_data = list(csv.DictReader(f))

    print("--- COMPARING INTEGRATION MODULE VS ORIGINAL MODULE ---")
    mismatch_count = 0
    for row in tracker_data:
        cid = row['CERTIFICATE ID']
        result = verifier.verify_single_certificate(row)
        actual_res = result.get('VERIFICATION RESULT')
        expected_res = expected_results.get(cid)

        if actual_res != expected_res:
            print(f"Mismatch for {cid}: Expected '{expected_res}', Got '{actual_res}'")
            mismatch_count += 1

    if mismatch_count == 0:
        print("SUCCESS: Integration module results perfectly match the previously validated results (42/42).")
    else:
        print(f"FAILED: Found {mismatch_count} mismatches.")

    print("\n--- TESTING PERSON 1 TO PERSON 2 FLOW ---")

    # Mocking Person 1 pipeline
    def process_certificate_from_person1(cert_dict):
        if cert_dict.get('IS_REAL') == False:
            print(f"Cert {cert_dict.get('CERTIFICATE ID', 'Unknown')} is FAKE -> REJECTED. Person 2 is bypassed.")
            return None
        else:
            print(f"Cert {cert_dict.get('CERTIFICATE ID', 'Unknown')} is REAL -> Passing to Person 2.")
            return verifier.verify_single_certificate(cert_dict)

    fake_cert = {
        "CERTIFICATE ID": "FAKE-001",
        "IS_REAL": False,
        "FACULTY ID": "F012",
        "FDP / PROGRAM NAME": "Fake Seminar",
        "PROGRAM INSTITUTION": "Unknown",
        "START DATE": "01/01/2026",
        "END DATE": "02/01/2026",
        "NUMBER OF DAYS": "2"
    }

    real_cert = {
        "CERTIFICATE ID": "REAL-001",
        "IS_REAL": True,
        "FACULTY ID": "F012",
        "FDP / PROGRAM NAME": "Real Workshop",
        "PROGRAM INSTITUTION": "Ramaiah Institute of Technology",
        "START DATE": "07/07/2025",
        "END DATE": "11/07/2025",
        "NUMBER OF DAYS": "5"
    }

    process_certificate_from_person1(fake_cert)
    res = process_certificate_from_person1(real_cert)
    print(f"Result from Person 2 for REAL cert: {res.get('VERIFICATION RESULT')} ({res.get('VERIFICATION REASON')})")

if __name__ == '__main__':
    main()
