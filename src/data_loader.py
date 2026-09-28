import os
import csv
import re
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from src.utils import extract_month_year, normalize_date_to_ddmmyyyy, normalize_institution

class DataLoader:
    def __init__(self, data_dir: Optional[str] = None):
        """
        Locates and loads data from data/ or fdp_data/ directory.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if data_dir and os.path.exists(data_dir):
            self.data_dir = data_dir
        elif os.path.exists(os.path.join(base_dir, "data")):
            self.data_dir = os.path.join(base_dir, "data")
        elif os.path.exists(os.path.join(base_dir, "fdp_data")):
            self.data_dir = os.path.join(base_dir, "fdp_data")
        else:
            self.data_dir = base_dir

        self.faculty_file = os.path.join(self.data_dir, "faculty_master.csv")
        self.attendance_file = os.path.join(self.data_dir, "attendance_sheet.csv")
        self.tracker_file = os.path.join(self.data_dir, "certificate_tracker.csv")

        self.faculty_by_id: Dict[str, str] = {}
        self.faculty_by_name: Dict[str, Tuple[str, str]] = {}
        self.attendance_lookup: Dict[Tuple[str, str], str] = {}
        self.faculty_months_available: Dict[str, Set[str]] = defaultdict(set)
        self.all_recorded_months: Set[str] = set()

        self.load_all()

    def load_all(self):
        self._load_faculty()
        self._load_attendance()

    def _normalize_name_key(self, name: str) -> str:
        """
        Cleans faculty name for robust matching:
        removes honorifics (Dr., Prof., etc.), punctuation, and whitespace.
        """
        clean = name.lower()
        clean = re.sub(r'^(dr\.|dr|prof\.|prof|mr\.|mr|ms\.|ms|mrs\.|mrs)\s*', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'[^a-z0-9]', '', clean)
        return clean

    def _load_faculty(self):
        self.faculty_by_id = {}
        self.faculty_by_name = {}

        if not os.path.exists(self.faculty_file):
            return

        with open(self.faculty_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = row.get('FACULTY ID', '').strip()
                fname = row.get('FACULTY NAME', '').strip()
                if fid:
                    self.faculty_by_id[fid] = fname
                    norm_key = self._normalize_name_key(fname)
                    self.faculty_by_name[norm_key] = (fid, fname)
                    # Also map exact lowercase
                    self.faculty_by_name[fname.lower()] = (fid, fname)

    def _load_attendance(self):
        self.attendance_lookup = {}
        self.faculty_months_available = defaultdict(set)
        self.all_recorded_months = set()

        if not os.path.exists(self.attendance_file):
            return

        with open(self.attendance_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                fid = row.get('FACULTY ID', '').strip()
                date_str = row.get('DATE', '').strip()
                status = row.get('ATTENDANCE STATUS', '').strip()

                if fid and date_str:
                    self.attendance_lookup[(fid, date_str)] = status
                    my = extract_month_year(date_str)
                    if my:
                        self.faculty_months_available[fid].add(my)
                        self.all_recorded_months.add(my)

    def find_faculty(self, faculty_id: Optional[str] = None, faculty_name: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """
        Attempts to match a faculty via ID then by name.
        Multi-stage name matching:
          1. Exact normalised key
          2. Case-insensitive exact
          3. Partial substring containment (>=5 chars)
          4. Token overlap (>=2 significant tokens match)
        Returns (Faculty ID, Faculty Name) or None.
        """
        if faculty_id:
            fid_clean = faculty_id.strip()
            if fid_clean in self.faculty_by_id:
                return (fid_clean, self.faculty_by_id[fid_clean])

        if faculty_name:
            fname_clean = faculty_name.strip()
            norm_key = self._normalize_name_key(fname_clean)

            # Stage 1: exact normalised key
            if norm_key in self.faculty_by_name:
                return self.faculty_by_name[norm_key]

            # Stage 2: case-insensitive exact
            if fname_clean.lower() in self.faculty_by_name:
                return self.faculty_by_name[fname_clean.lower()]

            # Stage 3: substring containment (handles abbreviated names)
            for key, (fid, official_name) in self.faculty_by_name.items():
                if norm_key and len(norm_key) >= 5:
                    if norm_key in key or (len(key) >= 5 and key in norm_key):
                        return (fid, official_name)

            # Stage 4: token overlap (handles "Shilpa Chaudari" → "Shilpa Shashikant Chaudhari")
            input_tokens = set(
                t for t in re.sub(r'[^a-z ]', '', fname_clean.lower()).split()
                if len(t) >= 3
            )
            if len(input_tokens) >= 1:
                best_match = None
                best_score = 0
                for key, (fid, official_name) in self.faculty_by_name.items():
                    master_tokens = set(
                        t for t in re.sub(r'[^a-z ]', '', official_name.lower()).split()
                        if len(t) >= 3
                    )
                    overlap = len(input_tokens & master_tokens)
                    # Require at least 2 token matches, or 1 if the token is long (>=6 chars)
                    long_overlap = len([t for t in (input_tokens & master_tokens) if len(t) >= 6])
                    if overlap >= 2 or long_overlap >= 1:
                        score = overlap + long_overlap
                        if score > best_score:
                            best_score = score
                            best_match = (fid, official_name)
                if best_match:
                    return best_match

            # Stage 5: Fuzzy character matching (handles OCR character/spacing glitches e.g. "Aks habhaKamath" → "Akshatha Kamath")
            import difflib
            best_fuzzy_match = None
            best_fuzzy_ratio = 0.0
            norm_input = re.sub(r'[^a-z]', '', fname_clean.lower())
            norm_input = re.sub(r'^(dr|prof|mr|ms|mrs)', '', norm_input)
            if len(norm_input) >= 4:
                for key, (fid, official_name) in self.faculty_by_name.items():
                    norm_target = re.sub(r'[^a-z]', '', official_name.lower())
                    norm_target = re.sub(r'^(dr|prof|mr|ms|mrs)', '', norm_target)
                    ratio = difflib.SequenceMatcher(None, norm_input, norm_target).ratio()
                    if ratio >= 0.70 and ratio > best_fuzzy_ratio:
                        best_fuzzy_ratio = ratio
                        best_fuzzy_match = (fid, official_name)
                if best_fuzzy_match:
                    return best_fuzzy_match

        return None


    def get_attendance(self, faculty_id: str, date_str: str) -> Optional[str]:
        """
        Returns attendance status for a faculty on a given date (DD/MM/YYYY),
        or None if no record exists.
        """
        return self.attendance_lookup.get((faculty_id.strip(), date_str.strip()))

    def is_month_available(self, faculty_id: str, month_year: str) -> bool:
        """
        Checks if attendance data exists for this faculty (or institutionally)
        for the given month (MM/YYYY).
        """
        # Checks if faculty has records in this month
        return month_year in self.faculty_months_available.get(faculty_id.strip(), set())

    def get_certificate_tracker_rows(self) -> List[Dict[str, str]]:
        """
        Loads all certificate records from certificate_tracker.csv.
        """
        if not os.path.exists(self.tracker_file):
            return []
        with open(self.tracker_file, mode='r', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def find_matching_tracker_record(
        self,
        faculty_id: Optional[str] = None,
        faculty_name: Optional[str] = None,
        institution: Optional[str] = None,
        program_name: Optional[str] = None,
        filename: Optional[str] = None,
        raw_text: Optional[str] = None,
        cert_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        Cross-references an uploaded certificate against certificate_tracker.csv
        to ensure consistency with institutional dataset records.

        Priority order:
        1. Exact Certificate ID match (from explicit ID, filename, or raw OCR)
        2. Google Drive file ID match (from certificate link vs filename / text)
        3. Faculty candidate filtering + keyword & date scoring (program, institution, dates)
        """
        tracker_rows = self.get_certificate_tracker_rows()
        if not tracker_rows:
            return None

        filename_str = filename or ""
        raw_text_str = raw_text or ""
        filename_lower = filename_str.lower()
        text_lower = raw_text_str.lower()
        combined_text = f"{filename_str} {raw_text_str}"

        # 1. Certificate ID matching
        target_cids = set()
        if cert_id:
            target_cids.add(cert_id.strip().upper())
        found_cids = re.findall(r'CERT-\d+', combined_text, re.IGNORECASE)
        for cid in found_cids:
            target_cids.add(cid.strip().upper())

        if target_cids:
            for row in tracker_rows:
                row_cid = row.get("CERTIFICATE ID", "").strip().upper()
                if row_cid in target_cids:
                    return row

        # 2. Source / Google Drive Link matching
        for row in tracker_rows:
            link = row.get("CERTIFICATE LINK", "").strip()
            if not link:
                continue
            # Extract Drive file ID if present (e.g., id=1XXMet48... or /d/1XXMet48...)
            drive_id_match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', link) or re.search(r'/d/([a-zA-Z0-9_-]+)', link)
            if drive_id_match:
                drive_file_id = drive_id_match.group(1)
                if len(drive_file_id) >= 8 and (drive_file_id in filename_str or drive_file_id in raw_text_str):
                    return row

        # 3. Filter candidate rows by faculty if available
        candidates = []
        fid_clean = (faculty_id or "").strip().upper()
        fname_clean = (faculty_name or "").strip().lower()

        for r in tracker_rows:
            row_fid = r.get("FACULTY ID", "").strip().upper()
            row_fname = r.get("FACULTY NAME", "").strip().lower()
            if fid_clean and row_fid == fid_clean:
                candidates.append(r)
            elif fname_clean and (fname_clean in row_fname or row_fname in fname_clean):
                candidates.append(r)

        if not candidates:
            candidates = tracker_rows

        if len(candidates) == 1 and fid_clean and candidates[0].get("FACULTY ID") == fid_clean:
            return candidates[0]

        # 4. Score candidates by filename, institution, program title, dates, and text
        best_row = None
        best_score = 0

        inst_lower = (institution or "").lower()
        prog_lower = (program_name or "").lower()
        norm_input_inst = normalize_institution(institution or "")
        norm_start = normalize_date_to_ddmmyyyy(start_date or "") if start_date else None
        norm_end = normalize_date_to_ddmmyyyy(end_date or "") if end_date else None

        stop_words = {'and', 'for', 'the', 'with', 'course', 'program', 'programme', 'development', 'fdp', 'workshop', 'sttp', 'bootcamp', 'training', 'hands', 'learning', 'national', 'international'}
        input_prog_tokens = set(re.findall(r'[a-z0-9]{3,}', prog_lower)) - stop_words

        for row in candidates:
            score = 0
            row_inst = row.get("PROGRAM INSTITUTION", "").lower()
            row_prog = row.get("FDP / PROGRAM NAME", "").lower()
            row_cid = row.get("CERTIFICATE ID", "").lower()
            row_norm_inst = normalize_institution(row.get("PROGRAM INSTITUTION", ""))

            # A. Explicit Certificate ID in filename or text
            if row_cid and (row_cid in filename_lower or row_cid in text_lower):
                score += 20

            # B. Program Title Keyword Overlap
            row_prog_tokens = set(re.findall(r'[a-z0-9]{3,}', row_prog)) - stop_words
            overlap = len(input_prog_tokens & row_prog_tokens)
            score += overlap * 4

            for kw in row_prog_tokens:
                if kw in filename_lower:
                    score += 3
                if kw in text_lower:
                    score += 2

            # C. Institution Matching (normalized + keyword)
            if norm_input_inst and norm_input_inst != "Unknown" and norm_input_inst == row_norm_inst:
                score += 10
            elif inst_lower and inst_lower != "unknown" and (inst_lower in row_inst or row_inst in inst_lower):
                score += 6

            for kw in re.findall(r'[a-z0-9]{3,}', row_inst):
                if kw in ['and', 'the', 'for', 'institute', 'technology', 'college', 'engineering']:
                    continue
                if kw in inst_lower or kw in filename_lower:
                    score += 4
                if kw in text_lower:
                    score += 2
                if kw in prog_lower:
                    score += 4

            # D. Dates Matching (High Reliability!)
            row_s_date = normalize_date_to_ddmmyyyy(row.get("START DATE", "")) or row.get("START DATE", "")
            row_e_date = normalize_date_to_ddmmyyyy(row.get("END DATE", "")) or row.get("END DATE", "")

            if norm_start and norm_start == row_s_date:
                score += 12
            elif row_s_date and row_s_date in text_lower:
                score += 5

            if norm_end and norm_end == row_e_date:
                score += 12
            elif row_e_date and row_e_date in text_lower:
                score += 5

            if score > best_score:
                best_score = score
                best_row = row

        if best_row and best_score >= 3:
            return best_row

        return None

    def update_certificate_tracker_row(self, cert_id: str, updates: Dict[str, str]) -> bool:
        """
        Updates a specific certificate in certificate_tracker.csv.
        """
        rows = self.get_certificate_tracker_rows()
        if not rows:
            return False

        updated = False
        fieldnames = list(rows[0].keys())
        for row in rows:
            if row.get('CERTIFICATE ID', '').strip() == cert_id.strip():
                for k, v in updates.items():
                    if k in fieldnames:
                        row[k] = str(v)
                updated = True
                break

        if updated:
            with open(self.tracker_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            return True
        return False
