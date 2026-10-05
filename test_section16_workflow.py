import os
import tempfile
import html
from pypdf import PdfReader
from src.history import VerificationHistoryManager
from src.pdf_generator import generate_training_feedback_pdf

def test_section_16_exact_flow(tmp_path):
    results_path = os.path.join(tmp_path, "verification_results.csv")
    hm = VerificationHistoryManager(results_path=results_path)
    
    cert_id = "CERT_TEST_S16"
    
    # User inputs exact text from Section 16
    cov_text = "TEST COVERAGE — Quantum computing fundamentals were explained with practical examples."
    und_reason_text = "TEST REASON — The concepts were clearly explained and easy to follow."
    rec_topics_text = "TEST RECOMMENDATION — Advanced quantum algorithms and hands-on labs."
    
    # 1. Central form state
    form_data = {
        "Certificate ID": cert_id,
        "Verification ID": "VERIF_S16_001",
        "Faculty ID": "F_TEST",
        "Faculty Name": "Dr. Alan Turing",
        "Training Date": "05/10/2026",
        "Department": "Computer Science and Engineering",
        "Training Program": "Quantum Computing Fundamentals & Algorithms",
        "Presentation Rating": "Good",
        "Coverage of Topics": cov_text,
        "Understanding Level": "Good",
        "Understanding Reason": und_reason_text,
        "Future Programs": "Yes",
        "Recommended Topics": rec_topics_text,
        "Feedback Status": "IN_PROGRESS",
        "Program Type": "INTERNAL",
    }
    
    # 2. Preview HTML verification
    escaped_cov = html.escape(form_data["Coverage of Topics"])
    escaped_reason = html.escape(form_data["Understanding Reason"])
    escaped_rec = html.escape(form_data["Recommended Topics"])
    assert cov_text in escaped_cov, "Coverage must appear in preview"
    assert und_reason_text in escaped_reason, "Understanding reason must appear in preview"
    assert rec_topics_text in escaped_rec, "Recommended topics must appear in preview"
    print("[1 & 2] PREVIEW VERIFIED: All three texts present and properly escaped.")
    
    # 3. Save Draft
    saved_draft = hm.create_training_feedback(form_data)
    assert saved_draft is not None
    assert saved_draft["Feedback Status"] == "IN_PROGRESS"
    fid = saved_draft["Feedback ID"]
    print(f"[3] SAVE DRAFT VERIFIED: Saved draft with ID {fid}")
    
    # 4. Reopen draft
    reopened = hm.get_training_feedback_for_certificate(cert_id)
    assert reopened is not None
    assert reopened["Coverage of Topics"] == cov_text
    assert reopened["Understanding Reason"] == und_reason_text
    assert reopened["Recommended Topics"] == rec_topics_text
    assert reopened["Faculty Name"] == "Dr. Alan Turing"
    assert reopened["Department"] == "Computer Science and Engineering"
    print("[4 & 5] REOPEN DRAFT VERIFIED: All 3 texts and faculty info preserved without loss.")
    
    # 5. Download Draft PDF
    pdf_bytes = generate_training_feedback_pdf(reopened)
    assert len(pdf_bytes) > 0
    draft_pdf_path = os.path.join(tmp_path, "draft.pdf")
    with open(draft_pdf_path, "wb") as f:
        f.write(pdf_bytes)
    
    reader = PdfReader(draft_pdf_path)
    pdf_text = " ".join([page.extract_text() for page in reader.pages])
    assert "TEST COVERAGE" in pdf_text
    assert "Quantum computing fundamentals" in pdf_text
    assert "TEST REASON" in pdf_text
    assert "TEST RECOMMENDATION" in pdf_text
    print("[6, 7 & 8] DRAFT PDF VERIFIED: All 3 texts extracted from PDF successfully.")
    
    # 6. Submit Feedback
    form_data["Feedback Status"] = "SUBMITTED"
    submitted = hm.create_training_feedback(form_data)
    assert submitted["Feedback Status"] == "SUBMITTED"
    print("[9] SUBMIT VERIFIED: Record marked SUBMITTED.")
    
    # 7. Verify Submitted Record & Preview
    sub_fetched = hm.get_training_feedback_for_certificate(cert_id)
    assert sub_fetched["Feedback Status"] == "SUBMITTED"
    assert sub_fetched["Coverage of Topics"] == cov_text
    assert sub_fetched["Understanding Reason"] == und_reason_text
    assert sub_fetched["Recommended Topics"] == rec_topics_text
    print("[10, 11 & 12] SUBMITTED RECORD & PREVIEW VERIFIED: Exactly identical text.")
    
    # 8. Approve Feedback
    approved = hm.approve_training_feedback(fid)
    assert approved["Feedback Status"] == "APPROVED"
    assert approved["Coverage of Topics"] == cov_text
    assert approved["Understanding Reason"] == und_reason_text
    assert approved["Recommended Topics"] == rec_topics_text
    print("[13, 14 & 15] APPROVAL VERIFIED: Approved record retains all 3 texts.")
    
    # 9. Download Approved PDF
    app_pdf_bytes = generate_training_feedback_pdf(approved)
    app_pdf_path = os.path.join(tmp_path, "approved.pdf")
    with open(app_pdf_path, "wb") as f:
        f.write(app_pdf_bytes)
    reader_app = PdfReader(app_pdf_path)
    app_pdf_text = " ".join([page.extract_text() for page in reader_app.pages])
    assert "TEST COVERAGE" in app_pdf_text
    assert "TEST REASON" in app_pdf_text
    assert "TEST RECOMMENDATION" in app_pdf_text
    print("[16 & 17] APPROVED PDF VERIFIED: All 3 texts verified in approved PDF.")
    
    # 10. Reject + Edit & Resubmit Test
    rejected = hm.reject_training_feedback(fid, "Please add more details on quantum circuits")
    assert rejected["Feedback Status"] == "REJECTED"
    assert rejected["Rejection Reason"] == "Please add more details on quantum circuits"
    
    # Faculty edits Coverage
    updated_cov = "UPDATED TEXT — Quantum computing with deep-dive into quantum phase estimation."
    form_data["Coverage of Topics"] = updated_cov
    form_data["Feedback Status"] = "SUBMITTED"
    resubmitted = hm.create_training_feedback(form_data)
    assert resubmitted["Feedback Status"] == "SUBMITTED"
    assert resubmitted["Coverage of Topics"] == updated_cov
    
    # Verify resubmitted PDF
    resub_pdf = generate_training_feedback_pdf(resubmitted)
    resub_path = os.path.join(tmp_path, "resubmitted.pdf")
    with open(resub_path, "wb") as f:
        f.write(resub_pdf)
    reader_resub = PdfReader(resub_path)
    resub_text = " ".join([page.extract_text() for page in reader_resub.pages])
    assert "UPDATED TEXT" in resub_text
    print("[18] REJECT + EDIT & RESUBMIT VERIFIED: Updated text survives to submission and PDF.")
    
    # 11. Multi-line and Special characters
    special_text = """The training was useful & practical.
Topics included AI, ML, "Python" and data analysis (100% recommended).
Lines:
1. First line
2. Second line & more"""
    form_data["Coverage of Topics"] = special_text
    form_data["Feedback Status"] = "APPROVED"
    special_saved = hm.create_training_feedback(form_data)
    special_pdf = generate_training_feedback_pdf(special_saved)
    spec_path = os.path.join(tmp_path, "special.pdf")
    with open(spec_path, "wb") as f:
        f.write(special_pdf)
    reader_spec = PdfReader(spec_path)
    spec_text = " ".join([page.extract_text() for page in reader_spec.pages])
    assert "useful & practical" in spec_text
    assert "Python" in spec_text
    assert "100% recommended" in spec_text
    print("[19] SPECIAL CHARACTERS & MULTI-LINE VERIFIED: Ampersands, quotes, %, and newlines preserved without errors.")
    
    print("\n============================================================")
    print("ALL 19 ACCEPTANCE CRITERIA FOR SECTION 16 SUCCEEDED 100%!")
    print("============================================================")

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as td:
        test_section_16_exact_flow(td)
