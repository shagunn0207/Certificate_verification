import os
import shutil
from typing import Dict, Any, Optional
from src.utils import (
    is_valid_file_extension,
    normalize_date_to_ddmmyyyy,
    normalize_institution,
    is_internal_program,
    generate_date_range
)
from src.data_loader import DataLoader
from src.ocr_processor import CertificateOCRProcessor

class CertificateProcessor:
    def __init__(self, data_loader: DataLoader, upload_dir: Optional[str] = None):
        self.data_loader = data_loader
        self.ocr_processor = CertificateOCRProcessor()

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.upload_dir = upload_dir or os.path.join(base_dir, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

    def process_uploaded_file(self, file_bytes: bytes, filename: str, fallback_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes an uploaded certificate file:
        1. Validates extension.
        2. Saves locally to uploads/ directory.
        3. Extracts raw text via OCR.
        4. Parses structured fields.
        5. Matches faculty against Faculty Master.
        6. Classifies Internal/External program type.
        """
        if not is_valid_file_extension(filename):
            raise ValueError("Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG certificate.")

        # Save to uploads/
        saved_path = os.path.join(self.upload_dir, filename)
        with open(saved_path, 'wb') as f:
            f.write(file_bytes)

        # OCR / Text extraction
        raw_text = self.ocr_processor.extract_raw_text(saved_path, filename)
        
        # Parse fields
        parsed = self.ocr_processor.parse_certificate_text(raw_text, fallback_meta=fallback_meta)
        parsed['SAVED_FILE_PATH'] = saved_path
        parsed['FILENAME'] = filename

        # Faculty Matching
        raw_fid = parsed.get("FACULTY ID", "").strip()
        raw_fname = parsed.get("FACULTY NAME", "").strip()

        matched_faculty = self.data_loader.find_faculty(faculty_id=raw_fid, faculty_name=raw_fname)
        if matched_faculty:
            parsed['FACULTY ID'] = matched_faculty[0]
            parsed['FACULTY NAME'] = matched_faculty[1]
            parsed['FACULTY_MATCHED'] = True
        else:
            parsed['FACULTY_MATCHED'] = False

        # Normalize Institution and Internal/External classification
        inst = parsed.get("PROGRAM INSTITUTION", "").strip()
        normalized_inst = normalize_institution(inst) if inst else "Unknown"
        parsed['PROGRAM INSTITUTION'] = normalized_inst
        parsed['PROGRAM TYPE'] = "INTERNAL" if is_internal_program(normalized_inst) else "EXTERNAL"

        # Normalize dates
        if parsed.get("START DATE"):
            parsed["START DATE"] = normalize_date_to_ddmmyyyy(parsed["START DATE"]) or parsed["START DATE"]
        if parsed.get("END DATE"):
            parsed["END DATE"] = normalize_date_to_ddmmyyyy(parsed["END DATE"]) or parsed["END DATE"]

        return parsed

    def process_existing_record(self, tracker_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts a row from certificate_tracker.csv into the standardized certificate structure
        for verification.
        """
        raw_fid = tracker_row.get("FACULTY ID", "").strip()
        raw_fname = tracker_row.get("FACULTY NAME", "").strip()
        inst = tracker_row.get("PROGRAM INSTITUTION", "").strip()
        start_date = tracker_row.get("START DATE", "").strip()
        end_date = tracker_row.get("END DATE", "").strip()
        days = tracker_row.get("NUMBER OF DAYS", "").strip()
        cid = tracker_row.get("CERTIFICATE ID", "").strip()
        title = tracker_row.get("FDP / PROGRAM NAME", "").strip()

        matched = self.data_loader.find_faculty(faculty_id=raw_fid, faculty_name=raw_fname)
        norm_inst = normalize_institution(inst)

        return {
            "CERTIFICATE ID": cid,
            "FACULTY ID": matched[0] if matched else raw_fid,
            "FACULTY NAME": matched[1] if matched else raw_fname,
            "FACULTY_MATCHED": bool(matched),
            "FDP / PROGRAM NAME": title,
            "PROGRAM INSTITUTION": norm_inst,
            "PROGRAM TYPE": "INTERNAL" if is_internal_program(norm_inst) else "EXTERNAL",
            "START DATE": normalize_date_to_ddmmyyyy(start_date) or start_date,
            "END DATE": normalize_date_to_ddmmyyyy(end_date) or end_date,
            "NUMBER OF DAYS": days,
            "CERTIFICATE LINK": tracker_row.get("CERTIFICATE LINK", ""),
            "RAW_TEXT": tracker_row.get("EXTRACTED DETAILS", "")
        }
