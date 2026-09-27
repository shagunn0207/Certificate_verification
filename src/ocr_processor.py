import os
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from src.utils import normalize_date_to_ddmmyyyy, parse_date_flexible, normalize_institution

# Try importing PDF extraction libraries
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Try importing image libraries & pytesseract
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_PYTESSERACT = True
except ImportError:
    HAS_PYTESSERACT = False


class CertificateOCRProcessor:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """
        Initializes the OCR / document parser.
        Supports PDF extraction (pdfplumber, pypdf) and image OCR (pytesseract).
        """
        self.tesseract_available = False
        if HAS_PYTESSERACT:
            if tesseract_cmd and os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                self.tesseract_available = True
            else:
                # Check default windows paths
                common_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
                ]
                for p in common_paths:
                    if os.path.exists(p):
                        pytesseract.pytesseract.tesseract_cmd = p
                        self.tesseract_available = True
                        break

    def extract_raw_text(self, file_path_or_bytes, filename: str) -> str:
        """
        Extracts raw text from PDF or image document.
        """
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        text = ""

        if ext == 'pdf':
            # Try pdfplumber first
            if HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(file_path_or_bytes) as pdf:
                        page_texts = [page.extract_text() or '' for page in pdf.pages]
                        text = "\n".join(page_texts)
                except Exception:
                    text = ""

            # Fallback to pypdf if empty or error
            if not text.strip() and HAS_PYPDF:
                try:
                    reader = pypdf.PdfReader(file_path_or_bytes)
                    page_texts = [p.extract_text() or '' for p in reader.pages]
                    text = "\n".join(page_texts)
                except Exception:
                    text = ""

        elif ext in ['jpg', 'jpeg', 'png']:
            if HAS_PIL:
                try:
                    img = Image.open(file_path_or_bytes)
                    if self.tesseract_available and HAS_PYTESSERACT:
                        text = pytesseract.image_to_string(img)
                    else:
                        # If OCR binary not installed, check image metadata or EXIF
                        info = getattr(img, 'info', {})
                        text = " ".join([str(v) for v in info.values() if isinstance(v, str)])
                except Exception:
                    text = ""

        return text.strip()

    def parse_certificate_text(self, text: str, fallback_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extracts structured fields from raw certificate text.
        Returns:
            - FACULTY ID
            - FACULTY NAME
            - FDP / PROGRAM NAME
            - PROGRAM INSTITUTION
            - START DATE
            - END DATE
            - NUMBER OF DAYS
            - CERTIFICATE ID
            - RAW_TEXT
        """
        result = {
            "FACULTY ID": "",
            "FACULTY NAME": "",
            "FDP / PROGRAM NAME": "",
            "PROGRAM INSTITUTION": "",
            "START DATE": "",
            "END DATE": "",
            "NUMBER OF DAYS": "",
            "CERTIFICATE ID": "",
            "RAW_TEXT": text
        }

        if fallback_meta:
            for k, v in fallback_meta.items():
                if v and k in result:
                    result[k] = str(v).strip()

        if not text:
            return result

        # 1. Faculty ID extraction (e.g. F001-F032, RIT001-RIT999)
        fid_match = re.search(r'\b(F\d{3}|RIT\d{3})\b', text, re.IGNORECASE)
        if fid_match:
            result["FACULTY ID"] = fid_match.group(1).upper()

        # 2. Date Extraction
        # Patterns for date ranges: e.g. "10/09/2026 to 12/09/2026", "10/09/2026 - 12/09/2026"
        # "14 July 2025 to 18 July 2025", "July 14, 2025 to July 18, 2025"
        # "14/07/2025 - 18/07/2025"
        date_patterns = [
            # Two explicit dates with separator
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*(?:to|-|–|until)\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            # Date month year to date month year
            r'(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{2,4})\s*(?:to|-|–)\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{2,4})',
            # Month date, year to Month date, year
            r'([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{2,4})\s*(?:to|-|–)\s*([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{2,4})',
            # Same month range: "14 to 18 July 2025" or "14th - 18th July 2025"
            r'(\d{1,2}(?:st|nd|rd|th)?)\s*(?:to|-|–)\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{2,4})'
        ]

        found_start = ""
        found_end = ""

        for pat in date_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                g1, g2 = m.group(1).strip(), m.group(2).strip()
                # Check for single month range e.g. "14 to 18 July 2025"
                if re.match(r'^\d{1,2}(?:st|nd|rd|th)?$', g1):
                    month_year_part = re.sub(r'^\d{1,2}(?:st|nd|rd|th)?\s*', '', g2)
                    g1 = f"{g1} {month_year_part}"

                norm_start = normalize_date_to_ddmmyyyy(g1)
                norm_end = normalize_date_to_ddmmyyyy(g2)
                if norm_start and norm_end:
                    found_start = norm_start
                    found_end = norm_end
                    break

        # If not found as range, find all individual dates
        if not found_start:
            all_dates = []
            # Match numeric dates
            num_dates = re.findall(r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b', text)
            for d in num_dates:
                nd = normalize_date_to_ddmmyyyy(d)
                if nd and nd not in all_dates:
                    all_dates.append(nd)

            # Match text dates
            txt_dates = re.findall(r'\b\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s+\d{4}\b', text)
            for d in txt_dates:
                nd = normalize_date_to_ddmmyyyy(d)
                if nd and nd not in all_dates:
                    all_dates.append(nd)

            if len(all_dates) >= 2:
                # Chronological sort
                parsed = [(parse_date_flexible(d), d) for d in all_dates if parse_date_flexible(d)]
                parsed.sort(key=lambda x: x[0])
                found_start = parsed[0][1]
                found_end = parsed[-1][1]
            elif len(all_dates) == 1:
                found_start = all_dates[0]
                found_end = all_dates[0]

        if found_start and not result.get("START DATE"):
            result["START DATE"] = found_start
        if found_end and not result.get("END DATE"):
            result["END DATE"] = found_end

        # Calculate number of days if start and end exist
        if result["START DATE"] and result["END DATE"] and not result.get("NUMBER OF DAYS"):
            dt1 = parse_date_flexible(result["START DATE"])
            dt2 = parse_date_flexible(result["END DATE"])
            if dt1 and dt2 and dt2 >= dt1:
                result["NUMBER OF DAYS"] = str((dt2 - dt1).days + 1)

        # 3. Faculty Name Extraction
        if not result.get("FACULTY NAME"):
            name_pats = [
                r'(?:certified that|certify that|presented to|awarded to|this is to certify that)\s+(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)?\s*([A-Z][a-zA-Z\.\s]{2,30})',
                r'\b(Dr\.\s+[A-Z][a-zA-Z\s\.]+)\b',
                r'\b(Prof\.\s+[A-Z][a-zA-Z\s\.]+)\b'
            ]
            for p in name_pats:
                nm = re.search(p, text, re.IGNORECASE)
                if nm:
                    candidate = nm.group(1).strip().split('\n')[0].strip()
                    # Filter out institution names mistakenly matched
                    if "institute" not in candidate.lower() and "college" not in candidate.lower() and len(candidate) > 2:
                        result["FACULTY NAME"] = candidate
                        break

        # 4. FDP / Program Name Extraction
        if not result.get("FDP / PROGRAM NAME"):
            fdp_pats = [
                r'(?:participated in|attended|completion of|for the)\s+(?:the\s+)?(?:FDP on|one week FDP on|workshop on|Faculty Development Program on|short term training program on|STTP on)\s*["“]?([^"\n\.,]{5,100})["”]?',
                r'(?:Faculty Development Program on|FDP on|Workshop on)\s*["“]?([^"\n\.,]{5,100})["”]?',
                r'["“]([^"”\n]{8,80}(?:AI|Analytics|Learning|Technologies|Computing|Innovations|Systems|Intelligence|Development|Bootcamp)[^"”\n]*)["”]'
            ]
            for p in fdp_pats:
                fm = re.search(p, text, re.IGNORECASE)
                if fm:
                    result["FDP / PROGRAM NAME"] = fm.group(1).strip()
                    break

        # 5. Program Institution Extraction
        if not result.get("PROGRAM INSTITUTION"):
            inst_pats = [
                r'(?:organized by|conducted by|held at|jointly organized by|venue:)\s*["“]?([^\n,\.]{4,80}(?:Institute|College|University|Academy|Campus|School|Council|TCS|SwipeGen|BITS|NIT|IIT)[^\n\.]*)',
                r'\b(Ramaiah Institute of Technology|MSRIT|RIT|M\.S\.\s*Ramaiah Institute of Technology)\b',
                r'\b(NIT[\s,]+[A-Za-z]+|BITS Pilani[A-Za-z\s]*|IIT[\s,]+[A-Za-z]+|IIIT[\s,]+[A-Za-z]+|BMS College of Engineering)\b'
            ]
            for p in inst_pats:
                im = re.search(p, text, re.IGNORECASE)
                if im:
                    candidate_inst = im.group(1).strip()
                    result["PROGRAM INSTITUTION"] = normalize_institution(candidate_inst)
                    break

        # 6. Certificate ID extraction
        if not result.get("CERTIFICATE ID"):
            cid_match = re.search(r'\b(CERT[-\s]?\d{3}|[A-Z0-9]{8,16})\b', text)
            if cid_match:
                result["CERTIFICATE ID"] = cid_match.group(1).strip()

        return result
