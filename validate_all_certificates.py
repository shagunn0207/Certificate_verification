"""
validate_all_certificates.py
============================
Runs every certificate in data/certificate_tracker.csv through the verification
pipeline without modifying the original datasets.
Generates an audit report in results/validation_report.csv.
"""

import os
import csv
import sys
import hashlib
from typing import Dict, Any, List

# Ensure project root is in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.data_loader import DataLoader
from src.pipeline import VerificationPipeline


def get_file_md5(path: str) -> str:
    """Calculates MD5 checksum of a file to verify immutability."""
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    tracker_path = os.path.join(ROOT_DIR, "data", "certificate_tracker.csv")
    attendance_path = os.path.join(ROOT_DIR, "data", "attendance_sheet.csv")
    faculty_path = os.path.join(ROOT_DIR, "data", "faculty_master.csv")
    output_dir = os.path.join(ROOT_DIR, "results")
    report_path = os.path.join(output_dir, "validation_report.csv")

    os.makedirs(output_dir, exist_ok=True)

    # 1. Record pre-execution checksums of original datasets
    tracker_md5_before = get_file_md5(tracker_path)
    attendance_md5_before = get_file_md5(attendance_path)
    faculty_md5_before = get_file_md5(faculty_path)

    print("=" * 80)
    print("INSTITUTIONAL CERTIFICATE VERIFICATION - AUDIT VALIDATION RUN")
    print("=" * 80)
    print(f"Source Tracker: {tracker_path}")
    print(f"Initial Checksum (MD5): {tracker_md5_before}")

    data_loader = DataLoader()
    pipeline = VerificationPipeline()

    tracker_rows = data_loader.get_certificate_tracker_rows()
    print(f"Total Certificates to Validate: {len(tracker_rows)}")
    print("-" * 80)

    report_rows = []
    matches = 0
    disagreements = 0

    agreement_by_class = {
        "INTERNAL": {"agree": 0, "disagree": 0},
        "EXTERNAL": {"agree": 0, "disagree": 0}
    }

    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    for idx, row in enumerate(tracker_rows, 1):
        cid = row.get("CERTIFICATE ID", f"ROW-{idx}")
        fid = row.get("FACULTY ID", "")
        fname = row.get("FACULTY NAME", "")
        inst = row.get("PROGRAM INSTITUTION", "")
        ptype = row.get("PROGRAM TYPE", "")
        sdate = row.get("START DATE", "")
        edate = row.get("END DATE", "")
        expected = row.get("VERIFICATION RESULT", "").strip().upper()

        # Run verification without modifying original tracker (save_to_history=False for audit test)
        res = pipeline.verify_existing_certificate(row, save_to_history=False)

        computed = res.get("final_result", "").strip().upper()
        reason = res.get("final_reason", "")
        rule_res = res.get("rule_engine", {}).get("RULE_RESULT", "")
        ml_res = res.get("ml_model", {}).get("prediction", "")
        ml_conf = res.get("ml_model", {}).get("confidence", 0.0)

        is_agree = (computed == expected)
        if is_agree:
            matches += 1
            status_symbol = "[MATCH]"
        else:
            disagreements += 1
            status_symbol = "[DISAGREE]"

        norm_ptype = "INTERNAL" if "INTERNAL" in ptype.upper() else "EXTERNAL"
        if is_agree:
            agreement_by_class[norm_ptype]["agree"] += 1
        else:
            agreement_by_class[norm_ptype]["disagree"] += 1

        print(f"[{idx:02d}/{len(tracker_rows):02d}] {cid} | {fname[:18]:18s} | {ptype:8s} | "
              f"Expected: {expected:7s} | Computed: {computed:7s} | {status_symbol}")

        report_rows.append({
            "Certificate ID": cid,
            "Faculty ID": fid,
            "Faculty Name": fname,
            "Institution": inst,
            "Program Type": ptype,
            "Start Date": sdate,
            "End Date": edate,
            "Expected (Tracker)": expected,
            "Computed Result": computed,
            "Agreement": "YES" if is_agree else "NO",
            "Rule Engine Result": rule_res,
            "ML Prediction": ml_res,
            "ML Confidence": f"{ml_conf * 100:.1f}%",
            "Reason": reason
        })

    # Write report CSV
    fieldnames = [
        "Certificate ID", "Faculty ID", "Faculty Name", "Institution",
        "Program Type", "Start Date", "End Date", "Expected (Tracker)",
        "Computed Result", "Agreement", "Rule Engine Result", "ML Prediction",
        "ML Confidence", "Reason"
    ]
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_rows)

    # Verify dataset immutability
    tracker_md5_after = get_file_md5(tracker_path)
    attendance_md5_after = get_file_md5(attendance_path)
    faculty_md5_after = get_file_md5(faculty_path)

    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    total = len(tracker_rows)
    acc = (matches / total) * 100 if total > 0 else 0
    print(f"Total Evaluated : {total}")
    print(f"Agreements      : {matches} ({acc:.1f}%)")
    print(f"Disagreements   : {disagreements}")
    print(f"Internal Certs  : {agreement_by_class['INTERNAL']['agree']} agree, {agreement_by_class['INTERNAL']['disagree']} disagree")
    print(f"External Certs  : {agreement_by_class['EXTERNAL']['agree']} agree, {agreement_by_class['EXTERNAL']['disagree']} disagree")
    print(f"Audit Report    : {report_path}")
    print("-" * 80)
    print("DATASET INTEGRITY CHECK (Source data must be UNCHANGED):")
    tracker_intact = (tracker_md5_before == tracker_md5_after)
    attendance_intact = (attendance_md5_before == attendance_md5_after)
    faculty_intact = (faculty_md5_before == faculty_md5_after)
    print(f"  certificate_tracker.csv : {'PASS (UNCHANGED)' if tracker_intact else 'FAIL (MUTATED!)'}")
    print(f"  attendance_sheet.csv    : {'PASS (UNCHANGED)' if attendance_intact else 'FAIL (MUTATED!)'}")
    print(f"  faculty_master.csv      : {'PASS (UNCHANGED)' if faculty_intact else 'FAIL (MUTATED!)'}")
    print("=" * 80)

    if not tracker_intact:
        sys.exit(1)


if __name__ == "__main__":
    main()
