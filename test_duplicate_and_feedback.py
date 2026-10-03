"""
Comprehensive test suite for duplicate detection, uniqueness calculation,
count protection, faculty+department grouping, and feedback storage.
"""
import os
import sys
import csv
import shutil
import tempfile

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.history import (
    VerificationHistoryManager,
    compute_certificate_fingerprint,
    _normalize_name_for_fingerprint,
    _normalize_for_fingerprint
)

PASS_COUNT = 0
FAIL_COUNT = 0


def report(test_name, passed, details=""):
    global PASS_COUNT, FAIL_COUNT
    if passed:
        PASS_COUNT += 1
        print(f"  [PASS] {test_name}")
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] {test_name} -- {details}")


def test_fingerprint_normalization():
    """Test that fingerprinting normalizes names, whitespace, and casing."""
    print("\n=== TEST: Fingerprint Normalization ===")

    cert1 = {
        "FACULTY NAME": "Dr. Sushma B",
        "FACULTY ID": "F012",
        "PROGRAM INSTITUTION": "Ramaiah Institute of Technology",
        "FDP / PROGRAM NAME": "Quantum Computing",
        "START DATE": "07/07/2025",
        "END DATE": "11/07/2025",
        "CERTIFICATE ID": "CERT-001"
    }

    # Same data but with extra spaces and different casing
    cert2 = {
        "FACULTY NAME": "  dr.  sushma   b  ",
        "FACULTY ID": "  f012 ",
        "PROGRAM INSTITUTION": "  Ramaiah Institute   of Technology  ",
        "FDP / PROGRAM NAME": "  quantum   computing  ",
        "START DATE": "07/07/2025",
        "END DATE": "11/07/2025",
        "CERTIFICATE ID": "  cert-001  "
    }

    fp1 = compute_certificate_fingerprint(cert1)
    fp2 = compute_certificate_fingerprint(cert2)
    report("Same certificate with different formatting produces same fingerprint",
           fp1 == fp2, f"fp1={fp1!r} != fp2={fp2!r}")

    # Genuinely different certificate
    cert3 = {
        "FACULTY NAME": "Dr. Sushma B",
        "FACULTY ID": "F012",
        "PROGRAM INSTITUTION": "Ramaiah Institute of Technology",
        "FDP / PROGRAM NAME": "Machine Learning Basics",
        "START DATE": "14/07/2025",
        "END DATE": "18/07/2025",
        "CERTIFICATE ID": "CERT-002"
    }
    fp3 = compute_certificate_fingerprint(cert3)
    report("Different certificate produces different fingerprint",
           fp1 != fp3, f"fp1={fp1!r} == fp3={fp3!r}")


def test_duplicate_detection():
    """TEST 1 & TEST 2 & TEST 3: New cert inserts, duplicate is blocked, filename irrelevant."""
    print("\n=== TEST: Duplicate Detection (Tests 1, 2, 3) ===")

    # Use a temp directory for test results
    tmpdir = tempfile.mkdtemp()
    results_file = os.path.join(tmpdir, "test_verification_results.csv")
    mgr = VerificationHistoryManager(results_path=results_file)
    # Override feedback file too
    mgr.feedback_file = os.path.join(tmpdir, "test_feedback.csv")
    mgr._ensure_feedback_file_exists()

    cert_data = {
        "FACULTY NAME": "Dr. Sushma B",
        "FACULTY ID": "F012",
        "PROGRAM INSTITUTION": "Ramaiah Institute of Technology",
        "FDP / PROGRAM NAME": "Quantum Computing",
        "START DATE": "07/07/2025",
        "END DATE": "11/07/2025",
        "CERTIFICATE ID": "CERT-001",
        "PROGRAM TYPE": "INTERNAL",
        "NUMBER OF DAYS": "5"
    }

    rule_output = {"RULE_RESULT": "VALID", "ACTUAL_DAYS": 5}
    ml_output = {"prediction": "VALID", "confidence": 1.0}

    # TEST 1: Upload a new certificate
    dup = mgr.find_duplicate(cert_data)
    report("TEST 1: New certificate has no duplicate",
           dup is None, f"Found unexpected duplicate: {dup}")

    # Insert it
    mgr.record_verification(cert_data, rule_output, ml_output, "VALID", "All good")
    records_after_first = mgr.get_all_records()
    report("TEST 1: Count is 1 after first insert",
           len(records_after_first) == 1, f"Count={len(records_after_first)}")

    # TEST 2: Upload exact same certificate again
    dup = mgr.find_duplicate(cert_data)
    report("TEST 2: Same certificate detected as duplicate",
           dup is not None, "Duplicate NOT detected!")
    if dup:
        report("TEST 2: Duplicate points to original record",
               dup.get("Certificate ID") == "CERT-001",
               f"Matched wrong record: {dup.get('Certificate ID')}")

    # Don't insert duplicate — count should stay 1
    records_still = mgr.get_all_records()
    report("TEST 2: Count remains 1 (no duplicate inserted)",
           len(records_still) == 1, f"Count={len(records_still)}")

    # TEST 3: Different filename doesn't matter (we test fingerprint, not filename)
    # The fingerprint doesn't include filename at all
    cert_renamed = dict(cert_data)
    cert_renamed["FILENAME"] = "totally_different_name.pdf"
    dup = mgr.find_duplicate(cert_renamed)
    report("TEST 3: Same cert with different filename still detected as duplicate",
           dup is not None, "Duplicate NOT detected with different filename!")

    shutil.rmtree(tmpdir)


def test_different_certs_same_faculty():
    """TEST 4: Two different FDPs from same faculty remain separate."""
    print("\n=== TEST: Different Certs Same Faculty (Test 4) ===")

    tmpdir = tempfile.mkdtemp()
    results_file = os.path.join(tmpdir, "test_vr.csv")
    mgr = VerificationHistoryManager(results_path=results_file)

    cert_a = {
        "FACULTY NAME": "Dr. Sushma B",
        "FACULTY ID": "F012",
        "PROGRAM INSTITUTION": "Ramaiah Institute of Technology",
        "FDP / PROGRAM NAME": "Quantum Computing",
        "START DATE": "07/07/2025",
        "END DATE": "11/07/2025",
        "CERTIFICATE ID": "CERT-001",
        "PROGRAM TYPE": "INTERNAL",
        "NUMBER OF DAYS": "5"
    }

    cert_b = {
        "FACULTY NAME": "Dr. Sushma B",
        "FACULTY ID": "F012",
        "PROGRAM INSTITUTION": "Ramaiah Institute of Technology",
        "FDP / PROGRAM NAME": "Adaptive Learning for AI",
        "START DATE": "14/07/2025",
        "END DATE": "18/07/2025",
        "CERTIFICATE ID": "CERT-002",
        "PROGRAM TYPE": "INTERNAL",
        "NUMBER OF DAYS": "5"
    }

    rule_output = {"RULE_RESULT": "VALID", "ACTUAL_DAYS": 5}
    ml_output = {"prediction": "VALID", "confidence": 1.0}

    # Insert cert A
    mgr.record_verification(cert_a, rule_output, ml_output, "VALID", "OK")

    # cert B should NOT be a duplicate
    dup = mgr.find_duplicate(cert_b)
    report("TEST 4: Different FDP from same faculty is NOT a duplicate",
           dup is None, f"Incorrectly detected as duplicate: {dup}")

    # Insert cert B
    mgr.record_verification(cert_b, rule_output, ml_output, "VALID", "OK")

    records = mgr.get_all_records()
    report("TEST 4: Both certificates exist (count=2)",
           len(records) == 2, f"Count={len(records)}")

    # Both should appear in same faculty group
    unique = mgr.get_unique_records()
    report("TEST 4: Both are unique records",
           len(unique) == 2, f"Unique count={len(unique)}")

    shutil.rmtree(tmpdir)


def test_different_faculty_similar_names():
    """TEST 5: Two genuinely different faculty are NOT merged."""
    print("\n=== TEST: Different Faculty Similar Names (Test 5) ===")

    tmpdir = tempfile.mkdtemp()
    results_file = os.path.join(tmpdir, "test_vr.csv")
    mgr = VerificationHistoryManager(results_path=results_file)

    cert_x = {
        "FACULTY NAME": "Dr. S. Seema",
        "FACULTY ID": "F001",
        "PROGRAM INSTITUTION": "NIT Surathkal",
        "FDP / PROGRAM NAME": "AI Workshop",
        "START DATE": "10/09/2026",
        "END DATE": "12/09/2026",
        "CERTIFICATE ID": "CERT-X",
        "PROGRAM TYPE": "EXTERNAL"
    }

    cert_y = {
        "FACULTY NAME": "Dr. S. Seema Kumar",
        "FACULTY ID": "F099",
        "PROGRAM INSTITUTION": "NIT Surathkal",
        "FDP / PROGRAM NAME": "AI Workshop",
        "START DATE": "10/09/2026",
        "END DATE": "12/09/2026",
        "CERTIFICATE ID": "CERT-Y",
        "PROGRAM TYPE": "EXTERNAL"
    }

    rule_output = {"RULE_RESULT": "VALID", "ACTUAL_DAYS": 3}
    ml_output = {"prediction": "VALID", "confidence": 0.9}

    mgr.record_verification(cert_x, rule_output, ml_output, "VALID", "OK")

    # cert_y has different faculty ID AND different name → should NOT be duplicate
    dup = mgr.find_duplicate(cert_y)
    report("TEST 5: Different faculty members with similar names are NOT merged",
           dup is None, f"Incorrectly detected as duplicate: {dup}")

    shutil.rmtree(tmpdir)


def test_statistics_exclude_duplicates():
    """Verify that statistics count UNIQUE certificates only."""
    print("\n=== TEST: Statistics Exclude Duplicates ===")

    tmpdir = tempfile.mkdtemp()
    results_file = os.path.join(tmpdir, "test_vr.csv")
    mgr = VerificationHistoryManager(results_path=results_file)

    cert_data = {
        "FACULTY NAME": "Dr. Test Faculty",
        "FACULTY ID": "F100",
        "PROGRAM INSTITUTION": "Test University",
        "FDP / PROGRAM NAME": "Test FDP",
        "START DATE": "01/01/2026",
        "END DATE": "05/01/2026",
        "CERTIFICATE ID": "CERT-T01",
        "PROGRAM TYPE": "EXTERNAL"
    }

    rule_output = {"RULE_RESULT": "VALID", "ACTUAL_DAYS": 5}
    ml_output = {"prediction": "VALID", "confidence": 0.95}

    # Insert same certificate 3 times (simulating what would happen without dup check)
    mgr.record_verification(cert_data, rule_output, ml_output, "VALID", "OK")
    mgr.record_verification(cert_data, rule_output, ml_output, "VALID", "OK")
    mgr.record_verification(cert_data, rule_output, ml_output, "VALID", "OK")

    all_recs = mgr.get_all_records()
    unique_recs = mgr.get_unique_records()
    stats = mgr.get_statistics()

    report("Raw records count is 3 (all stored)",
           len(all_recs) == 3, f"All={len(all_recs)}")
    report("Unique records count is 1 (deduplicated)",
           len(unique_recs) == 1, f"Unique={len(unique_recs)}")
    report("Statistics total = 1 (uses unique records)",
           stats["total"] == 1, f"Stats total={stats['total']}")
    report("Statistics valid = 1",
           stats["valid"] == 1, f"Stats valid={stats['valid']}")

    shutil.rmtree(tmpdir)


def test_feedback_persistence():
    """TEST 6: Feedback is saved and persists."""
    print("\n=== TEST: Feedback Persistence (Test 6) ===")

    tmpdir = tempfile.mkdtemp()
    results_file = os.path.join(tmpdir, "test_vr.csv")
    mgr = VerificationHistoryManager(results_path=results_file)
    mgr.feedback_file = os.path.join(tmpdir, "test_feedback.csv")
    mgr._ensure_feedback_file_exists()

    # Submit feedback
    fb = mgr.record_feedback(
        verification_id="VERIF-TEST-001",
        certificate_id="CERT-001",
        faculty_name="Dr. Test",
        fdp_name="Test FDP",
        feedback_type="Correct result",
        comment="Everything looks good",
        is_duplicate_context=False
    )

    report("Feedback record created with ID",
           fb.get("Feedback ID", "").startswith("FB-"),
           f"ID={fb.get('Feedback ID')}")

    # Re-read from file (simulates restart)
    mgr2 = VerificationHistoryManager(results_path=results_file)
    mgr2.feedback_file = os.path.join(tmpdir, "test_feedback.csv")
    all_fb = mgr2.get_all_feedback()

    report("Feedback persists after re-read (1 entry)",
           len(all_fb) == 1, f"Count={len(all_fb)}")
    report("Feedback type is correct",
           all_fb[0].get("Feedback Type") == "Correct result",
           f"Type={all_fb[0].get('Feedback Type')}")
    report("Feedback comment is correct",
           all_fb[0].get("Comment") == "Everything looks good",
           f"Comment={all_fb[0].get('Comment')}")

    # Submit duplicate feedback
    fb2 = mgr.record_feedback(
        verification_id="VERIF-DUP-001",
        certificate_id="CERT-001",
        faculty_name="Dr. Test",
        fdp_name="Test FDP",
        feedback_type="Yes — duplicate detected correctly",
        comment="",
        is_duplicate_context=True
    )

    all_fb2 = mgr.get_all_feedback()
    report("Two feedback entries after second submission",
           len(all_fb2) == 2, f"Count={len(all_fb2)}")
    report("Second feedback has duplicate context",
           all_fb2[1].get("Is Duplicate Context") == "Yes",
           f"Context={all_fb2[1].get('Is Duplicate Context')}")

    shutil.rmtree(tmpdir)


def test_name_normalization_edge_cases():
    """Test normalization preserves genuinely different names."""
    print("\n=== TEST: Name Normalization Edge Cases ===")

    # Same person, different formatting
    report("'Dr. Sushma B' and 'sushma b' normalize to same",
           _normalize_name_for_fingerprint("Dr. Sushma B") == _normalize_name_for_fingerprint("sushma b"))

    report("'  Dr.  Sushma   B  ' normalizes correctly",
           _normalize_name_for_fingerprint("  Dr.  Sushma   B  ") == _normalize_name_for_fingerprint("Dr. Sushma B"))

    # Different people
    report("'Dr. Sushma B' != 'Dr. Mallegowda M'",
           _normalize_name_for_fingerprint("Dr. Sushma B") != _normalize_name_for_fingerprint("Dr. Mallegowda M"))


def test_fingerprint_column_migration():
    """Test that existing CSV without Fingerprint column gets migrated."""
    print("\n=== TEST: Fingerprint Column Migration ===")

    tmpdir = tempfile.mkdtemp()
    results_file = os.path.join(tmpdir, "test_vr.csv")

    # Write a CSV without the Fingerprint column
    old_headers = [
        "Verification ID", "Timestamp", "Certificate ID", "Faculty ID",
        "Faculty Name", "FDP Name", "Institution", "Internal/External",
        "Start Date", "End Date", "Duration (Days)", "ML Prediction",
        "ML Confidence", "Rule Result", "Final Result", "Tracker Original Result",
        "Agreement", "Reason"
    ]
    with open(results_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(old_headers)
        writer.writerow([
            "VERIF-001", "2026-01-01 00:00:00", "CERT-001", "F012",
            "Dr. Sushma B", "Quantum Computing", "Ramaiah Institute of Technology",
            "INTERNAL", "07/07/2025", "11/07/2025", "5", "VALID", "100.0%",
            "VALID", "VALID", "VALID", "YES", "All good"
        ])

    # Initialize manager — should trigger migration
    mgr = VerificationHistoryManager(results_path=results_file)

    records = mgr.get_all_records()
    report("Migration adds Fingerprint column",
           "Fingerprint" in records[0] if records else False,
           f"Keys={list(records[0].keys()) if records else 'no records'}")

    report("Migrated fingerprint is non-empty",
           len(records[0].get("Fingerprint", "")) > 0 if records else False)

    # Duplicate detection should work on migrated data
    cert_dup = {
        "FACULTY NAME": "Dr. Sushma B",
        "FACULTY ID": "F012",
        "PROGRAM INSTITUTION": "Ramaiah Institute of Technology",
        "FDP / PROGRAM NAME": "Quantum Computing",
        "START DATE": "07/07/2025",
        "END DATE": "11/07/2025",
        "CERTIFICATE ID": "CERT-001"
    }
    dup = mgr.find_duplicate(cert_dup)
    report("Duplicate detected after migration",
           dup is not None, "Duplicate NOT detected after migration!")

    shutil.rmtree(tmpdir)


def main():
    global PASS_COUNT, FAIL_COUNT
    print("=" * 60)
    print("FDP Certificate Verification — Comprehensive Test Suite")
    print("=" * 60)

    test_fingerprint_normalization()
    test_duplicate_detection()
    test_different_certs_same_faculty()
    test_different_faculty_similar_names()
    test_statistics_exclude_duplicates()
    test_feedback_persistence()
    test_name_normalization_edge_cases()
    test_fingerprint_column_migration()

    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS_COUNT} passed, {FAIL_COUNT} failed, {PASS_COUNT + FAIL_COUNT} total")
    print("=" * 60)

    if FAIL_COUNT > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
