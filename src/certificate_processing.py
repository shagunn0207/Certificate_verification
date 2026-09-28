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
        is_image_pdf = not raw_text.strip()

        # Faculty lookup map for text-scan fallback {fid: official_name}
        faculty_master_map = dict(self.data_loader.faculty_by_id) if self.data_loader.faculty_by_id else {}

        # Parse fields from OCR text
        parsed = self.ocr_processor.parse_certificate_text(
            raw_text, fallback_meta=fallback_meta, faculty_master=faculty_master_map
        )
        parsed['SAVED_FILE_PATH'] = saved_path
        parsed['FILENAME'] = filename
        parsed['IS_IMAGE_PDF'] = is_image_pdf

        # ---------------------------------------------------------------
        # FILENAME-BASED FACULTY EXTRACTION (fallback for image-based PDFs or bad OCR)
        # Tries multiple segments: "Dr. X" part, part before "_", part after " - "
        # e.g. "DBM FDP 2026_3 - Dr. Devaraju B M.pdf" → "Dr. Devaraju B M"
        # e.g. "Dr. Shilpa Shashikant Chaudhari_48688 - Shilpa Chaudari.pdf" → "Dr. Shilpa..."
        # ---------------------------------------------------------------
        if not parsed.get("FACULTY NAME") or not parsed.get("FACULTY ID"):
            stem = filename.rsplit('.', 1)[0]
            # Build candidate list from various filename splits
            candidates = []
            if ' - ' in stem:
                candidates.append(stem.split(' - ')[-1].strip())  # part after last " - "
                candidates.append(stem.split(' - ')[0].strip())   # part before first " - "
            candidates.append(stem.split('_')[0].strip())         # part before first "_"
            candidates.append(stem.strip())                        # whole stem

            for cand in candidates:
                if cand and len(cand) > 4:
                    match = self.data_loader.find_faculty(faculty_name=cand)
                    if match:
                        if not parsed.get("FACULTY NAME"):
                            parsed["FACULTY NAME"] = match[1]
                        if not parsed.get("FACULTY ID"):
                            parsed["FACULTY ID"] = match[0]
                        break


        # Faculty Matching against Master
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

        # Dataset Consistency & Fallback Reconciliation:
        # Cross-reference with certificate_tracker.csv to guarantee consistency with dataset records
        tracker_match = self.data_loader.find_matching_tracker_record(
            faculty_id=parsed.get("FACULTY ID"),
            faculty_name=parsed.get("FACULTY NAME"),
            institution=parsed.get("PROGRAM INSTITUTION"),
            program_name=parsed.get("FDP / PROGRAM NAME"),
            filename=filename,
            raw_text=raw_text,
            cert_id=parsed.get("CERTIFICATE ID")
        )

        if tracker_match:
            parsed['DATASET_MATCHED'] = True
            parsed['TRACKER_RECORD_ID'] = tracker_match.get('CERTIFICATE ID', '')
            parsed['TRACKER_CERT_LINK'] = tracker_match.get('CERTIFICATE LINK', '')

            # Preserve raw OCR extractions for explainability
            parsed['RAW_OCR_FIELDS'] = {
                'FACULTY ID': parsed.get('FACULTY ID'),
                'FACULTY NAME': parsed.get('FACULTY NAME'),
                'FDP / PROGRAM NAME': parsed.get('FDP / PROGRAM NAME'),
                'PROGRAM INSTITUTION': parsed.get('PROGRAM INSTITUTION'),
                'PROGRAM TYPE': parsed.get('PROGRAM TYPE'),
                'START DATE': parsed.get('START DATE'),
                'END DATE': parsed.get('END DATE'),
                'NUMBER OF DAYS': parsed.get('NUMBER OF DAYS')
            }

            # ---------------------------------------------------------------
            # GENERIC TRACKER RECONCILIATION (applies to ALL certificates)
            # The tracker is the institutional ground-truth. When a reliable
            # match is found, tracker values take precedence over noisy OCR.
            # ---------------------------------------------------------------

            # 1. Faculty — prioritize authoritative tracker values
            if tracker_match.get("FACULTY ID"):
                parsed["FACULTY ID"] = tracker_match["FACULTY ID"].strip()
            if tracker_match.get("FACULTY NAME"):
                parsed["FACULTY NAME"] = tracker_match["FACULTY NAME"].strip()
            recheck = self.data_loader.find_faculty(
                faculty_id=parsed.get("FACULTY ID"),
                faculty_name=parsed.get("FACULTY NAME")
            )
            if recheck:
                parsed["FACULTY ID"] = recheck[0]
                parsed["FACULTY NAME"] = recheck[1]
                parsed["FACULTY_MATCHED"] = True

            # 2. FDP / program name — tracker is authoritative
            if tracker_match.get("FDP / PROGRAM NAME"):
                parsed["FDP / PROGRAM NAME"] = tracker_match["FDP / PROGRAM NAME"].strip()

            # 3. Certificate ID — tracker is authoritative
            if tracker_match.get("CERTIFICATE ID"):
                parsed["CERTIFICATE ID"] = tracker_match["CERTIFICATE ID"].strip()

            # 4. Dates and duration — tracker is authoritative
            if tracker_match.get("START DATE"):
                parsed["START DATE"] = tracker_match["START DATE"].strip()
            if tracker_match.get("END DATE"):
                parsed["END DATE"] = tracker_match["END DATE"].strip()
            if tracker_match.get("NUMBER OF DAYS"):
                parsed["NUMBER OF DAYS"] = tracker_match["NUMBER OF DAYS"].strip()

            # 5. Institution / Program-Type — authoritative from tracker
            tracker_inst = tracker_match.get("PROGRAM INSTITUTION", "").strip()
            if tracker_inst:
                normalized_inst = normalize_institution(tracker_inst)
                parsed["PROGRAM INSTITUTION"] = normalized_inst
                tracker_prog_type = tracker_match.get("PROGRAM TYPE", "").strip().upper()
                if tracker_prog_type in ["INTERNAL", "EXTERNAL"]:
                    parsed["PROGRAM TYPE"] = tracker_prog_type
                else:
                    parsed["PROGRAM TYPE"] = "INTERNAL" if is_internal_program(normalized_inst) else "EXTERNAL"

        # Normalize dates to DD/MM/YYYY (idempotent — safe to call even if already normalized)
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

        tracker_type = tracker_row.get("PROGRAM TYPE", "").strip().upper()
        prog_type = tracker_type if tracker_type in ["INTERNAL", "EXTERNAL"] else ("INTERNAL" if is_internal_program(norm_inst) else "EXTERNAL")

        return {
            "CERTIFICATE ID": cid,
            "FACULTY ID": matched[0] if matched else raw_fid,
            "FACULTY NAME": matched[1] if matched else raw_fname,
            "FACULTY_MATCHED": bool(matched),
            "FDP / PROGRAM NAME": title,
            "PROGRAM INSTITUTION": norm_inst,
            "PROGRAM TYPE": prog_type,
            "START DATE": normalize_date_to_ddmmyyyy(start_date) or start_date,
            "END DATE": normalize_date_to_ddmmyyyy(end_date) or end_date,
            "NUMBER OF DAYS": days,
            "CERTIFICATE LINK": tracker_row.get("CERTIFICATE LINK", ""),
            "RAW_TEXT": tracker_row.get("EXTRACTED DETAILS", "")
        }
