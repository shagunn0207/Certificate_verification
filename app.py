import os
import io
import time
import re
import html
import textwrap
import pandas as pd
import streamlit as st
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="MSRIT FDP Certificate Verification System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern design aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .main {
        background-color: #0b0f19;
        color: #f1f5f9;
    }

    .header-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .stat-card {
        background: rgba(30, 41, 59, 0.7);
        border-radius: 14px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }

    .stat-num {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .stat-label {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        font-weight: 600;
    }

    .result-banner-valid {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.05) 100%);
        border: 1px solid #10b981;
        border-radius: 14px;
        padding: 20px;
        color: #34d399;
    }

    .result-banner-invalid {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.05) 100%);
        border: 1px solid #ef4444;
        border-radius: 14px;
        padding: 20px;
        color: #f87171;
    }

    .result-banner-review {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(217, 119, 6, 0.05) 100%);
        border: 1px solid #f59e0b;
        border-radius: 14px;
        padding: 20px;
        color: #fbbf24;
    }

    .result-banner-duplicate {
        background: linear-gradient(135deg, rgba(168, 85, 247, 0.18) 0%, rgba(139, 92, 246, 0.06) 100%);
        border: 1px solid #a855f7;
        border-radius: 14px;
        padding: 20px;
        color: #c084fc;
    }

    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 700;
    }
    .badge-valid { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
    .badge-invalid { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
    .badge-review { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }
    .badge-internal { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; }
    .badge-external { background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #a855f7; }
    .badge-duplicate { background: rgba(168, 85, 247, 0.25); color: #e9d5ff; border: 1px solid #a855f7; }

    .faculty-group-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.7) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 12px 0 8px 0;
    }

    .feedback-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        margin-top: 12px;
    }

    /* --- Official MSRIT Feedback on Training Form Styling --- */
    .official-form-container {
        background: #ffffff !important;
        color: #111827 !important;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        max-width: 820px;
        margin: 16px auto 24px auto;
        padding: 44px 50px;
        font-family: 'Times New Roman', Times, 'Georgia', serif !important;
        line-height: 1.5;
        box-sizing: border-box;
    }
    .official-form-container * {
        font-family: 'Times New Roman', Times, 'Georgia', serif !important;
    }
    .official-form-container p,
    .official-form-container div,
    .official-form-container span,
    .official-form-container label,
    .official-form-container b {
        color: #111827 !important;
    }
    .official-doc-input input,
    .official-doc-input textarea {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border: 1px solid #94a3b8 !important;
        border-radius: 4px !important;
        font-family: 'Times New Roman', Times, 'Georgia', serif !important;
        font-size: 15px !important;
    }
    .official-doc-input input:focus,
    .official-doc-input textarea:focus {
        border-color: #2563eb !important;
        background-color: #ffffff !important;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }
    .hod-locked-box {
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0 16px 0;
        color: #64748b !important;
        font-style: italic;
        font-size: 13.5px;
    }
    .official-action-toolbar {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .official-print-btn {
        background: #1e293b;
        color: #ffffff !important;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s ease;
    }
    .official-print-btn:hover {
        background: #334155;
        border-color: #94a3b8;
    }

    @media print {
        header, [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"],
        .no-print, button, .stButton, .stDownloadButton, [data-testid="stFormSubmitButton"],
        .header-banner, .stat-card, .official-action-toolbar, .stTabs {
            display: none !important;
        }
        body, .main, .stApp {
            background: #ffffff !important;
            color: #000000 !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        .official-form-container {
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            background: #ffffff !important;
            color: #000000 !important;
        }
        .official-form-container * {
            color: #000000 !important;
        }
        @page {
            size: A4 portrait;
            margin: 15mm;
        }
    }
</style>
""", unsafe_allow_html=True)

# Imports from src pipeline
from src.pipeline import VerificationPipeline
from src.data_loader import DataLoader
from src.utils import normalize_date_to_ddmmyyyy
from src.pdf_generator import generate_training_feedback_pdf, sanitize_filename
from src.sheets_sync import sync_feedback_to_google_sheet


def _sync_to_sheet(record: dict, label: str = "") -> None:
    """Fire-and-forget Google Sheets sync with a lightweight status toast."""
    try:
        result = sync_feedback_to_google_sheet(record)
        if result.get("status") == "SYNCED":
            st.toast(f"📊 Google Sheet updated{' — ' + label if label else ''}", icon="✅")
        elif result.get("status") == "NOT_CONFIGURED":
            pass  # Silently skip — credentials not yet set up
        else:
            st.toast(f"⚠️ Sheet sync: {result.get('message', 'unknown error')}", icon="⚠️")
    except Exception as _exc:
        st.toast(f"⚠️ Sheet sync error: {_exc}", icon="⚠️")

@st.cache_resource
def get_pipeline():
    return VerificationPipeline()

pipeline = get_pipeline()

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 10px 0 20px 0;'>
        <h2 style='margin:0; font-weight:800; color:#6366f1; letter-spacing:-0.5px;'>Ramaiah Institute of Technology</h2>
        <div style='font-size: 12px; color: #94a3b8; font-weight: 600; text-transform: uppercase;'>FDP Certificate Verification System</div>
        <div style='margin-top: 8px;'><span class='badge badge-internal'>AIML Automated Pipeline</span></div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "🔍 Verify New Certificate",
            "📝 Training Feedback",
            "📁 Existing Certificates",
            "📜 Verification History",
            "🤖 Model Performance",
            "💬 Feedback",
            "ℹ️ About"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### 🏛️ Faculty Master")
    fac_count = len(pipeline.data_loader.faculty_by_id)
    att_count = len(pipeline.data_loader.attendance_lookup)
    st.caption(f"**Faculty Registered:** {fac_count}")
    st.caption(f"**Attendance Records:** {att_count}")
    st.caption("**Institution Source:** MSRIT / RIT")

# Helper to render metric cards
def render_metrics_cards(stats):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-label'>Total Certificates</div>
            <div class='stat-num' style='color:#f8fafc;'>{stats['total']}</div>
            <div style='font-size:12px; color:#94a3b8;'>Internal: {stats['internal']} | External: {stats['external']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-label'>Verified Valid</div>
            <div class='stat-num' style='color:#10b981;'>{stats['valid']}</div>
            <div style='font-size:12px; color:#10b981;'>{(stats['valid']/max(1, stats['total'])*100):.1f}% verification rate</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-label'>Flagged Invalid</div>
            <div class='stat-num' style='color:#ef4444;'>{stats['invalid']}</div>
            <div style='font-size:12px; color:#ef4444;'>{stats['total_leave_conflicts']} leave conflicts</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-label'>Needs Review</div>
            <div class='stat-num' style='color:#f59e0b;'>{stats['needs_review']}</div>
            <div style='font-size:12px; color:#f59e0b;'>{stats['missing_attendance_cases']} missing attendance</div>
        </div>
        """, unsafe_allow_html=True)


def _normalize_group_key(value: str) -> str:
    """Normalize a string for grouping: lowercase, strip, collapse whitespace."""
    if not value:
        return ""
    clean = value.strip().lower()
    clean = re.sub(r'\s+', ' ', clean)
    return clean


def _normalize_faculty_display(name: str) -> str:
    """Return a clean display name preserving original casing but fixing spacing."""
    if not name:
        return "Unknown"
    return re.sub(r'\s+', ' ', name.strip())


def render_feedback_section(verification_id: str, certificate_id: str,
                           faculty_name: str, fdp_name: str,
                           is_duplicate: bool = False):
    """Renders the feedback form after verification or duplicate detection."""
    st.markdown("---")
    st.markdown("#### 💬 Submit Feedback")

    if is_duplicate:
        st.markdown("""
        <div class='feedback-card'>
            <div style='font-size:15px; font-weight:700; color:#c084fc; margin-bottom:8px;'>
                🔍 Was this duplicate detection correct?
            </div>
        </div>
        """, unsafe_allow_html=True)
        fb_type = st.radio(
            "Duplicate detection accuracy",
            ["Yes — duplicate detected correctly",
             "No — this is NOT a duplicate"],
            key=f"dup_fb_{verification_id}",
            label_visibility="collapsed"
        )
        fb_comment = st.text_area(
            "Tell us what was wrong (optional)",
            key=f"dup_comment_{verification_id}",
            placeholder="Describe any issue with the duplicate detection..."
        )
    else:
        fb_type = st.radio(
            "How accurate was this verification result?",
            ["Correct result",
             "Incorrect result",
             "Duplicate detected incorrectly",
             "Duplicate was not detected",
             "Other"],
            key=f"fb_type_{verification_id}"
        )
        fb_comment = st.text_area(
            "Additional comments (optional)",
            key=f"fb_comment_{verification_id}",
            placeholder="Share details about the verification accuracy..."
        )

    if st.button("📩 Submit Feedback", key=f"fb_submit_{verification_id}"):
        try:
            pipeline.history_manager.record_feedback(
                verification_id=verification_id,
                certificate_id=certificate_id,
                faculty_name=faculty_name,
                fdp_name=fdp_name,
                feedback_type=fb_type,
                comment=fb_comment,
                is_duplicate_context=is_duplicate
            )
            st.success("✅ Thank you! Your feedback has been saved successfully.")
        except Exception as e:
            st.error(f"Error saving feedback: {e}")


def _get_logo_base64() -> str:
    """Return base64 string of MSRIT logo."""
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "msrit_logo.png")
    if os.path.exists(logo_path):
        import base64
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def safe_markdown_html(html_str: str):
    """Safely render HTML in Streamlit without triggering CommonMark code-block indentation."""
    clean = re.sub(r'^[ \t]+', '', textwrap.dedent(html_str).strip(), flags=re.MULTILINE)
    st.markdown(clean, unsafe_allow_html=True)


def render_training_feedback_form(verification_id: str, cert: dict, show_back_button: bool = False):
    """
    Renders the official MSRIT/IQAC Feedback on Training workflow for a VALID certificate.
    Visually and structurally reproduces the official MSRIT form from media_1791211291171.png.
    GUARANTEES: The website form inputs are the single source of truth.
    Any changes typed into the fields flow through to Preview, Save Draft, Submit, PDF, and Approval.
    """
    if not cert:
        st.error("Certificate information could not be loaded.")
        return

    faculty_id = str(cert.get("FACULTY ID", cert.get("Faculty ID", ""))).strip()
    faculty_name = str(cert.get("FACULTY NAME", cert.get("Faculty Name", ""))).strip()
    training_date = str(cert.get("START DATE", cert.get("Start Date", cert.get("Training Date", "")))).strip()
    training_program = str(cert.get("FDP / PROGRAM NAME", cert.get("FDP Name", cert.get("Training Program", "")))).strip()
    program_type = str(cert.get("PROGRAM TYPE", cert.get("Internal/External", cert.get("Program Type", "")))).strip().upper()
    certificate_id = str(cert.get("CERTIFICATE ID", cert.get("Certificate ID", ""))).strip()

    if not verification_id or verification_id == "N/A":
        verification_id = str(cert.get("Verification ID", cert.get("VERIFICATION ID", f"VERIF-{certificate_id}"))).strip()

    master_dept = pipeline.data_loader.get_faculty_department(
        faculty_id=faculty_id,
        faculty_name=faculty_name
    )

    form_state_key = f"tf_active_state_{certificate_id}"
    preview_key = f"preview_mode_{certificate_id}"

    # Widget Keys
    k_emp = f"tf_in_emp_{certificate_id}"
    k_date = f"tf_in_date_{certificate_id}"
    k_dept = f"tf_in_dept_{certificate_id}"
    k_prog = f"tf_in_prog_{certificate_id}"
    k_pres = f"tf_in_pres_{certificate_id}"
    k_cov = f"tf_in_cov_{certificate_id}"
    k_und = f"tf_in_und_{certificate_id}"
    k_und_reason = f"tf_in_und_reason_{certificate_id}"
    k_future = f"tf_in_future_{certificate_id}"
    k_rec_topics = f"tf_in_rec_topics_{certificate_id}"

    # 1. Initialize or load central form state
    existing_fb = pipeline.history_manager.get_training_feedback_for_certificate(certificate_id) or {}
    if form_state_key not in st.session_state:
        st.session_state[form_state_key] = {
            "Feedback ID": existing_fb.get("Feedback ID", "") or "",
            "Verification ID": verification_id,
            "Certificate ID": certificate_id,
            "Faculty ID": faculty_id,
            "Faculty Name": existing_fb.get("Faculty Name") or faculty_name,
            "Department": existing_fb.get("Department") or master_dept,
            "Training Date": existing_fb.get("Training Date") or training_date,
            "Training Program": existing_fb.get("Training Program") or training_program,
            "Program Type": program_type,
            "Presentation Rating": existing_fb.get("Presentation Rating") or "Good",
            "Coverage of Topics": existing_fb.get("Coverage of Topics") or "",
            "Understanding Level": existing_fb.get("Understanding Level") or "Good",
            "Understanding Reason": existing_fb.get("Understanding Reason") or "",
            "Future Programs": existing_fb.get("Future Programs") or "Yes",
            "Recommended Topics": existing_fb.get("Recommended Topics") or "",
            "Feedback Status": existing_fb.get("Feedback Status") or "NOT_STARTED",
            "Rejection Reason": existing_fb.get("Rejection Reason") or "",
            "Approved At": existing_fb.get("Approved At") or "",
            "HOD General Remarks": existing_fb.get("HOD General Remarks") or ""
        }

    form_state = st.session_state[form_state_key]

    # 2. LIVE SYNCHRONIZATION: Whatever the user typed into the browser widgets is the IMMEDIATE truth!
    if k_emp in st.session_state:
        form_state["Faculty Name"] = st.session_state[k_emp]
    if k_date in st.session_state:
        form_state["Training Date"] = st.session_state[k_date]
    if k_dept in st.session_state:
        form_state["Department"] = st.session_state[k_dept]
    if k_prog in st.session_state:
        form_state["Training Program"] = st.session_state[k_prog]
    if k_pres in st.session_state:
        form_state["Presentation Rating"] = st.session_state[k_pres]
    if k_cov in st.session_state:
        form_state["Coverage of Topics"] = st.session_state[k_cov]
    if k_und in st.session_state:
        form_state["Understanding Level"] = st.session_state[k_und]
    if k_und_reason in st.session_state:
        form_state["Understanding Reason"] = st.session_state[k_und_reason]
    if k_future in st.session_state:
        form_state["Future Programs"] = st.session_state[k_future]
    if k_rec_topics in st.session_state:
        form_state["Recommended Topics"] = st.session_state[k_rec_topics]

    current_status = str(form_state.get("Feedback Status", "NOT_STARTED")).upper()
    if current_status == "APPROVED" and preview_key not in st.session_state:
        st.session_state[preview_key] = True
    is_preview = st.session_state.get(preview_key, False)

    # 3. Action Toolbar / Header
    safe_markdown_html("<div class='official-action-toolbar no-print'>")
    col_tb1, col_tb2, col_tb3 = st.columns([3, 2, 2])
    with col_tb1:
        if show_back_button:
            if st.button("⬅️ Back to Training Feedback Dashboard", key=f"back_tbl_{certificate_id}"):
                st.session_state.pop("selected_training_cert_id", None)
                st.session_state.pop(preview_key, None)
                st.session_state.pop(form_state_key, None)
                st.rerun()
    with col_tb2:
        status_colors = {
            "APPROVED": "#10b981",
            "REJECTED": "#ef4444",
            "SUBMITTED": "#3b82f6",
            "PENDING": "#f59e0b",
            "IN_PROGRESS": "#8b5cf6",
            "DRAFT": "#8b5cf6",
            "NOT_STARTED": "#94a3b8"
        }
        badge_color = status_colors.get(current_status, "#94a3b8")
        safe_markdown_html(f"""
        <div style='text-align: center; margin-top: 6px;'>
            <span style='font-size: 11px; text-transform: uppercase; color: #94a3b8; font-weight: 700; margin-right: 6px;'>Status:</span>
            <span style='background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}; padding: 4px 12px; border-radius: 9999px; font-weight: 700; font-size: 13px;'>
                {current_status}
            </span>
        </div>
        """)
    with col_tb3:
        safe_markdown_html("""
        <div style='text-align: right;'>
            <button onclick="window.parent.print ? window.parent.print() : window.print()" class="official-print-btn">
                🖨️ Print Form
            </button>
        </div>
        """)
    safe_markdown_html("</div>")

    # 4. Status Notifications
    if current_status == "REJECTED":
        rejection_reason = form_state.get("Rejection Reason", "")
        safe_markdown_html(f"""
        <div style='background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; color: #f87171;' class='no-print'>
            <div style='font-weight: 800; font-size: 15px; margin-bottom: 4px;'>❌ Feedback Revision Required</div>
            <div style='font-size: 14px;'><b>Reason for Rejection:</b> {html.escape(rejection_reason) or 'No specific reason provided'}</div>
            <div style='font-size: 12px; margin-top: 6px; color: #fca5a5;'>Please edit the feedback details below and re-submit for IQAC approval.</div>
        </div>
        """)
    elif current_status == "APPROVED":
        appr_time = form_state.get("Approved At", "")
        safe_markdown_html(f"""
        <div style='background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; color: #34d399;' class='no-print'>
            <div style='font-weight: 800; font-size: 15px; margin-bottom: 4px;'>✅ Feedback Approved by IQAC</div>
            <div style='font-size: 13.5px;'>This training feedback was reviewed and approved on <b>{appr_time or 'N/A'}</b>. Recorded in institutional appraisal dataset.</div>
        </div>
        """)
    elif current_status == "SUBMITTED":
        safe_markdown_html("""
        <div style='background: rgba(59, 130, 246, 0.15); border: 1px solid #3b82f6; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; color: #60a5fa;' class='no-print'>
            <div style='font-weight: 800; font-size: 15px; margin-bottom: 4px;'>⏳ Feedback Submitted for Approval</div>
            <div style='font-size: 13.5px;'>This feedback has been submitted by the faculty and is currently pending IQAC review and HOD evaluation.</div>
        </div>
        """)

    logo_b64 = _get_logo_base64()
    logo_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height: 48px; display: block; margin: 0 auto 8px auto;" alt="MSRIT Logo">' if logo_b64 else '<h2 style="margin:0 auto 8px auto; text-align:center; font-family:serif; font-weight:800; color:#000;">RAMAIAH</h2>'

    # ==================== A4 OFFICIAL DOCUMENT VIEW ====================
    if is_preview:
        # PURE READ-ONLY DOCUMENT REPRESENTATION DIRECTLY FROM FORM_STATE
        disp_emp = html.escape(str(form_state.get("Faculty Name", "") or ""))
        disp_date = html.escape(str(form_state.get("Training Date", "") or ""))
        disp_dept = html.escape(str(form_state.get("Department", "") or ""))
        disp_prog = html.escape(str(form_state.get("Training Program", "") or ""))
        disp_pres = html.escape(str(form_state.get("Presentation Rating", "Good") or "Good"))
        disp_und = html.escape(str(form_state.get("Understanding Level", "Good") or "Good"))
        disp_future = html.escape(str(form_state.get("Future Programs", "Yes") or "Yes"))

        cov_raw = str(form_state.get("Coverage of Topics", "") or "")
        und_reason_raw = str(form_state.get("Understanding Reason", "") or "")
        rec_topics_raw = str(form_state.get("Recommended Topics", "") or "")

        cov_box_content = html.escape(cov_raw) if cov_raw.strip() else "&nbsp;"
        und_box_content = html.escape(und_reason_raw) if und_reason_raw.strip() else "&nbsp;"
        rec_note = "N/A" if disp_future == "No" and not rec_topics_raw.strip() else "&nbsp;"
        rec_box_content = html.escape(rec_topics_raw) if rec_topics_raw.strip() else rec_note

        approved_at_str = str(form_state.get("Approved At", "") or "")
        fac_sig_status = 'Verified Faculty Submission' if current_status in ['SUBMITTED', 'APPROVED'] else 'Pending Faculty Signature'
        hod_sig_status = f"Approved on {approved_at_str}" if current_status == 'APPROVED' else 'Pending HOD Signature'

        safe_markdown_html(f"""
        <div class="official-form-container">
            <div style="text-align: right; font-weight: 700; font-size: 13.5px; margin-bottom: 10px; letter-spacing: 0.5px;">
                MSRIT/IQAC/2026/FBT
            </div>
            
            <div style="text-align: center; margin-bottom: 22px;">
                {logo_tag}
                <div style="font-size: 17px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;">
                    MS RAMAIAH INSTITUTE OF TECHNOLOGY, BANGALORE – 54
                </div>
                <div style="font-size: 13px; font-style: italic; margin-top: 2px;">
                    (Autonomous institute Affiliated to VTU)
                </div>
                <div style="margin-top: 14px; font-size: 16px; font-weight: 800; text-decoration: underline; letter-spacing: 0.5px;">
                    FEEDBACK ON TRAINING
                </div>
            </div>

            <div style="margin-top: 22px; font-size: 14.5px; line-height: 2;">
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                    <div><b>Name of the Employee:</b> <span style="border-bottom: 1px dotted #333; padding-bottom: 1px;">{disp_emp}</span></div>
                    <div><b>Date of Training:</b> <span style="border-bottom: 1px dotted #333; padding-bottom: 1px;">{disp_date}</span></div>
                </div>
                <div style="margin-top: 8px;">
                    <b>Department:</b> <span style="border-bottom: 1px dotted #333; padding-bottom: 1px;">{disp_dept or "N/A"}</span>
                </div>
                <div style="margin-top: 8px;">
                    <b>Name of the Training Program:</b> <span style="border-bottom: 1px dotted #333; padding-bottom: 1px;">{disp_prog}</span>
                </div>
            </div>

            <div style="margin-top: 22px; font-size: 14.5px;">
                <div style="font-weight: 800; font-size: 15px; margin-bottom: 10px;">Feedback:</div>

                <div style="margin-bottom: 14px; line-height: 1.8;">
                    <b>a) Presentation by faculty :</b> &nbsp; <span style="text-decoration: underline; font-weight: 600;">{disp_pres}</span> &nbsp; <span style="font-size: 12px; color: #64748b;">(Excellent / Good / Average / Poor / Very Poor)</span>
                </div>

                <div style="margin-bottom: 14px; line-height: 1.8;">
                    <b>b) Coverage of topics :</b>
                    <div style="padding: 10px 14px; background: #fafafa; border: 1px solid #cbd5e1; border-radius: 4px; min-height: 44px; white-space: pre-wrap; word-break: break-word; font-family: 'Times New Roman', serif; font-size: 14.5px; margin-top: 4px;">{cov_box_content}</div>
                </div>

                <div style="margin-bottom: 14px; line-height: 1.8;">
                    <b>c) Your level of understanding :</b> &nbsp; <span style="text-decoration: underline; font-weight: 600;">{disp_und}</span> &nbsp; <span style="font-size: 12px; color: #64748b;">(Good / Average / Poor)</span><br>
                    <span style="font-size: 13px; font-style: italic;">(Specify briefly reasons)</span>
                    <div style="padding: 10px 14px; background: #fafafa; border: 1px solid #cbd5e1; border-radius: 4px; min-height: 44px; white-space: pre-wrap; word-break: break-word; font-family: 'Times New Roman', serif; font-size: 14.5px; margin-top: 4px;">{und_box_content}</div>
                </div>

                <div style="margin-bottom: 14px; line-height: 1.8;">
                    <div style="display: flex; justify-content: space-between;">
                        <div><b>d) Do you want such programs in future :</b></div>
                        <div><span style="text-decoration: underline; font-weight: 600;">{disp_future}</span></div>
                    </div>
                    <div style="font-size: 13px; font-style: italic; margin-top: 2px;">If yes, what topics would you recommend?</div>
                    <div style="padding: 10px 14px; background: #fafafa; border: 1px solid #cbd5e1; border-radius: 4px; min-height: 40px; white-space: pre-wrap; word-break: break-word; font-family: 'Times New Roman', serif; font-size: 14.5px; margin-top: 4px;">{rec_box_content}</div>
                </div>
            </div>

            <hr style="border: 0; border-top: 2px solid #000; margin: 24px 0 2px 0;">
            <hr style="border: 0; border-top: 1px solid #000; margin: 0 0 16px 0;">

            <div style="font-size: 14.5px;">
                <div style="font-weight: 800; margin-bottom: 2px;">
                    HOD’s evaluation of the effectiveness of training
                </div>
                <div style="font-size: 12.5px; font-style: italic; margin-bottom: 12px; color: #475569;">
                    (to be filled in about three months after the training)
                </div>

                <div style="margin-bottom: 8px; line-height: 1.8;">
                    <b>a) Understanding:</b> &nbsp; Good / Average / Poor
                </div>

                <div style="margin-bottom: 10px; line-height: 1.8;">
                    <b>b) Application at Job:</b> &nbsp; Applies well / No evidence of application / Exhibits Lack of understanding / Indifferent though knowledgeable
                </div>

                <div style="margin-bottom: 12px; line-height: 1.8;">
                    <b>c) General Remarks:</b>
                    <div class="hod-locked-box">
                        Pending HOD Evaluation — to be completed approximately three months after training.
                    </div>
                </div>
            </div>

            <hr style="border: 0; border-top: 1px solid #000; margin: 22px 0 30px 0;">

            <div style="display: flex; justify-content: space-between; font-size: 14px; font-weight: 700; padding: 0 10px;">
                <div>
                    <div>Signature of the Faculty</div>
                    <div style="font-size: 12px; font-weight: normal; color: #64748b; margin-top: 6px;">
                        Status: {fac_sig_status}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div>Signature of the HOD</div>
                    <div style="font-size: 12px; font-weight: normal; color: #64748b; margin-top: 6px;">
                        Status: {hod_sig_status}
                    </div>
                </div>
            </div>
        </div>
        """)

    else:
        # ==================== EDIT MODE (INTERACTIVE FORM) ====================
        safe_markdown_html(f"""
        <div class="official-form-container">
            <div style="text-align: right; font-weight: 700; font-size: 13.5px; margin-bottom: 10px; letter-spacing: 0.5px;">
                MSRIT/IQAC/2026/FBT
            </div>
            
            <div style="text-align: center; margin-bottom: 22px;">
                {logo_tag}
                <div style="font-size: 17px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;">
                    MS RAMAIAH INSTITUTE OF TECHNOLOGY, BANGALORE – 54
                </div>
                <div style="font-size: 13px; font-style: italic; margin-top: 2px;">
                    (Autonomous institute Affiliated to VTU)
                </div>
                <div style="margin-top: 14px; font-size: 16px; font-weight: 800; text-decoration: underline; letter-spacing: 0.5px;">
                    FEEDBACK ON TRAINING
                </div>
            </div>
        </div>
        """)

        # Interactive form fields container
        with st.container():
            c_emp, c_date = st.columns(2)
            with c_emp:
                st.text_input(
                    "Name of the Employee",
                    value=form_state.get("Faculty Name", ""),
                    key=k_emp,
                    help="Auto-filled from certificate, editable"
                )
            with c_date:
                st.text_input(
                    "Date of Training",
                    value=form_state.get("Training Date", ""),
                    key=k_date,
                    help="Auto-filled from certificate, editable"
                )

            st.text_input(
                "Department",
                value=form_state.get("Department", ""),
                key=k_dept,
                placeholder="Enter department name...",
                help="Auto-filled from faculty master if available, editable"
            )
            if not form_state.get("Department", "").strip():
                st.caption("⚠️ *Department was not available in the faculty master data. Please verify.*")

            st.text_input(
                "Name of the Training Program",
                value=form_state.get("Training Program", ""),
                key=k_prog,
                help="Auto-filled from certificate, editable"
            )

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.markdown("#### **Feedback:**")

            # a) Presentation by faculty
            pres_options = ["Excellent", "Good", "Average", "Poor", "Very Poor"]
            curr_pres = form_state.get("Presentation Rating", "Good")
            pres_idx = pres_options.index(curr_pres) if curr_pres in pres_options else 1
            st.radio(
                "a) Presentation by faculty",
                pres_options,
                index=pres_idx,
                horizontal=True,
                key=k_pres
            )

            # b) Coverage of topics
            st.text_area(
                "b) Coverage of topics",
                value=form_state.get("Coverage of Topics", ""),
                key=k_cov,
                placeholder="Describe the coverage of topics in detail..."
            )

            # c) Level of understanding
            und_options = ["Good", "Average", "Poor"]
            curr_und = form_state.get("Understanding Level", "Good")
            und_idx = und_options.index(curr_und) if curr_und in und_options else 0
            st.radio(
                "c) Your level of understanding",
                und_options,
                index=und_idx,
                horizontal=True,
                key=k_und
            )
            st.text_area(
                "(Specify briefly reasons)",
                value=form_state.get("Understanding Reason", ""),
                key=k_und_reason,
                placeholder="Specify reasons for your understanding rating..."
            )

            # d) Future programs
            fut_options = ["Yes", "No"]
            curr_fut = form_state.get("Future Programs", "Yes")
            fut_idx = fut_options.index(curr_fut) if curr_fut in fut_options else 0
            st.radio(
                "d) Do you want such programs in future",
                fut_options,
                index=fut_idx,
                horizontal=True,
                key=k_future
            )
            st.text_area(
                "If yes, what topics would you recommend?",
                value=form_state.get("Recommended Topics", ""),
                key=k_rec_topics,
                placeholder="Enter topics you recommend for future programs..."
            )

            safe_markdown_html("""
            <hr style="border: 0; border-top: 2px solid #000; margin: 24px 0 2px 0;">
            <hr style="border: 0; border-top: 1px solid #000; margin: 0 0 16px 0;">
            <div style="font-family: 'Times New Roman', serif;">
                <div style="font-weight: 800; font-size: 15px; margin-bottom: 2px;">
                    HOD’s evaluation of the effectiveness of training
                </div>
                <div style="font-size: 12.5px; font-style: italic; margin-bottom: 12px; color: #94a3b8;">
                    (to be filled in about three months after the training)
                </div>
                <div style="font-size: 14px; margin-bottom: 8px;"><b>a) Understanding:</b> Good / Average / Poor</div>
                <div style="font-size: 14px; margin-bottom: 8px;"><b>b) Application at Job:</b> Applies well / No evidence of application / Exhibits Lack of understanding / Indifferent though knowledgeable</div>
                <div class="hod-locked-box">
                    Pending HOD Evaluation — to be completed approximately three months after training.
                </div>
            </div>
            <hr style="border: 0; border-top: 1px solid #000; margin: 20px 0 28px 0;">
            <div style="display: flex; justify-content: space-between; font-family: 'Times New Roman', serif; font-size: 14px; font-weight: 700; margin-bottom: 20px;">
                <div>Signature of the Faculty<br><span style="font-size: 12px; font-weight: normal; color: #94a3b8;">Faculty Signature: Pending</span></div>
                <div style="text-align: right;">Signature of the HOD<br><span style="font-size: 12px; font-weight: normal; color: #94a3b8;">HOD Signature: Pending</span></div>
            </div>
            """)

    # ==================== SECTION 15: ACTION CONTROLS BAR (BELOW A4 DOC) ====================
    # PDF generation directly from the central form state
    try:
        pdf_bytes = generate_training_feedback_pdf(form_state)
    except Exception as e:
        pdf_bytes = b""

    clean_name = sanitize_filename(form_state.get("Faculty Name") or "Faculty")
    clean_date = sanitize_filename(form_state.get("Training Date") or "Training")
    pdf_filename = f"Feedback_{clean_name}_{clean_date}.pdf"

    st.markdown("<div class='official-controls-bar no-print'>", unsafe_allow_html=True)

    # 1. NOT_STARTED / DRAFT / IN_PROGRESS CONTROLS
    if current_status in ["NOT_STARTED", "IN_PROGRESS", "DRAFT"]:
        c1, c2, c3, c4 = st.columns([1, 1, 1.2, 1])
        with c1:
            if st.button("💾 Save Draft", key=f"btn_save_draft_{certificate_id}", use_container_width=True):
                payload = dict(form_state)
                payload["Feedback Status"] = "IN_PROGRESS"
                saved = pipeline.history_manager.create_training_feedback(payload)
                form_state["Feedback Status"] = "IN_PROGRESS"
                form_state["Feedback ID"] = saved.get("Feedback ID", "")
                _sync_to_sheet(saved, "Save Draft")
                st.success("✅ Feedback draft saved successfully.")
                st.rerun()

        with c2:
            toggle_label = "✏️ Edit Mode" if is_preview else "👁️ Preview Document"
            if st.button(toggle_label, key=f"btn_toggle_mode_{certificate_id}", use_container_width=True):
                if not is_preview:
                    payload = dict(form_state)
                    if payload.get("Feedback Status", "NOT_STARTED") in ["NOT_STARTED", "DRAFT"]:
                        payload["Feedback Status"] = "IN_PROGRESS"
                    saved = pipeline.history_manager.create_training_feedback(payload)
                    form_state["Feedback ID"] = saved.get("Feedback ID", "")
                    st.session_state[preview_key] = True
                else:
                    st.session_state[preview_key] = False
                    st.session_state[k_emp] = form_state["Faculty Name"]
                    st.session_state[k_date] = form_state["Training Date"]
                    st.session_state[k_dept] = form_state["Department"]
                    st.session_state[k_prog] = form_state["Training Program"]
                    st.session_state[k_pres] = form_state["Presentation Rating"]
                    st.session_state[k_cov] = form_state["Coverage of Topics"]
                    st.session_state[k_und] = form_state["Understanding Level"]
                    st.session_state[k_und_reason] = form_state["Understanding Reason"]
                    st.session_state[k_future] = form_state["Future Programs"]
                    st.session_state[k_rec_topics] = form_state["Recommended Topics"]
                st.rerun()

        with c3:
            if st.button("🚀 Submit Feedback", key=f"btn_submit_fb_{certificate_id}", type="primary", use_container_width=True):
                if not form_state.get("Department", "").strip():
                    st.error("Please enter the Department before submitting.")
                elif not form_state.get("Coverage of Topics", "").strip():
                    st.error("Please provide remarks on Coverage of topics before submitting.")
                elif not form_state.get("Understanding Reason", "").strip():
                    st.error("Please specify reasons for your understanding rating.")
                elif form_state.get("Future Programs") == "Yes" and not form_state.get("Recommended Topics", "").strip():
                    st.error("Please enter recommended topics when selecting Yes for future programs.")
                else:
                    payload = dict(form_state)
                    payload["Feedback Status"] = "SUBMITTED"
                    saved = pipeline.history_manager.create_training_feedback(payload)
                    form_state["Feedback Status"] = "SUBMITTED"
                    form_state["Feedback ID"] = saved.get("Feedback ID", "")
                    _sync_to_sheet(saved, "Submit")
                    st.session_state[preview_key] = True
                    st.success("✅ Feedback submitted successfully! The submission is now pending IQAC review.")
                    st.rerun()

        with c4:
            if pdf_bytes:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key=f"btn_dl_pdf_{certificate_id}",
                    use_container_width=True
                )

    # 2. SUBMITTED CONTROLS (Under IQAC Review)
    elif current_status == "SUBMITTED":
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            toggle_label = "✏️ Edit Details" if is_preview else "👁️ View Official Form"
            if st.button(toggle_label, key=f"btn_toggle_sub_{certificate_id}", use_container_width=True):
                st.session_state[preview_key] = not is_preview
                if not st.session_state[preview_key]:
                    st.session_state[k_emp] = form_state["Faculty Name"]
                    st.session_state[k_date] = form_state["Training Date"]
                    st.session_state[k_dept] = form_state["Department"]
                    st.session_state[k_prog] = form_state["Training Program"]
                    st.session_state[k_pres] = form_state["Presentation Rating"]
                    st.session_state[k_cov] = form_state["Coverage of Topics"]
                    st.session_state[k_und] = form_state["Understanding Level"]
                    st.session_state[k_und_reason] = form_state["Understanding Reason"]
                    st.session_state[k_future] = form_state["Future Programs"]
                    st.session_state[k_rec_topics] = form_state["Recommended Topics"]
                st.rerun()

        with c2:
            if st.button("✅ Approve Feedback", key=f"btn_appr_{certificate_id}", type="primary", use_container_width=True):
                try:
                    payload = dict(form_state)
                    payload["Feedback Status"] = "APPROVED"
                    saved = pipeline.history_manager.create_training_feedback(payload)
                    approved = pipeline.history_manager.approve_training_feedback(saved["Feedback ID"])
                    form_state["Feedback Status"] = "APPROVED"
                    form_state["Approved At"] = approved.get("Approved At", "")
                    # Sync approved record (includes Approved At timestamp)
                    approved_payload = dict(saved)
                    approved_payload["Feedback Status"] = "APPROVED"
                    approved_payload["Approved At"] = approved.get("Approved At", "")
                    _sync_to_sheet(approved_payload, "Approve")
                    st.session_state[preview_key] = True
                    st.success("✅ Feedback approved and added to results/approved_feedback.csv.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error approving feedback: {e}")

        with c3:
            if st.button("❌ Reject Feedback", key=f"btn_rej_{certificate_id}", use_container_width=True):
                st.session_state[f"show_reject_input_{certificate_id}"] = True

        with c4:
            if pdf_bytes:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key=f"btn_dl_pdf_sub_{certificate_id}",
                    use_container_width=True
                )

        if st.session_state.get(f"show_reject_input_{certificate_id}"):
            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            rej_reason_in = st.text_area(
                "Reason for rejecting this feedback (required):",
                key=f"rej_reason_input_{certificate_id}",
                placeholder="Please state clear reasons for revision (e.g. insufficient coverage remarks)..."
            )
            col_cr1, col_cr2 = st.columns([1, 1])
            with col_cr1:
                if st.button("Confirm Rejection", key=f"confirm_rej_{certificate_id}", type="primary", use_container_width=True):
                    if not rej_reason_in.strip():
                        st.warning("Please provide a rejection reason.")
                    else:
                        try:
                            payload = dict(form_state)
                            payload["Feedback Status"] = "REJECTED"
                            payload["Rejection Reason"] = rej_reason_in.strip()
                            saved = pipeline.history_manager.create_training_feedback(payload)
                            rejected = pipeline.history_manager.reject_training_feedback(saved["Feedback ID"], rej_reason_in.strip())
                            form_state["Feedback Status"] = "REJECTED"
                            form_state["Rejection Reason"] = rej_reason_in.strip()
                            # Sync rejection (includes reason)
                            rejected_payload = dict(saved)
                            rejected_payload["Feedback Status"] = "REJECTED"
                            rejected_payload["Rejection Reason"] = rej_reason_in.strip()
                            _sync_to_sheet(rejected_payload, "Reject")
                            st.session_state.pop(f"show_reject_input_{certificate_id}", None)
                            st.warning("Feedback rejected and stored in results/rejected_feedback.csv.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error rejecting feedback: {e}")
            with col_cr2:
                if st.button("Cancel", key=f"cancel_rej_{certificate_id}", use_container_width=True):
                    st.session_state.pop(f"show_reject_input_{certificate_id}", None)
                    st.rerun()

    # 3. APPROVED CONTROLS
    elif current_status == "APPROVED":
        c1, c2, c3 = st.columns([1.5, 1, 1])
        with c1:
            if pdf_bytes:
                st.download_button(
                    label="📥 Download Approved PDF",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key=f"btn_dl_pdf_appr_{certificate_id}",
                    use_container_width=True
                )
        with c2:
            if st.button("✏️ Reopen for Editing", key=f"btn_reopen_{certificate_id}", use_container_width=True):
                st.session_state[preview_key] = False
                form_state["Feedback Status"] = "IN_PROGRESS"
                updated = pipeline.history_manager.update_training_feedback(form_state.get("Feedback ID", ""), {"Feedback Status": "IN_PROGRESS"})
                reopen_payload = dict(form_state)
                reopen_payload["Feedback Status"] = "IN_PROGRESS"
                _sync_to_sheet(reopen_payload, "Reopen")
                st.session_state[k_emp] = form_state["Faculty Name"]
                st.session_state[k_date] = form_state["Training Date"]
                st.session_state[k_dept] = form_state["Department"]
                st.session_state[k_prog] = form_state["Training Program"]
                st.session_state[k_pres] = form_state["Presentation Rating"]
                st.session_state[k_cov] = form_state["Coverage of Topics"]
                st.session_state[k_und] = form_state["Understanding Level"]
                st.session_state[k_und_reason] = form_state["Understanding Reason"]
                st.session_state[k_future] = form_state["Future Programs"]
                st.session_state[k_rec_topics] = form_state["Recommended Topics"]
                st.rerun()
        with c3:
            safe_markdown_html("""
            <button onclick="window.parent.print ? window.parent.print() : window.print()" class="official-print-btn" style="width:100%; justify-content:center;">
                🖨️ Print Form
            </button>
            """)

    # 4. REJECTED CONTROLS
    elif current_status == "REJECTED":
        c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
        with c1:
            if st.button("✏️ Edit & Resubmit", key=f"btn_edit_resubmit_{certificate_id}", type="primary", use_container_width=True):
                st.session_state[preview_key] = False
                st.session_state[k_emp] = form_state["Faculty Name"]
                st.session_state[k_date] = form_state["Training Date"]
                st.session_state[k_dept] = form_state["Department"]
                st.session_state[k_prog] = form_state["Training Program"]
                st.session_state[k_pres] = form_state["Presentation Rating"]
                st.session_state[k_cov] = form_state["Coverage of Topics"]
                st.session_state[k_und] = form_state["Understanding Level"]
                st.session_state[k_und_reason] = form_state["Understanding Reason"]
                st.session_state[k_future] = form_state["Future Programs"]
                st.session_state[k_rec_topics] = form_state["Recommended Topics"]
                st.rerun()

        with c2:
            if st.button("💾 Save Draft", key=f"btn_save_draft_rej_{certificate_id}", use_container_width=True):
                payload = dict(form_state)
                payload["Feedback Status"] = "IN_PROGRESS"
                saved = pipeline.history_manager.create_training_feedback(payload)
                form_state["Feedback Status"] = "IN_PROGRESS"
                _sync_to_sheet(saved, "Save Draft (after rejection)")
                st.success("✅ Changes saved as draft.")
                st.rerun()

        with c3:
            if pdf_bytes:
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    key=f"btn_dl_pdf_rej_{certificate_id}",
                    use_container_width=True
                )

        with c4:
            safe_markdown_html("""
            <button onclick="window.parent.print ? window.parent.print() : window.print()" class="official-print-btn" style="width:100%; justify-content:center;">
                🖨️ Print Form
            </button>
            """)

    st.markdown("</div>", unsafe_allow_html=True)


def render_training_feedback_dashboard():
    """
    Renders the dedicated MSRIT Training Feedback Dashboard:
    - Summary Cards (Total Valid, Pending, Approved, Rejected, Completion Rate)
    - Search & Filter bar to select verified training certificates
    - Interactive Official MSRIT Form
    - Pending, Approved, and Rejected tables with quick action buttons
    """
    safe_markdown_html("""
    <div class='header-banner no-print'>
        <h1 style='margin:0; font-size:26px; font-weight:800;'>📝 Training Feedback</h1>
        <p style='margin:4px 0 0 0; color:#94a3b8; font-size:14px;'>
            Review, complete and manage feedback for verified training programs.
        </p>
    </div>
    """)

    # 1. Live Summary Cards from existing dataset
    stats = pipeline.history_manager.get_training_feedback_stats()
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        safe_markdown_html(f"""
        <div class='stat-card'>
            <div class='stat-label'>Total Valid</div>
            <div class='stat-num' style='color:#38bdf8;'>{stats['total_valid']}</div>
            <div style='font-size:12px; color:#94a3b8;'>Verified certificates</div>
        </div>
        """)
    with c2:
        safe_markdown_html(f"""
        <div class='stat-card'>
            <div class='stat-label'>Feedback Pending</div>
            <div class='stat-num' style='color:#f59e0b;'>{stats['pending']}</div>
            <div style='font-size:12px; color:#94a3b8;'>Awaiting approval</div>
        </div>
        """)
    with c3:
        safe_markdown_html(f"""
        <div class='stat-card'>
            <div class='stat-label'>Approved</div>
            <div class='stat-num' style='color:#10b981;'>{stats['approved']}</div>
            <div style='font-size:12px; color:#94a3b8;'>Appraisal ready</div>
        </div>
        """)
    with c4:
        safe_markdown_html(f"""
        <div class='stat-card'>
            <div class='stat-label'>Rejected</div>
            <div class='stat-num' style='color:#ef4444;'>{stats['rejected']}</div>
            <div style='font-size:12px; color:#94a3b8;'>Needs revision</div>
        </div>
        """)
    with c5:
        safe_markdown_html(f"""
        <div class='stat-card'>
            <div class='stat-label'>Completion Rate</div>
            <div class='stat-num' style='color:#a855f7;'>{stats['completion_rate']:.1f}%</div>
            <div style='font-size:12px; color:#94a3b8;'>Approved / Valid</div>
        </div>
        """)

    st.markdown("<div style='height: 16px;' class='no-print'></div>", unsafe_allow_html=True)

    # 2. Retrieve Datasets
    unique_records = pipeline.history_manager.get_unique_records()
    valid_records = [r for r in unique_records if r.get("Final Result", "").upper() == "VALID"]
    all_feedback = pipeline.history_manager.get_all_training_feedback()
    fb_by_cert = {r.get("Certificate ID", "").strip(): r for r in all_feedback if r.get("Certificate ID")}

    # 3. Check if a certificate is actively selected
    selected_cert_id = st.session_state.get("selected_training_cert_id")

    # 4. Search & Filter: Select Verified Training (Section 8)
    st.markdown("### 🎯 Select Verified Training", help="Search and select any valid training to open its official feedback form")
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        faculty_list = ["All Faculty"] + sorted(list(set(r.get("Faculty Name", "") for r in valid_records if r.get("Faculty Name"))))
        selected_fac = st.selectbox("Filter by Faculty", faculty_list, key="tf_filter_fac")
    with col_f2:
        search_query = st.text_input("Search (Faculty Name, ID, FDP Title, Certificate ID, Date)", "", key="tf_search_q")

    # Filter records
    filtered_valid = valid_records
    if selected_fac != "All Faculty":
        filtered_valid = [r for r in filtered_valid if r.get("Faculty Name") == selected_fac]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_valid = [r for r in filtered_valid if any(q in str(v).lower() for v in r.values())]

    # Selectbox dropdown
    if filtered_valid:
        cert_options = ["-- Select a verified training certificate --"] + [
            f"{r.get('Certificate ID')} | {r.get('Faculty Name')} | {r.get('FDP Name', '')[:35]} ({r.get('Start Date', '')})"
            for r in filtered_valid
        ]
        chosen_opt = st.selectbox("Select Certificate to Complete/View Feedback:", cert_options, key="tf_select_cert_dropdown")
        if chosen_opt != "-- Select a verified training certificate --":
            chosen_cid = chosen_opt.split(" | ")[0].strip()
            if chosen_cid != selected_cert_id:
                # Clear active cache for clean load from storage
                st.session_state.pop(f"tf_active_state_{chosen_cid}", None)
                st.session_state["selected_training_cert_id"] = chosen_cid
                st.rerun()

    # If a certificate is currently selected, render its official form!
    if selected_cert_id:
        target_cert = next((r for r in valid_records if r.get("Certificate ID", "").strip() == selected_cert_id.strip()), None)
        if not target_cert:
            # Check if an invalid certificate was requested
            all_records = pipeline.history_manager.get_all_records()
            invalid_cert = next((r for r in all_records if r.get("Certificate ID", "").strip() == selected_cert_id.strip()), None)
            if invalid_cert and invalid_cert.get("Final Result", "").upper() != "VALID":
                st.error("Training feedback is available only for certificates verified as VALID.")
                if st.button("⬅️ Clear Selection", key="clear_invalid_sel"):
                    st.session_state.pop("selected_training_cert_id", None)
                    st.rerun()
                return
            st.error(f"Certificate {selected_cert_id} could not be loaded from valid records.")
            if st.button("⬅️ Back to All Records", key="back_missing_sel"):
                st.session_state.pop("selected_training_cert_id", None)
                st.rerun()
            return

        render_training_feedback_form(
            verification_id=target_cert.get("Verification ID", ""),
            cert=target_cert,
            show_back_button=True
        )
        return

    # 5. Tables: Pending, Approved, and Rejected (Sections 4, 5, 6)
    st.markdown("---")

    # Compile Pending list (Valid certs without APPROVED feedback)
    pending_list = []
    for r in valid_records:
        cid = r.get("Certificate ID", "").strip()
        fb = fb_by_cert.get(cid)
        status = fb.get("Feedback Status", "NOT_STARTED").upper() if fb else "NOT_STARTED"
        if status != "APPROVED":
            dept = (fb.get("Department") if fb else "") or pipeline.data_loader.get_faculty_department(
                faculty_id=r.get("Faculty ID", ""),
                faculty_name=r.get("Faculty Name", "")
            )
            pending_list.append({
                "Faculty Name": r.get("Faculty Name", ""),
                "Faculty ID": r.get("Faculty ID", ""),
                "Department": dept or "Pending Entry",
                "Training Program": r.get("FDP Name", ""),
                "Training Date": r.get("Start Date", ""),
                "Program Type": r.get("Internal/External", ""),
                "Certificate ID": cid,
                "Feedback Status": status
            })

    # Compile Approved list
    approved_list = []
    approved_rows = [r for r in all_feedback if r.get("Feedback Status", "").upper() == "APPROVED"]
    for fb in approved_rows:
        approved_list.append({
            "Faculty Name": fb.get("Faculty Name", ""),
            "Faculty ID": fb.get("Faculty ID", ""),
            "Department": fb.get("Department", ""),
            "Training Program": fb.get("Training Program", ""),
            "Training Date": fb.get("Training Date", ""),
            "Program Type": fb.get("Program Type", ""),
            "Feedback Status": "APPROVED",
            "Approved At": fb.get("Approved At", ""),
            "Certificate ID": fb.get("Certificate ID", "")
        })

    # Compile Rejected list
    rejected_list = []
    rejected_rows = [r for r in all_feedback if r.get("Feedback Status", "").upper() == "REJECTED"]
    for fb in rejected_rows:
        rejected_list.append({
            "Faculty Name": fb.get("Faculty Name", ""),
            "Faculty ID": fb.get("Faculty ID", ""),
            "Training Program": fb.get("Training Program", ""),
            "Training Date": fb.get("Training Date", ""),
            "Rejection Reason": fb.get("Rejection Reason", ""),
            "Feedback Status": "REJECTED",
            "Certificate ID": fb.get("Certificate ID", "")
        })

    tab_p, tab_a, tab_r = st.tabs([
        f"⏳ Pending Training Feedback ({len(pending_list)})",
        f"✅ Approved Feedback ({len(approved_list)})",
        f"❌ Rejected Feedback ({len(rejected_list)})"
    ])

    with tab_p:
        st.subheader("⏳ Pending Training Feedback")
        st.caption("Valid certificates awaiting faculty completion or administrative approval.")
        if not pending_list:
            st.info("No pending feedback records. All valid certificates have approved feedback.")
        else:
            df_pending = pd.DataFrame(pending_list)
            st.dataframe(df_pending, use_container_width=True, hide_index=True)

            col_p1, col_p2 = st.columns([3, 1])
            with col_p1:
                p_opts = [f"{r['Certificate ID']} — {r['Faculty Name']} ({r['Training Program'][:30]})" for r in pending_list]
                sel_p = st.selectbox("Select Pending Certificate to Open:", p_opts, key="sel_pending_tbl")
            with col_p2:
                st.write("")
                st.write("")
                if st.button("📝 Open Feedback", key="btn_open_pending_action", type="primary"):
                    cid_chosen = sel_p.split(" — ")[0].strip()
                    st.session_state["selected_training_cert_id"] = cid_chosen
                    st.session_state[f"preview_mode_{cid_chosen}"] = False
                    st.session_state.pop(f"tf_active_state_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_emp_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_date_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_dept_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_prog_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_pres_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_cov_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_und_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_und_reason_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_future_{cid_chosen}", None)
                    st.session_state.pop(f"tf_in_rec_topics_{cid_chosen}", None)
                    st.rerun()

    with tab_a:
        st.subheader("✅ Approved Feedback")
        st.caption("Verified and approved training feedback records ready for MSRIT appraisal automation.")
        if not approved_list:
            st.info("No feedback records available.")
        else:
            df_appr = pd.DataFrame(approved_list)
            st.dataframe(df_appr[["Faculty Name", "Faculty ID", "Department", "Training Program", "Training Date", "Program Type", "Feedback Status", "Approved At"]], use_container_width=True, hide_index=True)

            col_a1, col_a2 = st.columns([3, 1])
            with col_a1:
                a_opts = [f"{r['Certificate ID']} — {r['Faculty Name']} ({r['Training Program'][:30]})" for r in approved_list]
                sel_a = st.selectbox("Select Approved Certificate to View:", a_opts, key="sel_appr_tbl")
            with col_a2:
                st.write("")
                st.write("")
                if st.button("👁️ View", key="btn_view_appr_action", type="primary"):
                    cid_chosen = sel_a.split(" — ")[0].strip()
                    st.session_state["selected_training_cert_id"] = cid_chosen
                    st.session_state[f"preview_mode_{cid_chosen}"] = True
                    st.session_state.pop(f"tf_active_state_{cid_chosen}", None)
                    st.rerun()

    with tab_r:
        st.subheader("❌ Rejected Feedback")
        st.caption("Training feedback submissions that were rejected and require faculty revision.")
        if not rejected_list:
            st.info("No feedback records available.")
        else:
            df_rej = pd.DataFrame(rejected_list)
            st.dataframe(df_rej[["Faculty Name", "Faculty ID", "Training Program", "Training Date", "Rejection Reason", "Feedback Status"]], use_container_width=True, hide_index=True)

            col_r1, col_r2 = st.columns([3, 1])
            with col_r1:
                r_opts = [f"{r['Certificate ID']} — {r['Faculty Name']} ({r['Training Program'][:30]})" for r in rejected_list]
                sel_r = st.selectbox("Select Rejected Certificate to Review:", r_opts, key="sel_rej_tbl")
            with col_r2:
                st.write("")
                st.write("")
                if st.button("🔍 Review", key="btn_review_rej_action", type="primary"):
                    cid_chosen = sel_r.split(" — ")[0].strip()
                    st.session_state["selected_training_cert_id"] = cid_chosen
                    st.session_state[f"preview_mode_{cid_chosen}"] = False
                    st.session_state.pop(f"tf_active_state_{cid_chosen}", None)
                    st.rerun()


# PAGE 1: DASHBOARD
if page == "📊 Dashboard":
    st.markdown("""
    <div class='header-banner'>
        <h1 style='margin:0; font-size:26px; font-weight:800;'>📊 FDP Certificate Verification Dashboard</h1>
        <p style='margin:4px 0 0 0; color:#94a3b8; font-size:14px;'>
            Real-time analytics, automated attendance conflict tracking, and verification statistics for MSRIT faculty.
        </p>
    </div>
    """, unsafe_allow_html=True)

    stats = pipeline.history_manager.get_statistics()
    render_metrics_cards(stats)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📋 Verification & Conflict Breakdowns")
        breakdown_df = pd.DataFrame([
            {"Metric": "Internal FDPs (MSRIT/RIT)", "Count": stats["internal"], "Category": "Program Type"},
            {"Metric": "External FDPs", "Count": stats["external"], "Category": "Program Type"},
            {"Metric": "OOD Attendance Cases", "Count": stats["ood_cases"], "Category": "Attendance Evidence"},
            {"Metric": "Casual Leave Conflicts", "Count": stats["casual_leave_conflicts"], "Category": "Attendance Conflict"},
            {"Metric": "Emergency Leave Conflicts", "Count": stats["emergency_leave_conflicts"], "Category": "Attendance Conflict"},
            {"Metric": "Unpaid Leave Conflicts", "Count": stats["unpaid_leave_conflicts"], "Category": "Attendance Conflict"},
            {"Metric": "Missing Attendance Cases", "Count": stats["missing_attendance_cases"], "Category": "Missing Evidence"}
        ])
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("📈 Monthly Verification Distribution")
        month_data = stats.get("month_breakdown", {})
        if month_data:
            m_df = pd.DataFrame(list(month_data.items()), columns=["Month", "Certificates"]).sort_values("Month")
            st.bar_chart(m_df.set_index("Month"), color="#6366f1")
        else:
            st.info("No monthly data available yet.")

    st.markdown("---")

    # Faculty + Department Grouping in Dashboard
    st.subheader("👨‍🏫 Faculty Verification Summary (Grouped)")
    unique_records = pipeline.history_manager.get_unique_records()
    if unique_records:
        # Build groups by normalized faculty name + institution (as department proxy)
        groups = {}
        for r in unique_records:
            fname_display = _normalize_faculty_display(r.get("Faculty Name", "Unknown"))
            dept_display = _normalize_faculty_display(r.get("Institution", "Unknown"))
            # Grouping key: normalized (lowercase, trimmed) version
            group_key = (_normalize_group_key(r.get("Faculty Name", "")),
                         _normalize_group_key(r.get("Institution", "")))
            if group_key not in groups:
                groups[group_key] = {
                    "faculty_display": fname_display,
                    "dept_display": dept_display,
                    "certificates": []
                }
            groups[group_key]["certificates"].append(r)

        # Sort by faculty name
        sorted_groups = sorted(groups.values(), key=lambda g: g["faculty_display"].lower())

        for g in sorted_groups:
            cert_count = len(g["certificates"])
            st.markdown(f"""
            <div class='faculty-group-header'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <span style='font-size:16px; font-weight:700; color:#e2e8f0;'>👤 {g['faculty_display']}</span>
                        <span style='font-size:13px; color:#94a3b8; margin-left:12px;'>📍 {g['dept_display']}</span>
                    </div>
                    <div>
                        <span class='badge badge-internal'>{cert_count} certificate{'s' if cert_count != 1 else ''}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            certs_df = pd.DataFrame([{
                "Certificate ID": c.get("Certificate ID", ""),
                "FDP Name": c.get("FDP Name", ""),
                "Start Date": c.get("Start Date", ""),
                "End Date": c.get("End Date", ""),
                "Result": c.get("Final Result", ""),
                "Type": c.get("Internal/External", "")
            } for c in g["certificates"]])
            st.dataframe(certs_df, use_container_width=True, hide_index=True)
    else:
        st.info("No verification records available yet.")


# PAGE 2: VERIFY NEW CERTIFICATE
elif page == "🔍 Verify New Certificate":
    st.markdown("""
    <div class='header-banner'>
        <h1 style='margin:0; font-size:26px; font-weight:800;'>🔍 Verify New Certificate</h1>
        <p style='margin:4px 0 0 0; color:#94a3b8; font-size:14px;'>
            Upload an FDP certificate (PDF, JPG, JPEG, PNG). The system automatically runs OCR, identifies faculty, searches attendance for every single date, predicts via ML, and checks institutional rules.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tab_upload, tab_presets = st.tabs(["📤 Upload Certificate", "⚡ One-Click Demo Presets"])

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Choose Certificate File (PDF, JPG, JPEG, PNG)",
            type=["pdf", "jpg", "jpeg", "png"],
            help="Upload the digital certificate document for automated verification."
        )

        with st.expander("🛠️ Advanced / Optional Metadata Override (If document is scanned or noisy)"):
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                opt_fid = st.text_input("Faculty ID (e.g. F012)", placeholder="F012")
                opt_fname = st.text_input("Faculty Name (e.g. Dr. Sushma B)", placeholder="Dr. Sushma B")
                opt_inst = st.text_input("Program Institution", placeholder="Ramaiah Institute of Technology")
            with c_f2:
                opt_title = st.text_input("FDP / Program Name", placeholder="AI and Analytics Bootcamp")
                opt_start = st.text_input("Start Date (DD/MM/YYYY)", placeholder="07/07/2025")
                opt_end = st.text_input("End Date (DD/MM/YYYY)", placeholder="11/07/2025")

        if st.button("🚀 VERIFY CERTIFICATE", type="primary", use_container_width=True):
            if uploaded_file is None:
                st.error("Please upload a PDF, JPG, JPEG, or PNG certificate file.")
            else:
                with st.spinner("Processing certificate through automated OCR, Attendance, ML & Rule engines..."):
                    file_bytes = uploaded_file.read()
                    fallback_meta = {
                        "FACULTY ID": opt_fid,
                        "FACULTY NAME": opt_fname,
                        "PROGRAM INSTITUTION": opt_inst,
                        "FDP / PROGRAM NAME": opt_title,
                        "START DATE": opt_start,
                        "END DATE": opt_end
                    }
                    try:
                        res = pipeline.verify_uploaded_certificate(
                            file_bytes=file_bytes,
                            filename=uploaded_file.name,
                            fallback_meta=fallback_meta,
                            save_to_history=True
                        )
                        st.session_state["last_verification"] = res
                        if res.get("is_duplicate"):
                            st.warning("⚠️ Duplicate certificate detected! See details below.")
                        else:
                            st.success("Verification complete! Results generated below.")
                    except ValueError as ve:
                        st.error(str(ve))
                    except Exception as e:
                        st.error(f"Error during verification: {e}")

    with tab_presets:
        st.info("Select a preset scenario below to demonstrate the end-to-end automated pipeline in 1 click:")
        p_col1, p_col2 = st.columns(2)

        with p_col1:
            if st.button("🟢 Scenario 1: Valid External + OOD", use_container_width=True):
                mock_cert = {
                    "FACULTY ID": "F011", "FACULTY NAME": "Dr. Ganeshayya Shidaganti", "FACULTY_MATCHED": True,
                    "FDP / PROGRAM NAME": "Quantum Computing & AI Convergence",
                    "PROGRAM INSTITUTION": "BMS College of Engineering Bangalore", "PROGRAM TYPE": "EXTERNAL",
                    "START DATE": "09/02/2026", "END DATE": "13/02/2026", "NUMBER OF DAYS": "5"
                }
                # Check for duplicate before running pipeline
                dup = pipeline.history_manager.find_duplicate(mock_cert)
                if dup:
                    st.session_state["last_verification"] = {
                        "is_duplicate": True,
                        "cert_data": mock_cert,
                        "duplicate_of": dup,
                        "final_result": "DUPLICATE",
                        "final_reason": "This certificate already exists in the system. No new record was added and counts were not increased.",
                        "rule_output": {},
                        "ml_output": {"prediction": "N/A", "confidence": 0.0, "probabilities": {}},
                        "features": {}
                    }
                else:
                    res = pipeline._execute_core_pipeline(mock_cert, save_to_history=True)
                    st.session_state["last_verification"] = res
                st.rerun()

            if st.button("🔴 Scenario 2: External + Casual Leave Conflict", use_container_width=True):
                mock_cert = {
                    "FACULTY ID": "F015", "FACULTY NAME": "Dr. Mallegowda M.", "FACULTY_MATCHED": True,
                    "FDP / PROGRAM NAME": "Privacy Preserving AI",
                    "PROGRAM INSTITUTION": "IIT Hyderabad", "PROGRAM TYPE": "EXTERNAL",
                    "START DATE": "28/07/2025", "END DATE": "01/08/2025", "NUMBER OF DAYS": "5"
                }
                dup = pipeline.history_manager.find_duplicate(mock_cert)
                if dup:
                    st.session_state["last_verification"] = {
                        "is_duplicate": True,
                        "cert_data": mock_cert,
                        "duplicate_of": dup,
                        "final_result": "DUPLICATE",
                        "final_reason": "This certificate already exists in the system. No new record was added and counts were not increased.",
                        "rule_output": {},
                        "ml_output": {"prediction": "N/A", "confidence": 0.0, "probabilities": {}},
                        "features": {}
                    }
                else:
                    res = pipeline._execute_core_pipeline(mock_cert, save_to_history=True)
                    st.session_state["last_verification"] = res
                st.rerun()

            if st.button("🔴 Scenario 3: Critical Multi-Day Conflict (10-12/09/2026)", use_container_width=True):
                # Setup 10-11 OOD, 12 Casual Leave
                pipeline.data_loader.attendance_lookup[("F001", "10/09/2026")] = "OOD"
                pipeline.data_loader.attendance_lookup[("F001", "11/09/2026")] = "OOD"
                pipeline.data_loader.attendance_lookup[("F001", "12/09/2026")] = "Casual Leave"
                pipeline.data_loader.faculty_months_available["F001"].add("09/2026")

                mock_cert = {
                    "FACULTY ID": "F001", "FACULTY NAME": "Dr. S. Seema", "FACULTY_MATCHED": True,
                    "FDP / PROGRAM NAME": "AI/ML Faculty Development Program",
                    "PROGRAM INSTITUTION": "NIT Surathkal", "PROGRAM TYPE": "EXTERNAL",
                    "START DATE": "10/09/2026", "END DATE": "12/09/2026", "NUMBER OF DAYS": "3"
                }
                dup = pipeline.history_manager.find_duplicate(mock_cert)
                if dup:
                    st.session_state["last_verification"] = {
                        "is_duplicate": True,
                        "cert_data": mock_cert,
                        "duplicate_of": dup,
                        "final_result": "DUPLICATE",
                        "final_reason": "This certificate already exists in the system. No new record was added and counts were not increased.",
                        "rule_output": {},
                        "ml_output": {"prediction": "N/A", "confidence": 0.0, "probabilities": {}},
                        "features": {}
                    }
                else:
                    res = pipeline._execute_core_pipeline(mock_cert, save_to_history=True)
                    st.session_state["last_verification"] = res
                st.rerun()

        with p_col2:
            if st.button("🟡 Scenario 4: Critical Missing Month (Sept 2026)", use_container_width=True):
                mock_cert = {
                    "FACULTY ID": "F002", "FACULTY NAME": "Dr. Monica R. Mundada", "FACULTY_MATCHED": True,
                    "FDP / PROGRAM NAME": "Cloud Architectures & DevOps",
                    "PROGRAM INSTITUTION": "External University", "PROGRAM TYPE": "EXTERNAL",
                    "START DATE": "10/09/2026", "END DATE": "12/09/2026", "NUMBER OF DAYS": "3"
                }
                dup = pipeline.history_manager.find_duplicate(mock_cert)
                if dup:
                    st.session_state["last_verification"] = {
                        "is_duplicate": True,
                        "cert_data": mock_cert,
                        "duplicate_of": dup,
                        "final_result": "DUPLICATE",
                        "final_reason": "This certificate already exists in the system. No new record was added and counts were not increased.",
                        "rule_output": {},
                        "ml_output": {"prediction": "N/A", "confidence": 0.0, "probabilities": {}},
                        "features": {}
                    }
                else:
                    res = pipeline._execute_core_pipeline(mock_cert, save_to_history=True)
                    st.session_state["last_verification"] = res
                st.rerun()

            if st.button("🟡 Scenario 5: Single Date Missing in Month", use_container_width=True):
                pipeline.data_loader.attendance_lookup[("F005", "10/09/2026")] = "OOD"
                pipeline.data_loader.attendance_lookup[("F005", "11/09/2026")] = "OOD"
                pipeline.data_loader.faculty_months_available["F005"].add("09/2026")
                if ("F005", "12/09/2026") in pipeline.data_loader.attendance_lookup:
                    del pipeline.data_loader.attendance_lookup[("F005", "12/09/2026")]

                mock_cert = {
                    "FACULTY ID": "F005", "FACULTY NAME": "Nagabhushan A. M", "FACULTY_MATCHED": True,
                    "FDP / PROGRAM NAME": "Edge AI Systems",
                    "PROGRAM INSTITUTION": "External Tech Institute", "PROGRAM TYPE": "EXTERNAL",
                    "START DATE": "10/09/2026", "END DATE": "12/09/2026", "NUMBER OF DAYS": "3"
                }
                dup = pipeline.history_manager.find_duplicate(mock_cert)
                if dup:
                    st.session_state["last_verification"] = {
                        "is_duplicate": True,
                        "cert_data": mock_cert,
                        "duplicate_of": dup,
                        "final_result": "DUPLICATE",
                        "final_reason": "This certificate already exists in the system. No new record was added and counts were not increased.",
                        "rule_output": {},
                        "ml_output": {"prediction": "N/A", "confidence": 0.0, "probabilities": {}},
                        "features": {}
                    }
                else:
                    res = pipeline._execute_core_pipeline(mock_cert, save_to_history=True)
                    st.session_state["last_verification"] = res
                st.rerun()

            if st.button("🟢 Scenario 6: Valid Internal FDP (MSRIT)", use_container_width=True):
                mock_cert = {
                    "FACULTY ID": "F012", "FACULTY NAME": "Dr. Sushma B", "FACULTY_MATCHED": True,
                    "FDP / PROGRAM NAME": "Quantum Computing: A Practical Approach",
                    "PROGRAM INSTITUTION": "Ramaiah Institute of Technology", "PROGRAM TYPE": "INTERNAL",
                    "START DATE": "07/07/2025", "END DATE": "11/07/2025", "NUMBER OF DAYS": "5"
                }
                dup = pipeline.history_manager.find_duplicate(mock_cert)
                if dup:
                    st.session_state["last_verification"] = {
                        "is_duplicate": True,
                        "cert_data": mock_cert,
                        "duplicate_of": dup,
                        "final_result": "DUPLICATE",
                        "final_reason": "This certificate already exists in the system. No new record was added and counts were not increased.",
                        "rule_output": {},
                        "ml_output": {"prediction": "N/A", "confidence": 0.0, "probabilities": {}},
                        "features": {}
                    }
                else:
                    res = pipeline._execute_core_pipeline(mock_cert, save_to_history=True)
                    st.session_state["last_verification"] = res
                st.rerun()

    # RENDER LAST VERIFICATION RESULT
    if "last_verification" in st.session_state:
        v = st.session_state["last_verification"]
        cert = v["cert_data"]
        is_dup = v.get("is_duplicate", False)

        st.markdown("---")

        if is_dup:
            # ===== DUPLICATE DETECTED UI =====
            dup_record = v.get("duplicate_of", {})

            st.markdown(f"""
            <div class='result-banner-duplicate'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='font-size:22px; font-weight:800;'>🔁 DUPLICATE CERTIFICATE DETECTED</div>
                    <div><span class='badge badge-duplicate'>DUPLICATE</span></div>
                </div>
                <div style='margin-top:10px; font-size:15px; font-weight:500; color:#f8fafc;'>
                    This certificate already exists in the system. <strong>No new record was added</strong> and <strong>counts were not increased</strong>.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            col_new, col_existing = st.columns(2)
            with col_new:
                st.markdown("#### 📄 Uploaded Certificate Info")
                st.markdown(f"""
                - **Faculty Name:** {cert.get('FACULTY NAME', 'N/A')}
                - **Faculty ID:** `{cert.get('FACULTY ID', 'N/A')}`
                - **FDP / Program:** {cert.get('FDP / PROGRAM NAME', 'N/A')}
                - **Institution:** {cert.get('PROGRAM INSTITUTION', 'N/A')}
                - **Dates:** `{cert.get('START DATE', 'N/A')}` to `{cert.get('END DATE', 'N/A')}`
                """)

            with col_existing:
                st.markdown("#### 📋 Matching Existing Record")
                st.markdown(f"""
                - **Verification ID:** `{dup_record.get('Verification ID', 'N/A')}`
                - **Faculty Name:** {dup_record.get('Faculty Name', 'N/A')}
                - **Faculty ID:** `{dup_record.get('Faculty ID', 'N/A')}`
                - **FDP / Program:** {dup_record.get('FDP Name', 'N/A')}
                - **Institution:** {dup_record.get('Institution', 'N/A')}
                - **Dates:** `{dup_record.get('Start Date', 'N/A')}` to `{dup_record.get('End Date', 'N/A')}`
                - **Original Result:** `{dup_record.get('Final Result', 'N/A')}`
                - **Verified On:** {dup_record.get('Timestamp', 'N/A')}
                """)

            st.info("ℹ️ The original verification record has been kept. This duplicate upload was ignored to prevent inflating counts and creating redundant records.")

            # Duplicate feedback section
            render_feedback_section(
                verification_id=dup_record.get("Verification ID", "DUP"),
                certificate_id=cert.get("CERTIFICATE ID", dup_record.get("Certificate ID", "")),
                faculty_name=cert.get("FACULTY NAME", ""),
                fdp_name=cert.get("FDP / PROGRAM NAME", ""),
                is_duplicate=True
            )

        else:
            # ===== NORMAL VERIFICATION RESULT =====
            rule_out = v["rule_output"]
            ml_out = v["ml_output"]
            final_res = v["final_result"]
            final_reason = v["final_reason"]

            st.subheader("📑 Verification Outcome & Explainable Evidence")

            # Result Banner
            if final_res == "VALID":
                banner_class = "result-banner-valid"
                badge_class = "badge-valid"
                icon = "✅"
            elif final_res == "INVALID":
                banner_class = "result-banner-invalid"
                badge_class = "badge-invalid"
                icon = "❌"
            else:
                banner_class = "result-banner-review"
                badge_class = "badge-review"
                icon = "⚠️"

            st.markdown(f"""
            <div class='{banner_class}'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div style='font-size:22px; font-weight:800;'>{icon} RESULT: {final_res}</div>
                    <div><span class='badge {badge_class}'>{final_res}</span></div>
                </div>
                <div style='margin-top:10px; font-size:15px; font-weight:500; color:#f8fafc;'>
                    <strong>Reason:</strong> {final_reason}
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("#### 👤 Faculty & Program Details")
                ptype = cert.get('PROGRAM TYPE', 'EXTERNAL')
                type_badge = "badge-internal" if ptype == "INTERNAL" else "badge-external"
                st.markdown(f"""
                - **Faculty Name:** {cert.get('FACULTY NAME', 'N/A')}
                - **Faculty ID:** `{cert.get('FACULTY ID', 'N/A')}`
                - **FDP / Program:** {cert.get('FDP / PROGRAM NAME', 'N/A')}
                - **Institution:** {cert.get('PROGRAM INSTITUTION', 'N/A')}
                - **Program Type:** <span class='badge {type_badge}'>{ptype}</span>
                - **FDP Dates:** `{cert.get('START DATE', 'N/A')}` to `{cert.get('END DATE', 'N/A')}` ({rule_out.get('ACTUAL_DAYS', cert.get('NUMBER OF DAYS', 'N/A'))} days)
                """, unsafe_allow_html=True)

            with col_d2:
                st.markdown("#### 🤖 Decision Engine Breakdown")
                st.markdown(f"""
                - **Rule Engine Verification:** `{rule_out.get('RULE_RESULT', 'N/A')}`
                - **Timeline Duration Match:** `{rule_out.get('TIMELINE_MATCH', 'N/A')}`
                - **ML Model Prediction:** `{ml_out.get('prediction', 'N/A')}` ({ml_out.get('confidence', 0.0)*100:.1f}% confidence)
                - **Hybrid Consensus:** `{final_res}`
                """)
                st.caption("Class Probabilities:")
                st.json(ml_out.get("probabilities", {}))

            st.markdown("#### 📅 Multi-Day Attendance Audit Trail")
            daily = rule_out.get("DAILY_ATTENDANCE", [])
            if daily:
                daily_table = []
                for item in daily:
                    flag = item.get("flag", "")
                    if flag == "VALID":
                        status_chip = "✅ VALID"
                    elif flag == "CONFLICT":
                        status_chip = "❌ CONFLICT"
                    elif flag in ["MISSING_DATE", "MISSING_MONTH"]:
                        status_chip = "⚠️ UNAVAILABLE"
                    else:
                        status_chip = "ℹ️ RECORDED"

                    daily_table.append({
                        "Date": item.get("date"),
                        "Attendance Status": item.get("status"),
                        "Verification Status": status_chip
                    })
                st.dataframe(pd.DataFrame(daily_table), use_container_width=True, hide_index=True)
            else:
                st.info("No individual date attendance records available.")

            # Training feedback workflow — only for certificates that passed verification.
            history_rec = v.get("history_record", {})
            if final_res == "VALID":
                render_training_feedback_form(
                    verification_id=history_rec.get("Verification ID", "N/A"),
                    cert=cert
                )
            else:
                st.info("📝 The Feedback on Training form becomes available after the certificate is verified as VALID.")

            # Generic verification feedback (always shown for non-duplicate results)
            render_feedback_section(
                verification_id=history_rec.get("Verification ID", "N/A"),
                certificate_id=cert.get("CERTIFICATE ID", ""),
                faculty_name=cert.get("FACULTY NAME", ""),
                fdp_name=cert.get("FDP / PROGRAM NAME", ""),
                is_duplicate=False
            )

# PAGE 3: EXISTING CERTIFICATES
elif page == "📁 Existing Certificates":
    st.markdown("""
    <div class='header-banner'>
        <h1 style='margin:0; font-size:26px; font-weight:800;'>📁 Existing Certificates (Person 1 Tracker)</h1>
        <p style='margin:4px 0 0 0; color:#94a3b8; font-size:14px;'>
            Certificates pre-registered in the system. Select any certificate to re-verify through the automated pipeline.
        </p>
    </div>
    """, unsafe_allow_html=True)

    tracker_rows = pipeline.data_loader.get_certificate_tracker_rows()
    if not tracker_rows:
        st.warning("No records found in certificate_tracker.csv.")
    else:
        df_tracker = pd.DataFrame(tracker_rows)
        
        c_filter1, c_filter2 = st.columns([1, 2])
        with c_filter1:
            fac_filter = st.selectbox("Filter by Faculty", ["All"] + sorted(list(pipeline.data_loader.faculty_by_id.values())))
        with c_filter2:
            search_tracker = st.text_input("Search FDP Title / Certificate ID", "")

        filtered_df = df_tracker
        if fac_filter != "All":
            filtered_df = filtered_df[filtered_df["FACULTY NAME"] == fac_filter]
        if search_tracker:
            st_query = search_tracker.lower()
            filtered_df = filtered_df[filtered_df.apply(lambda row: st_query in str(row).lower(), axis=1)]

        st.caption(f"Showing {len(filtered_df)} of {len(df_tracker)} certificates")
        st.dataframe(
            filtered_df[["CERTIFICATE ID", "FACULTY ID", "FACULTY NAME", "FDP / PROGRAM NAME", "PROGRAM INSTITUTION", "PROGRAM TYPE", "START DATE", "END DATE", "VERIFICATION RESULT"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.subheader("⚡ Inspect & Re-verify Certificate")
        cert_ids = filtered_df["CERTIFICATE ID"].tolist()
        if cert_ids:
            selected_cid = st.selectbox("Select Certificate ID", cert_ids)
            selected_row = next(r for r in tracker_rows if r["CERTIFICATE ID"] == selected_cid)

            c_info1, c_info2 = st.columns(2)
            with c_info1:
                st.write(f"**Faculty:** {selected_row.get('FACULTY NAME')} (`{selected_row.get('FACULTY ID')}`)")
                st.write(f"**Program:** {selected_row.get('FDP / PROGRAM NAME')}")
                st.write(f"**Institution:** {selected_row.get('PROGRAM INSTITUTION')} ({selected_row.get('PROGRAM TYPE')})")
            with c_info2:
                st.write(f"**Dates:** {selected_row.get('START DATE')} to {selected_row.get('END DATE')} ({selected_row.get('NUMBER OF DAYS')} days)")
                st.write(f"**Current Status:** {selected_row.get('VERIFICATION RESULT', 'PENDING')}")
                if selected_row.get('CERTIFICATE LINK'):
                    st.markdown(f"[🔗 View Document Link]({selected_row.get('CERTIFICATE LINK')})")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🔄 REVERIFY THIS CERTIFICATE", type="primary", use_container_width=True):
                    with st.spinner("Re-verifying certificate..."):
                        res = pipeline.verify_existing_certificate(selected_row, save_to_history=True)
                        st.session_state["last_verification"] = res
                        if res.get("is_duplicate"):
                            st.warning(f"⚠️ Certificate {selected_cid} is already verified (duplicate detected).")
                        else:
                            st.success(f"Certificate {selected_cid} re-verified: {res['final_result']}")
                            st.info(f"Reason: {res['final_reason']}")
                        time.sleep(1)
                        st.rerun()

            with col_btn2:
                if st.button("⚡ BATCH REVERIFY ALL TRACKER CERTIFICATES", use_container_width=True):
                    with st.spinner("Batch verifying all certificates..."):
                        prog_bar = st.progress(0)
                        dup_count = 0
                        new_count = 0
                        for idx, row in enumerate(tracker_rows):
                            res = pipeline.verify_existing_certificate(row, save_to_history=True)
                            if res.get("is_duplicate"):
                                dup_count += 1
                            else:
                                new_count += 1
                            prog_bar.progress((idx + 1) / len(tracker_rows))
                        st.success(f"Batch re-verification complete! {new_count} verified, {dup_count} duplicates skipped. Dashboard updated.")
                        time.sleep(1)
                        st.rerun()

# PAGE 4: VERIFICATION HISTORY
elif page == "📜 Verification History":
    st.markdown("""
    <div class='header-banner'>
        <h1 style='margin:0; font-size:26px; font-weight:800;'>📜 Complete Verification History</h1>
        <p style='margin:4px 0 0 0; color:#94a3b8; font-size:14px;'>
            Comprehensive audit log of every certificate processed through the system.
        </p>
    </div>
    """, unsafe_allow_html=True)

    all_history = pipeline.history_manager.get_all_records()
    if not all_history:
        st.info("No verification events logged yet.")
    else:
        df_hist = pd.DataFrame(all_history)

        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        with col_h1:
            res_filter = st.selectbox("Result Filter", ["All", "VALID", "INVALID", "NEEDS REVIEW"])
        with col_h2:
            type_filter = st.selectbox("Program Type", ["All", "INTERNAL", "EXTERNAL"])
        with col_h3:
            fac_hist_filter = st.selectbox("Faculty Member", ["All"] + sorted(list(set(df_hist["Faculty Name"].dropna().tolist()))))
        with col_h4:
            search_hist = st.text_input("Search Reason / FDP / ID", "")

        filtered_hist = df_hist
        if res_filter != "All":
            filtered_hist = filtered_hist[filtered_hist["Final Result"].str.upper() == res_filter]
        if type_filter != "All":
            filtered_hist = filtered_hist[filtered_hist["Internal/External"].str.upper() == type_filter]
        if fac_hist_filter != "All":
            filtered_hist = filtered_hist[filtered_hist["Faculty Name"] == fac_hist_filter]
        if search_hist:
            s_q = search_hist.lower()
            filtered_hist = filtered_hist[filtered_hist.apply(lambda row: s_q in str(row).lower(), axis=1)]

        st.caption(f"Showing {len(filtered_hist)} of {len(df_hist)} log entries")
        # Display without Fingerprint column for cleaner UI
        display_cols = [c for c in filtered_hist.columns if c != "Fingerprint"]
        st.dataframe(filtered_hist[display_cols], use_container_width=True, hide_index=True)

        csv_buffer = io.StringIO()
        filtered_hist.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Audit Log (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"fdp_verification_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

        # Faculty + Department grouped view for history
        st.markdown("---")
        st.subheader("👨‍🏫 Grouped by Faculty & Department")
        unique_recs = pipeline.history_manager.get_unique_records()
        if unique_recs:
            groups = {}
            for r in unique_recs:
                fname_display = _normalize_faculty_display(r.get("Faculty Name", "Unknown"))
                dept_display = _normalize_faculty_display(r.get("Institution", "Unknown"))
                group_key = (_normalize_group_key(r.get("Faculty Name", "")),
                             _normalize_group_key(r.get("Institution", "")))
                if group_key not in groups:
                    groups[group_key] = {
                        "faculty_display": fname_display,
                        "dept_display": dept_display,
                        "certificates": []
                    }
                groups[group_key]["certificates"].append(r)

            sorted_groups = sorted(groups.values(), key=lambda g: g["faculty_display"].lower())

            for g in sorted_groups:
                cert_count = len(g["certificates"])
                st.markdown(f"""
                <div class='faculty-group-header'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='font-size:15px; font-weight:700; color:#e2e8f0;'>👤 {g['faculty_display']}</span>
                            <span style='font-size:13px; color:#94a3b8; margin-left:10px;'>📍 {g['dept_display']}</span>
                        </div>
                        <span class='badge badge-internal'>{cert_count} cert{'s' if cert_count != 1 else ''}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                for c in g["certificates"]:
                    result = c.get("Final Result", "")
                    if "INVALID" in result.upper():
                        res_badge = "badge-invalid"
                    elif "VALID" in result.upper():
                        res_badge = "badge-valid"
                    else:
                        res_badge = "badge-review"
                    st.markdown(f"""
                    <div style='padding:6px 16px; margin:2px 0 2px 20px; font-size:13px; color:#cbd5e1;'>
                        <span class='badge {res_badge}'>{result}</span>
                        &nbsp; {c.get('FDP Name', '')} &nbsp;|&nbsp; {c.get('Start Date', '')} — {c.get('End Date', '')}
                    </div>
                    """, unsafe_allow_html=True)

# PAGE 5: MODEL PERFORMANCE
elif page == "🤖 Model Performance":
    st.markdown("""
    <div class='header-banner'>
        <h1 style='margin:0; font-size:26px; font-weight:800;'>🤖 Machine Learning Model Performance</h1>
        <p style='margin:4px 0 0 0; color:#94a3b8; font-size:14px;'>
            Evaluation metrics, feature importances, and model benchmarks powering the AIML hybrid consensus.
        </p>
    </div>
    """, unsafe_allow_html=True)

    metrics = pipeline.ml_model.metrics_
    if not metrics:
        st.info("Metrics not loaded. Retraining models to fetch evaluation stats...")
        metrics = pipeline.ml_model.train_and_evaluate()

    st.subheader("📊 Classifier Benchmark Comparison")
    table_rows = []
    for model_name, data in metrics.items():
        table_rows.append({
            "Model": model_name,
            "Accuracy": f"{data.get('accuracy', 0.0)*100:.2f}%",
            "F1-Score (Weighted)": f"{data.get('f1_score', 0.0):.4f}",
            "Status": "Active Deployment" if model_name == "RandomForest" else "Evaluated"
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    col_rf, col_feat = st.columns([1, 1])

    with col_rf:
        st.subheader("🎯 Primary Model: Random Forest")
        rf_data = metrics.get("RandomForest", {})
        st.metric("Test Accuracy", f"{rf_data.get('accuracy', 0.0)*100:.2f}%")
        st.metric("Weighted F1-Score", f"{rf_data.get('f1_score', 0.0):.4f}")
        
        st.markdown("##### Confusion Matrix")
        cm = rf_data.get("confusion_matrix", [])
        if cm:
            classes = rf_data.get("classes", ["INVALID", "NEEDS REVIEW", "VALID"])
            cm_df = pd.DataFrame(cm, index=[f"Actual {c}" for c in classes], columns=[f"Pred {c}" for c in classes])
            st.dataframe(cm_df, use_container_width=True)

    with col_feat:
        st.subheader("💡 Feature Importance Ranking")
        if hasattr(pipeline.ml_model.model, "feature_importances_"):
            importances = pipeline.ml_model.model.feature_importances_
            feat_df = pd.DataFrame({
                "Feature": pipeline.feature_engineer.feature_columns,
                "Importance": importances
            }).sort_values("Importance", ascending=False)
            st.bar_chart(feat_df.set_index("Feature"), color="#10b981")
        else:
            st.info("Feature importances available for tree-based models.")

# PAGE: TRAINING FEEDBACK (MSRIT/IQAC Feedback Dashboard & Form)
elif page == "📝 Training Feedback":
    render_training_feedback_dashboard()

# PAGE 6: FEEDBACK
elif page == "💬 Feedback":
    st.markdown("""
    <div class='header-banner'>
        <h1 style='margin:0; font-size:26px; font-weight:800;'>💬 Feedback Dashboard</h1>
        <p style='margin:4px 0 0 0; color:#94a3b8; font-size:14px;'>
            View all user feedback submitted for verification results and duplicate detections.
        </p>
    </div>
    """, unsafe_allow_html=True)

    all_feedback = pipeline.history_manager.get_all_feedback()
    if not all_feedback:
        st.info("No feedback has been submitted yet. Feedback can be submitted after verifying a certificate on the '🔍 Verify New Certificate' page.")
    else:
        fb_df = pd.DataFrame(all_feedback)
        st.caption(f"Total feedback entries: {len(fb_df)}")
        st.dataframe(fb_df, use_container_width=True, hide_index=True)

        csv_buffer = io.StringIO()
        fb_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Feedback Log (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"fdp_feedback_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    st.markdown("---")
    st.subheader("📩 Submit Standalone Feedback")
    st.caption("Use this form to submit general feedback about the verification system.")

    fb_standalone_type = st.radio(
        "Feedback category",
        ["Correct result", "Incorrect result", "Duplicate detected incorrectly",
         "Duplicate was not detected", "Other"],
        key="standalone_fb_type"
    )
    fb_standalone_comment = st.text_area(
        "Comments",
        key="standalone_fb_comment",
        placeholder="Describe your feedback..."
    )

    if st.button("📩 Submit General Feedback", key="standalone_fb_submit"):
        if fb_standalone_comment or fb_standalone_type:
            try:
                pipeline.history_manager.record_feedback(
                    verification_id="GENERAL",
                    certificate_id="N/A",
                    faculty_name="N/A",
                    fdp_name="N/A",
                    feedback_type=fb_standalone_type,
                    comment=fb_standalone_comment,
                    is_duplicate_context=False
                )
                st.success("✅ Thank you! Your feedback has been saved.")
            except Exception as e:
                st.error(f"Error saving feedback: {e}")
        else:
            st.warning("Please provide feedback text or select a category.")

# PAGE 7: ABOUT
elif page == "ℹ️ About":
    st.markdown("""
    <div class='header-banner'>
        <h1 style='margin:0; font-size:26px; font-weight:800;'>ℹ️ About the FDP Certificate Verification System</h1>
        <p style='margin:4px 0 0 0; color:#94a3b8; font-size:14px;'>
            Automated AIML solution for Ramaiah Institute of Technology (MSRIT) Faculty Development Programs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### 🎯 System Purpose & Architecture
    This application verifies Faculty Development Program (FDP) certificates submitted by faculty members of **Ramaiah Institute of Technology (MSRIT)**. It integrates:
    
    1. **PERSON 1 Responsibilities:**
       - `faculty_master.csv`: 32 Verified Faculty Records (F001–F032).
       - `attendance_sheet.csv`: 426 Official daily attendance logs with 7 institutional statuses.
       - `certificate_tracker.csv`: 42 Institutional submissions.
       - Source of truth for institutional verification rules.

    2. **PERSON 2 Responsibilities:**
       - Certificate OCR & Text Extraction.
       - Faculty Identification & Institution normalization (MSRIT, RIT, M.S. Ramaiah Institute of Technology).
       - Timeline & date range generation.
       - Initial rule logic & edge-case testing.

    3. **PERSON 3 (This Application):**
       - Unified application architecture & Streamlit UI.
       - Multi-day attendance lookup checking **every single date** in the FDP range.
       - Detection of **missing attendance** (distinguishing between entire missing month and individual missing date).
       - **Duplicate certificate detection** using content-based fingerprinting (faculty, program, dates, institution).
       - **Faculty + Department grouping** for organized certificate views.
       - **Persistent feedback system** for verification accuracy tracking.
       - Feature engineering (17 domain features) without target leakage.
       - Machine Learning model training (Random Forest, Gradient Boosting, etc.) and inference.
       - Hybrid consensus engine: Rules ensure attendance conflicts cannot be silently overridden by ML.
       - Real-time reactive dashboard & complete verification history audit log.

    ### ⚖️ Core Institutional Rules
    - **Internal vs External:** Refers to the **FDP/Program Institution**, NOT the faculty member.
      - Conducted at Ramaiah Institute of Technology $\\rightarrow$ **INTERNAL** (requires `PRESENT` or `HOLIDAY`).
      - Conducted at external university/organization $\\rightarrow$ **EXTERNAL** (requires `OOD` or `HOLIDAY`).
    - **Multi-Day FDPs:** Every day between Start Date and End Date is checked. Two OOD days and one Leave day $\\rightarrow$ **INVALID**.
    - **Missing Attendance:** Missing attendance data does **NOT** mean Valid or Invalid $\\rightarrow$ **NEEDS REVIEW**.
    - **Faculty Matching:** Faculty ID is primary. If faculty cannot be reliably matched $\\rightarrow$ **NEEDS REVIEW**.
    - **Duplicate Detection:** Certificates are fingerprinted by faculty name, institution, FDP name, dates, and certificate number. Duplicate uploads are rejected without creating new records or inflating counts.
    """)

st.markdown("""
<div style='text-align: center; margin-top: 40px; padding: 20px; color: #64748b; font-size: 13px; border-top: 1px solid rgba(255,255,255,0.05);'>
    Ramaiah Institute of Technology (MSRIT) • Department of Artificial Intelligence & Machine Learning<br>
    Final Integrated Application • Automated FDP Certificate Verification System
</div>
""", unsafe_allow_html=True)
