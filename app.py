import os
import io
import time
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
</style>
""", unsafe_allow_html=True)

# Imports from src pipeline
from src.pipeline import VerificationPipeline
from src.data_loader import DataLoader
from src.utils import normalize_date_to_ddmmyyyy

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
        ["📊 Dashboard", "🔍 Verify New Certificate", "📁 Existing Certificates", "📜 Verification History", "🤖 Model Performance", "ℹ️ About"],
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
    st.subheader("👨‍🏫 Faculty Verification Summary")
    fac_data = stats.get("faculty_breakdown", {})
    if fac_data:
        f_df = pd.DataFrame(list(fac_data.items()), columns=["Faculty Name", "Verified Submissions"]).sort_values("Verified Submissions", ascending=False)
        st.dataframe(f_df, use_container_width=True, hide_index=True)

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
                res = pipeline._execute_core_pipeline(mock_cert, save_to_history=True)
                st.session_state["last_verification"] = res
                st.rerun()

    # RENDER LAST VERIFICATION RESULT
    if "last_verification" in st.session_state:
        v = st.session_state["last_verification"]
        cert = v["cert_data"]
        rule_out = v["rule_output"]
        ml_out = v["ml_output"]
        final_res = v["final_result"]
        final_reason = v["final_reason"]

        st.markdown("---")
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
                        st.success(f"Certificate {selected_cid} re-verified: {res['final_result']}")
                        st.info(f"Reason: {res['final_reason']}")
                        time.sleep(1)
                        st.rerun()

            with col_btn2:
                if st.button("⚡ BATCH REVERIFY ALL TRACKER CERTIFICATES", use_container_width=True):
                    with st.spinner("Batch verifying all certificates..."):
                        prog_bar = st.progress(0)
                        for idx, row in enumerate(tracker_rows):
                            pipeline.verify_existing_certificate(row, save_to_history=True)
                            prog_bar.progress((idx + 1) / len(tracker_rows))
                        st.success("Batch re-verification complete! Dashboard updated.")
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
        st.dataframe(filtered_hist, use_container_width=True, hide_index=True)

        csv_buffer = io.StringIO()
        filtered_hist.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Audit Log (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"fdp_verification_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

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

# PAGE 6: ABOUT
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
    """)

st.markdown("""
<div style='text-align: center; margin-top: 40px; padding: 20px; color: #64748b; font-size: 13px; border-top: 1px solid rgba(255,255,255,0.05);'>
    Ramaiah Institute of Technology (MSRIT) • Department of Artificial Intelligence & Machine Learning<br>
    Final Integrated Application • Automated FDP Certificate Verification System
</div>
""", unsafe_allow_html=True)
