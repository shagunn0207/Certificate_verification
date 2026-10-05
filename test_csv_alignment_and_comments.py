import os
import csv
import tempfile
import html
from pypdf import PdfReader
from src.history import VerificationHistoryManager, TRAINING_FEEDBACK_HEADERS
from src.pdf_generator import generate_training_feedback_pdf

def test_csv_schema_and_alignment():
    print("============================================================")
    print("Testing Canonical 19-Column Schema & Comment Box Alignment")
    print("============================================================")

    with tempfile.TemporaryDirectory() as td:
        results_path = os.path.join(td, "verification_results.csv")
        hm = VerificationHistoryManager(results_path=results_path)

        # 1. Verify Header Column Count is EXACTLY 19
        assert len(TRAINING_FEEDBACK_HEADERS) == 19, f"Expected 19 columns, got {len(TRAINING_FEEDBACK_HEADERS)}"
        print(f"[PASS] TRAINING_FEEDBACK_HEADERS has exactly 19 columns: {TRAINING_FEEDBACK_HEADERS}")

        # 2. Section 8: Comment box test with exact strings
        cov_text = "TEST COVERAGE — The training was useful, practical, and well structured."
        und_reason_text = "TEST REASON — The concepts were clearly explained and easy to understand."
        rec_topics_text = "TEST RECOMMENDATION — Advanced AI and hands-on implementation."

        draft_payload = {
            "Certificate ID": "CERT_TEST_S8",
            "Verification ID": "VERIF_S8_001",
            "Faculty ID": "F012",
            "Faculty Name": "Dr. Sushma B",
            "Department": "Computer Science & Engineering",
            "Training Date": "07/07/2025",
            "Training Program": "AI and Deep Learning Essentials",
            "Program Type": "INTERNAL",
            "Presentation Rating": "Good",
            "Coverage of Topics": cov_text,
            "Understanding Level": "Good",
            "Understanding Reason": und_reason_text,
            "Future Programs": "Yes",
            "Recommended Topics": rec_topics_text,
            "Feedback Status": "IN_PROGRESS"
        }

        saved = hm.create_training_feedback(draft_payload)
        assert saved["Feedback Status"] == "IN_PROGRESS"

        # Read directly using raw csv.reader
        with open(hm.training_feedback_file, mode='r', encoding='utf-8') as f:
            raw_reader = list(csv.reader(f))

        # Check header
        assert len(raw_reader[0]) == 19
        assert raw_reader[0] == TRAINING_FEEDBACK_HEADERS

        # Check row 1
        assert len(raw_reader[1]) == 19, f"Row 1 length is {len(raw_reader[1])}, expected 19"
        row1_dict = dict(zip(raw_reader[0], raw_reader[1]))

        # Verify values appear under the exact columns
        assert row1_dict["Coverage of Topics"] == cov_text, f"Coverage mismatch: {row1_dict['Coverage of Topics']}"
        assert row1_dict["Understanding Reason"] == und_reason_text, f"Reason mismatch: {row1_dict['Understanding Reason']}"
        assert row1_dict["Recommended Topics"] == rec_topics_text, f"Recommended mismatch: {row1_dict['Recommended Topics']}"
        assert row1_dict["Faculty Name"] == "Dr. Sushma B"
        assert row1_dict["Department"] == "Computer Science & Engineering"
        assert row1_dict["Feedback Status"] == "IN_PROGRESS"
        print("[PASS] Section 8 Comment Box Test: Values correctly stored under Coverage, Reason, and Recommended Topics columns.")

        # 3. Section 9: Validate CSV Column Count across ALL rows
        for idx, row in enumerate(raw_reader):
            assert len(row) == 19, f"Row {idx} has {len(row)} columns, expected exactly 19!"
        print(f"[PASS] Section 9: Verified all {len(raw_reader)} rows in training_feedback.csv have exactly 19 fields.")

        # 4. Section 11: Multi-line and Comma comments
        multiline_comment = """The training covered AI, ML, Python and data analysis.

The practical examples were useful.

I would recommend this program again."""

        draft_payload["Coverage of Topics"] = multiline_comment
        draft_payload["Feedback Status"] = "SUBMITTED"
        updated = hm.create_training_feedback(draft_payload)

        # Re-read raw CSV
        with open(hm.training_feedback_file, mode='r', encoding='utf-8') as f:
            raw_reader_after = list(csv.reader(f))

        # Must not produce extra rows or extra columns
        assert len(raw_reader_after) == 2, f"Expected header + 1 row, got {len(raw_reader_after)} rows"
        assert len(raw_reader_after[1]) == 19, f"Expected 19 columns, got {len(raw_reader_after[1])}"
        row_after_dict = dict(zip(raw_reader_after[0], raw_reader_after[1]))
        assert row_after_dict["Coverage of Topics"] == multiline_comment
        print("[PASS] Section 11: Multi-line and comma-heavy comments remain exactly ONE properly quoted CSV field.")

        # Verify reopened draft
        reopened = hm.get_training_feedback_for_certificate("CERT_TEST_S8")
        assert reopened["Coverage of Topics"] == multiline_comment
        print("[PASS] Reopened record preserves exact multi-line comment.")

        # Verify preview escaping
        escaped_preview = html.escape(reopened["Coverage of Topics"])
        assert "AI, ML, Python and data analysis." in escaped_preview
        print("[PASS] Preview escapes and preserves multi-line string.")

        # Verify PDF generation
        pdf_bytes = generate_training_feedback_pdf(reopened)
        pdf_path = os.path.join(td, "test_multiline.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)
        reader = PdfReader(pdf_path)
        pdf_text = " ".join([p.extract_text() for p in reader.pages])
        assert "AI, ML, Python and data analysis" in pdf_text
        assert "The practical examples were useful" in pdf_text
        assert "I would recommend this program again" in pdf_text
        print("[PASS] PDF extracted text contains the full multi-line comment without corruption.")

        # 5. Check Approved and Rejected CSVs also have exactly 19 fields
        approved = hm.approve_training_feedback(updated["Feedback ID"])
        assert approved["Feedback Status"] == "APPROVED"
        with open(hm.approved_feedback_file, mode='r', encoding='utf-8') as f:
            appr_reader = list(csv.reader(f))
        for idx, row in enumerate(appr_reader):
            assert len(row) == 19, f"approved_feedback.csv row {idx} has {len(row)} columns, expected 19"
        print(f"[PASS] Section 7: approved_feedback.csv confirmed to have exactly 19 columns across all rows.")

    print("\n============================================================")
    print("ALL CANONICAL 19-COLUMN CSV ALIGNMENT & QUOTING TESTS PASSED!")
    print("============================================================")

def test_actual_file_alignment():
    print("\n=== Validating Active Repository CSV Files ===")
    for fname in ["results/training_feedback.csv", "results/approved_feedback.csv", "results/rejected_feedback.csv"]:
        with open(fname, mode='r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
        print(f"{fname}: {len(reader)} lines (Header + {len(reader)-1} rows)")
        for idx, row in enumerate(reader):
            assert len(row) == 19, f"{fname} line {idx} has {len(row)} fields, expected 19!"
        print(f"  [✓] All rows have exactly 19 fields.")

if __name__ == "__main__":
    test_csv_schema_and_alignment()
    test_actual_file_alignment()
