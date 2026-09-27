import os
import csv
import re
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from src.utils import extract_month_year

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
