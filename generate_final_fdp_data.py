"""
FDP Certificate Verification System — Complete Data Pipeline & Generator
========================================================================
Person 1 Responsibilities:
1. Data Preparation from authoritative source (April 2025 till date   Faculty attended FDP_Workshop_STTP.csv)
2. Existing Google Sheet Preparation (3 tabs: FACULTY MASTER, ATTENDANCE SHEET, CERTIFICATE TRACKER)
3. Faculty / FDP / Certificate Mapping (42 records mapped to F001–F032, preserved Drive links)
4. FDP-Linked Synthetic Attendance Dataset (426 records, 7 statuses, 10 test cases)

Output files:
- fdp_data/faculty_master.csv
- fdp_data/certificate_tracker.csv
- fdp_data/attendance_sheet.csv
- updateFDPSheet.gs (ready to paste and run in Google Apps Script)
"""

import csv
import io
import json
import zipfile
import datetime
from collections import Counter, defaultdict

# ── 1. FACULTY MASTER (32 Faculty Members) ───────────────────────────────────
FACULTY_MASTER = [
    ("F001", "Dr. S. Seema"),
    ("F002", "Dr. Monica R. Mundada"),
    ("F003", "Dr. Shilpa Shashikant Chaudhari"),
    ("F004", "Dr. Geetha J."),
    ("F005", "Nagabhushan A. M"),
    ("F006", "Dr. T.N.R.Kumar"),
    ("F007", "Dr. S. Rajarajeswari"),
    ("F008", "Dr. J Sangeetha"),
    ("F009", "Dr. Dayananda R. B."),
    ("F010", "Dr Sangeetha.V"),
    ("F011", "Dr. Ganeshayya Shidaganti"),
    ("F012", "Dr. Sushma B"),
    ("F013", "Dr. DEVARAJU B M"),
    ("F014", "Veena G.S."),
    ("F015", "Dr. Mallegowda M."),
    ("F016", "Dr. Chandrika Prasad"),
    ("F017", "Pradeep Kumar D."),
    ("F018", "Darshana A. Naik"),
    ("F019", "Nandini S B"),
    ("F020", "Soumya C S"),
    ("F021", "Dr. Akshata S. Bhayyar"),
    ("F022", "Mamatha A"),
    ("F023", "Vishwachetan D"),
    ("F024", "Pallavi N"),
    ("F025", "Akshatha Kamath"),
    ("F026", "Dr. Manjula R Chougala"),
    ("F027", "Priya K"),
    ("F028", "Brunda G"),
    ("F029", "Uzma Sulthana"),
    ("F030", "Uzma Taj"),
    ("F031", "Swetha M"),
    ("F032", "Sahil Kumar Jamwal")
]

# Name mapping dictionary from source CSV variations to standard Faculty Master
NAME_TO_FACULTY = {
    'Dr. Sushma B': ('F012', 'Dr. Sushma B'),
    'Dr. Mallegowda M': ('F015', 'Dr. Mallegowda M.'),
    'Dr. MAllegowda M': ('F015', 'Dr. Mallegowda M.'),
    'PRIYA K': ('F027', 'Priya K'),
    'priya K': ('F027', 'Priya K'),
    'Dr. Akshata S Bhayyar': ('F021', 'Dr. Akshata S. Bhayyar'),
    'Dr Akshata S Bhayyar': ('F021', 'Dr. Akshata S. Bhayyar'),
    'Nandini S B': ('F019', 'Nandini S B'),
    'Akshatha Kamath': ('F025', 'Akshatha Kamath'),
    'Dr Ganeshayya Shidaganti': ('F011', 'Dr. Ganeshayya Shidaganti'),
    'Dr Ganeshayya Shidaganti@msrit.edu': ('F011', 'Dr. Ganeshayya Shidaganti'),
    'Shilpa Chaudhari': ('F003', 'Dr. Shilpa Shashikant Chaudhari'),
    'Swetha M': ('F031', 'Swetha M'),
    'Dr.Sangeetha V': ('F010', 'Dr Sangeetha.V'),
    'Mamatha A': ('F022', 'Mamatha A'),
    'Dr. Devaraju B M': ('F013', 'Dr. DEVARAJU B M'),
    'Sahil Kumar Jamwal': ('F032', 'Sahil Kumar Jamwal'),
    'Dr.Rajarajeswari S': ('F007', 'Dr. S. Rajarajeswari'),
}

INTERNAL_INSTITUTIONS = {'ramaiah institute of technology', 'msrit', 'msrit bangalore', 'rit'}

def main():
    # ── 2. Read Source CSV from ZIP ──────────────────────────────────────────
    zip_path = '/Users/shags/Desktop/April 2025 till date   Faculty attended FDP_Workshop_STTP.csv.zip'
    with zipfile.ZipFile(zip_path) as z:
        fname = z.namelist()[0]
        with z.open(fname) as f:
            raw_text = f.read().decode('utf-8', errors='replace')
    
    reader = csv.reader(io.StringIO(raw_text))
    source_rows = list(reader)[1:] # Skip header

    # ── 3. Prepare Certificate Tracker Data ───────────────────────────────────
    # Columns required:
    # A: CERTIFICATE ID
    # B: FACULTY ID
    # C: FACULTY NAME
    # D: FDP / PROGRAM NAME
    # E: PROGRAM INSTITUTION
    # F: PROGRAM TYPE
    # G: START DATE (DD/MM/YYYY)
    # H: END DATE (DD/MM/YYYY)
    # I: NUMBER OF DAYS
    # J: CERTIFICATE LINK
    # K: EXTRACTED DETAILS (empty)
    # L: ATTENDANCE STATUS (empty)
    # M: TIMELINE MATCH (empty)
    # N: VERIFICATION RESULT (empty)
    # O: VERIFICATION REASON (empty)
    # P: SUBMITTED DATE (DD/MM/YYYY)

    cert_rows = []
    certs_meta = []

    for i, r in enumerate(source_rows, 1):
        cid = f"CERT-{i:03d}"
        ts, raw_name, desig, raw_type, title, from_date_str, to_date_str, days_str, college, cond_by, place, cert_link, iqac = r
        
        fac_id, fac_name = NAME_TO_FACULTY[raw_name.strip()]
        inst = college.strip()
        ptype = "INTERNAL" if inst.lower() in INTERNAL_INSTITUTIONS else "EXTERNAL"
        
        dt_from = datetime.datetime.strptime(from_date_str.strip(), "%Y-%m-%d").date()
        dt_to = datetime.datetime.strptime(to_date_str.strip(), "%Y-%m-%d").date()
        
        calc_days = (dt_to - dt_from).days + 1
        
        # Parse submitted date from timestamp e.g. "2025/10/23 2:23:04 PM GMT+5:30"
        ts_date_str = ts.strip().split()[0]
        sub_dt = datetime.datetime.strptime(ts_date_str, "%Y/%m/%d").date()
        
        start_date_ddmmyyyy = dt_from.strftime("%d/%m/%Y")
        end_date_ddmmyyyy = dt_to.strftime("%d/%m/%Y")
        sub_date_ddmmyyyy = sub_dt.strftime("%d/%m/%Y")
        
        row = [
            cid,
            fac_id,
            fac_name,
            title.strip(),
            inst,
            ptype,
            start_date_ddmmyyyy,
            end_date_ddmmyyyy,
            calc_days,
            cert_link.strip(),
            "", # EXTRACTED DETAILS (reserved for Person 2)
            "", # ATTENDANCE STATUS (reserved for Person 2)
            "", # TIMELINE MATCH (reserved for Person 2)
            "", # VERIFICATION RESULT (reserved for Person 2)
            "", # VERIFICATION REASON (reserved for Person 2)
            sub_date_ddmmyyyy
        ]
        cert_rows.append(row)
        certs_meta.append({
            "idx": i,
            "cid": cid,
            "fac_id": fac_id,
            "fac_name": fac_name,
            "title": title.strip(),
            "institution": inst,
            "ptype": ptype,
            "from_dt": dt_from,
            "to_dt": dt_to,
            "start_date_str": start_date_ddmmyyyy,
            "end_date_str": end_date_ddmmyyyy,
            "calc_days": calc_days,
            "source_days": days_str.strip(),
            "link": cert_link.strip(),
            "sub_date_str": sub_date_ddmmyyyy
        })

    # Write fdp_data/certificate_tracker.csv
    cert_headers = [
        "CERTIFICATE ID", "FACULTY ID", "FACULTY NAME", "FDP / PROGRAM NAME",
        "PROGRAM INSTITUTION", "PROGRAM TYPE", "START DATE", "END DATE",
        "NUMBER OF DAYS", "CERTIFICATE LINK", "EXTRACTED DETAILS",
        "ATTENDANCE STATUS", "TIMELINE MATCH", "VERIFICATION RESULT",
        "VERIFICATION REASON", "SUBMITTED DATE"
    ]
    with open("fdp_data/certificate_tracker.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cert_headers)
        writer.writerows(cert_rows)

    print(f"certificate_tracker.csv written with {len(cert_rows)} rows.")

    # ── 4. Generate Synthetic Attendance Dataset ──────────────────────────────
    # Base rule:
    # - Connected directly to the actual FDP dates from CERTIFICATE TRACKER
    # - Internal FDP -> PRESENT on weekdays
    # - External FDP -> OOD on weekdays
    # - Weekends (Saturday / Sunday) -> HOLIDAY
    # Key: (FACULTY ID, DATE) -> exactly one institutional attendance record per faculty per date

    attendance_dict = {} # (fac_id, date_obj) -> (fac_name, status)

    # Base generation
    for c in certs_meta:
        fid = c["fac_id"]
        fname = c["fac_name"]
        curr = c["from_dt"]
        while curr <= c["to_dt"]:
            is_weekend = (curr.weekday() in [5, 6])
            if is_weekend:
                status = "HOLIDAY"
            elif c["ptype"] == "INTERNAL":
                status = "PRESENT"
            else:
                status = "OOD"
            
            if (fid, curr) not in attendance_dict:
                attendance_dict[(fid, curr)] = (fname, status)
            curr += datetime.timedelta(days=1)

    # Deliberate Test Case Embeddings:
    # CASE 1: External FDP dates match OOD attendance throughout the FDP period
    #  -> CERT-015: F011 (Dr. Ganeshayya Shidaganti) 09/02/2026 to 13/02/2026 (all 5 days OOD)
    #  -> CERT-016: F011 (Dr. Ganeshayya Shidaganti) 28/07/2025 to 01/08/2025 (all 5 days OOD)
    #  -> CERT-033: F027 (Priya K) 29/06/2026 to 03/07/2026 (all 5 days OOD)

    # CASE 2: External FDP has CASUAL LEAVE on an FDP date
    #  -> CERT-006: F015 (Dr. Mallegowda M.) on 31/07/2025
    attendance_dict[("F015", datetime.date(2025, 7, 31))] = ("Dr. Mallegowda M.", "CASUAL LEAVE")

    # CASE 3: External FDP has EMERGENCY LEAVE on an FDP date
    #  -> CERT-017: F012 (Dr. Sushma B) on 08/11/2025
    attendance_dict[("F012", datetime.date(2025, 11, 8))] = ("Dr. Sushma B", "EMERGENCY LEAVE")

    # CASE 4: External FDP overlaps with a HOLIDAY
    #  -> CERT-030: F015 (Dr. Mallegowda M.) on 19/11/2025 (institutional holiday) & 22/11/2025 (weekend)
    attendance_dict[("F015", datetime.date(2025, 11, 19))] = ("Dr. Mallegowda M.", "HOLIDAY")

    # CASE 5: External FDP overlaps with UNPAID LEAVE
    #  -> CERT-025: F021 (Dr. Akshata S. Bhayyar) on 12/03/2026
    attendance_dict[("F021", datetime.date(2026, 3, 12))] = ("Dr. Akshata S. Bhayyar", "UNPAID LEAVE")

    # CASE 6: External FDP overlaps with VACATION
    #  -> CERT-020: F003 (Dr. Shilpa Shashikant Chaudhari) on 20/12/2025 to 31/12/2025
    curr = datetime.date(2025, 12, 20)
    end_vac = datetime.date(2025, 12, 31)
    while curr <= end_vac:
        attendance_dict[("F003", curr)] = ("Dr. Shilpa Shashikant Chaudhari", "VACATION")
        curr += datetime.timedelta(days=1)

    # CASE 7: Partial attendance / timeline mismatch
    #  -> CERT-032: F011 (Dr. Ganeshayya Shidaganti) 16/06/2026 to 19/06/2026
    #     16-17/06: OOD, but 18-19/06: PRESENT at Ramaiah Institute of Technology
    attendance_dict[("F011", datetime.date(2026, 6, 18))] = ("Dr. Ganeshayya Shidaganti", "PRESENT")
    attendance_dict[("F011", datetime.date(2026, 6, 19))] = ("Dr. Ganeshayya Shidaganti", "PRESENT")

    # CASE 8: Missing attendance for one or more FDP dates
    #  -> CERT-026: F025 (Akshatha Kamath) on 30/07/2026 (record completely omitted)
    if ("F025", datetime.date(2026, 7, 30)) in attendance_dict:
        del attendance_dict[("F025", datetime.date(2026, 7, 30))]

    # CASE 9: A fully matching FDP timeline
    #  -> Multiple Internal FDPs (CERT-001, CERT-007, CERT-011, CERT-014, CERT-021, CERT-022, CERT-023,
    #     CERT-031, CERT-034, CERT-036, CERT-037, CERT-038, CERT-039, CERT-040, CERT-042)

    # CASE 10: A deliberately conflicting FDP timeline
    #  -> CERT-005: F015 (Dr. Mallegowda M.) on 17/07/2025 and 18/07/2025
    #     Claims external workshop at BITS Pilani Hyderabad, but attendance log shows PRESENT on campus at MSRIT!
    attendance_dict[("F015", datetime.date(2025, 7, 17))] = ("Dr. Mallegowda M.", "PRESENT")
    attendance_dict[("F015", datetime.date(2025, 7, 18))] = ("Dr. Mallegowda M.", "PRESENT")
    #  -> CERT-003: F012 (Dr. Sushma B) on 14/07/2025 to 18/07/2025
    #     Claims external FDP at NIT Patna, but attendance log shows PRESENT at Ramaiah for CERT-002!

    # Sort attendance records chronologically by Date, then by Faculty ID
    sorted_attendance_keys = sorted(attendance_dict.keys(), key=lambda k: (k[1], k[0]))
    
    attendance_rows = []
    for fid, dt in sorted_attendance_keys:
        fname, status = attendance_dict[(fid, dt)]
        attendance_rows.append([
            fid,
            fname,
            dt.strftime("%d/%m/%Y"),
            status
        ])

    # Write fdp_data/attendance_sheet.csv
    att_headers = ["FACULTY ID", "FACULTY NAME", "DATE", "ATTENDANCE STATUS"]
    with open("fdp_data/attendance_sheet.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(att_headers)
        writer.writerows(attendance_rows)

    print(f"attendance_sheet.csv written with {len(attendance_rows)} rows.")

    # Status distribution
    status_counts = Counter(r[3] for r in attendance_rows)
    print("\nAttendance Status Distribution:")
    for st, c in status_counts.items():
        print(f"  {st:<16}: {c}")

    min_date = min(k[1] for k in attendance_dict.keys()).strftime("%d/%m/%Y")
    max_date = max(k[1] for k in attendance_dict.keys()).strftime("%d/%m/%Y")
    print(f"\nAttendance Date Range: {min_date} to {max_date}")

    return cert_rows, attendance_rows

if __name__ == "__main__":
    main()
