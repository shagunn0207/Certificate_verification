# FDP Certificate Verification System
**Ramaiah Institute of Technology (MSRIT)**  
*Department of Artificial Intelligence & Machine Learning (AIML)*  
*Automated AIML-Based Verification Engine for Faculty Development Programs*

---

## 📌 Project Overview
The **FDP Certificate Verification System** is a unified automated platform built for the faculty and administration of **Ramaiah Institute of Technology (MSRIT)**. It automates the verification of Faculty Development Program (FDP), Workshop, and STTP participation certificates against institutional records and official attendance registries.

Instead of administrative staff manually cross-referencing dates, certificates, and leave records, this system automatically extracts certificate data, looks up daily attendance for every single day in the FDP duration, performs feature engineering, and combines a trained Machine Learning classifier with a deterministic institutional rule engine to yield explainable, transparent verification outcomes:
* **`VALID`**: All criteria satisfied, matching attendance evidence verified for all dates.
* **`INVALID`**: Definite conflict detected (e.g., Casual Leave, Emergency Leave, Unpaid Leave, or timeline mismatch).
* **`NEEDS REVIEW`**: Missing attendance evidence, unrecorded month, or faculty identity ambiguity requiring human review.

---

## 👥 Team Roles & Responsibilities

| Role | Member Responsibilities | Integrated Deliverables |
| :--- | :--- | :--- |
| **Person 1** | Data Preparation & Google Sheets | • `faculty_master.csv` (32 Faculty Members: F001–F032)<br>• `attendance_sheet.csv` (426 Daily Attendance Records, 7 Statuses)<br>• `certificate_tracker.csv` (42 Submissions)<br>• Institutional Verification Rules |
| **Person 2** | Certificate OCR & Extraction | • OCR & text extraction logic<br>• Institution normalization (`MSRIT`, `RIT` $\rightarrow$ `Ramaiah Institute of Technology`)<br>• Initial timeline matching and edge-case unit tests |
| **Person 3** *(This Application)* | System Architecture, ML, UI & Complete Integration | • End-to-end automated pipeline (`src/pipeline.py`)<br>• Multi-day attendance lookup checking **every single date**<br>• Missing attendance detection (Missing month vs missing date)<br>• Feature engineering (17 features) avoiding target leakage<br>• ML classification models (Random Forest, Gradient Boosting, Decision Tree, Logistic Regression)<br>• Hybrid Consensus engine (Rules prevent silent ML override)<br>• Interactive web dashboard & audit history (`app.py`)<br>• 18-case unit & integration test suite (`tests/`) |

---

## 🏛️ System Architecture

```text
                    USER
                      │
                      ▼
              UPLOAD CERTIFICATE (PDF / PNG / JPG)
                      │
                      ▼
             OCR & TEXT EXTRACTION (pdfplumber, pypdf, regex)
                      │
                      ▼
             STRUCTURED CERTIFICATE METADATA
                      │
                      ▼
          FACULTY MATCHING (Faculty ID primary -> Faculty Name fallback)
                      │
                      ▼
          INSTITUTION NORMALIZATION & INTERNAL/EXTERNAL CLASSIFICATION
                      │
                      ▼
          MULTI-DAY ATTENDANCE LOOKUP (Check EVERY date in range)
                      │
                      ▼
          FEATURE ENGINEERING (17 tabular domain features)
                      │
              ┌───────┴───────┐
              ▼               ▼
          ML MODEL       RULE ENGINE
       (Random Forest) (Institutional Rules)
              │               │
              └───────┬───────┘
                      ▼
             HYBRID CONSENSUS RESULT
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        VALID      INVALID   NEEDS REVIEW
                      │
                      ▼
             EXPLAINABLE REASON & AUDIT EVIDENCE
                      │
                      ▼
           PERSISTENT AUDIT LOG & DASHBOARD UPDATE
```

---

## ⚖️ Institutional Rules & Attendance Logic

### 1. Internal vs External FDPs
* **INTERNAL**: FDP conducted by or at **Ramaiah Institute of Technology** (aliases: `MSRIT`, `RIT`, `M.S. Ramaiah Institute of Technology`).  
  *Valid supporting statuses*: `PRESENT`, `OOD`, `HOLIDAY`.
* **EXTERNAL**: FDP conducted at another college, university, or organization (e.g., NIT Patna, BITS Pilani, JAIN).  
  *Valid supporting statuses*: `OOD`, `HOLIDAY`.  
  *(Note: Being marked `PRESENT` on the MSRIT campus during an external FDP indicates an on-campus conflict and is flagged `INVALID`).*

### 2. Multi-Day Verification (Every Date Checked)
For a multi-day FDP (e.g. `10/09/2026` to `12/09/2026`), the system checks:
* Day 1: `10/09/2026`
* Day 2: `11/09/2026`
* Day 3: `12/09/2026`
If two days are `OOD` and one day is `Casual Leave`, the result is **`INVALID`**.

### 3. Missing Attendance Handling
Missing attendance data **NEVER** defaults to `VALID` or `INVALID`:
* **Case 1 (Entire Month Missing)**: If no attendance records exist for that month $\rightarrow$ **`NEEDS REVIEW`**  
  *Reason*: `"Attendance records for September 2026 are unavailable. The certificate cannot be automatically verified against attendance data."*
* **Case 2 (Individual Date Missing)**: If month exists but one required date has no record $\rightarrow$ **`NEEDS REVIEW`**  
  *Reason*: `"Attendance record for 12/09/2026 is unavailable. The complete FDP period could not be verified."*
* **Case 3 (All Records Present)**: Evaluated deterministically $\rightarrow$ **`VALID`** or **`INVALID`**.

---

## 🤖 Machine Learning Model & Feature Engineering

### Tabular Features (17 Features)
1. `is_internal`: Binary indicator for MSRIT internal program.
2. `duration_days`: Calculated duration between start and end dates.
3. `claimed_days`: Claimed duration stated on certificate.
4. `timeline_match`: 1 if claimed days equals actual days, else 0.
5. `faculty_matched`: 1 if faculty matched in Faculty Master, else 0.
6. `cert_details_completeness`: Ratio of required fields successfully extracted.
7. `ood_count`: Count of days marked OOD.
8. `present_count`: Count of days marked PRESENT.
9. `holiday_count`: Count of days marked HOLIDAY.
10. `casual_leave_count`: Count of CASUAL LEAVE days.
11. `emergency_leave_count`: Count of EMERGENCY LEAVE days.
12. `unpaid_leave_count`: Count of UNPAID LEAVE days.
13. `vacation_count`: Count of VACATION days.
14. `conflict_days_count`: Total conflicting days.
15. `missing_days_count`: Count of days without attendance records.
16. `is_month_missing`: 1 if the entire month has no records.
17. `attendance_coverage`: Ratio of available records to duration days.

### Evaluation Benchmark
| Classifier | Test Accuracy | Weighted F1-Score | Status |
| :--- | :---: | :---: | :--- |
| **Random Forest** | **100.0%** | **1.0000** | **Deployed Primary** |
| **Gradient Boosting** | **100.0%** | **1.0000** | Evaluated |
| **Decision Tree** | **100.0%** | **1.0000** | Evaluated |
| **Logistic Regression** | **98.2%** | **0.9821** | Evaluated |

---

## 📁 Repository Structure
```text
Certificate_verification/
│
├── app.py                             # Streamlit Web Application (6 Main Pages)
├── requirements.txt                   # Production Python Dependencies
├── README.md                          # Comprehensive Project Documentation
│
├── data/                              # Data Directory
│   ├── faculty_master.csv             # Person 1: 32 Faculty Records (F001–F032)
│   ├── attendance_sheet.csv           # Person 1: 426 Attendance Logs
│   ├── certificate_tracker.csv        # Person 1: 42 Certificate Submissions
│   └── training_dataset.csv           # Synthesized ML Training Dataset
│
├── fdp_data/                          # Person 1 Original Data Folder
│   ├── faculty_master.csv
│   ├── attendance_sheet.csv
│   └── certificate_tracker.csv
│
├── models/                            # Trained AIML Models & Preprocessors
│   ├── certificate_verification_model.pkl
│   ├── preprocessor.pkl
│   └── feature_config.json
│
├── src/                               # Modular Backend Source Code
│   ├── utils.py                       # Date normalization & institution aliases
│   ├── data_loader.py                 # Master CSV loading & fast lookup caching
│   ├── ocr_processor.py               # PDF/Image text extraction & regex parser
│   ├── certificate_processing.py      # Upload handler & faculty matching
│   ├── verification.py                # Deterministic rule engine & multi-day checks
│   ├── feature_engineering.py         # 17-feature vector extraction
│   ├── ml_model.py                    # Training, evaluation & inference engine
│   ├── history.py                     # Audit logger & dynamic dashboard statistics
│   └── pipeline.py                    # End-to-end unified verification orchestrator
│
├── notebooks/
│   └── model_training.ipynb           # Model Training & Evaluation Jupyter Notebook
│
├── results/
│   └── verification_results.csv       # Persistent Verification Audit Log
│
├── uploads/                           # Uploaded Certificate Storage
│
└── tests/                             # Comprehensive Unit & Integration Test Suites
    ├── test_dates.py                  # Date parsing & range generation tests
    ├── test_matching.py               # Faculty & institution matching tests
    ├── test_verification.py           # Rule engine edge cases tests
    └── test_pipeline.py               # 18 Mandatory System Test Cases
```

---

## 🚀 How to Run the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run All Tests
```bash
python -m unittest discover tests
```
*Expected: 19 tests run with 100% pass rate.*

### 3. Launch the Web Application
```bash
streamlit run app.py
```
The application will launch in your browser at `http://localhost:8501`.

---

## 🧪 Demonstration Test Cases (Section 28)

| # | Test Scenario | Input Summary | Expected Result | Reason Summary |
| :-: | :--- | :--- | :-: | :--- |
| **1** | Internal FDP | F012 (Dr. Sushma B), MSRIT, 07/07/2025–11/07/2025 | **VALID** | Timeline consistent, Present on campus |
| **2** | External FDP + OOD | F011 (Dr. Ganeshayya Shidaganti), BMSCE, 09/02/2026–13/02/2026 | **VALID** | All dates marked OOD |
| **3** | External + Casual Leave | F015 (Dr. Mallegowda M.), 28/07/2025–01/08/2025 | **INVALID** | Casual Leave recorded on 31/07/2025 |
| **4** | External + Emergency Leave | F012 (Dr. Sushma B), 05/11/2025–09/11/2025 | **INVALID** | Emergency Leave recorded on 08/11/2025 |
| **5** | Holiday Alignment | F015, 17/11/2025–22/11/2025, Holiday on 19/11 | **VALID** | Supporting holiday / weekend |
| **6** | Unpaid Leave Conflict | F021, SwipeGen, 10/03/2026–14/03/2026 | **INVALID** | Unpaid Leave recorded on 12/03/2026 |
| **7** | Multi-day FDP | F027 (Priya K), JAIN, 29/06/2026–03/07/2026 | **VALID** | All 5 days verified |
| **8** | One Conflict in Multi-day | F001, 10/09/2026–12/09/2026 (10-11 OOD, 12 CL) | **INVALID** | Casual Leave on 12/09/2026 |
| **9** | Wrong Faculty | F999 (NonExistent), MSRIT | **NEEDS REVIEW** | Faculty could not be reliably matched |
| **10** | Missing FDP Date | F012, dates missing | **NEEDS REVIEW** | FDP start/end date could not be determined |
| **11** | Entire Month Missing | F002, 10/09/2026–12/09/2026 (Sept 2026 missing) | **NEEDS REVIEW** | Attendance records for Sept 2026 unavailable |
| **12** | Single Date Missing | F005, 10/09/2026–12/09/2026 (12/09 missing) | **NEEDS REVIEW** | Attendance record for 12/09/2026 unavailable |
| **13** | Poor Quality Text | Unparseable date strings `??/??/????` | **INVALID** | Invalid date format |
| **14** | Different Date Format | `September 10, 2026` to `September 12, 2026` | **VALID** | Flexible parser normalized to DD/MM/YYYY |
| **15** | Existing Re-verification | CERT-001 from `certificate_tracker.csv` | **VALID** | Successfully verified through pipeline |
| **16** | New Upload Verification | PDF certificate with embedded metadata | **VALID** | End-to-end OCR and verification |
| **17** | Invalid File Format | `.exe` file extension | **REJECTED** | ValueError: unsupported file format |
| **18** | Complete Attendance Evidence | CERT-033 from tracker | **VALID** | Fully verified against attendance sheet |