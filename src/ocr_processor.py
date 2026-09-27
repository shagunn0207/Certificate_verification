import os
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from src.utils import normalize_date_to_ddmmyyyy, parse_date_flexible, normalize_institution

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


def _clean_text(raw: str) -> Tuple[str, str]:
    """
    Returns (flat_text, cleaned_raw_text):
    - flat_text: single-line, whitespace-normalised, unicode-chars stripped
    - cleaned_raw: newlines preserved but unicode chars stripped
    """
    cleaned = raw.replace('\ufffd', '-')
    cleaned = re.sub(r'[\u2013\u2014\u2015\u2018\u2019\u201c\u201d\u00ab\u00bb]', '"', cleaned)
    flat = re.sub(r'[\r\n]+', ' ', cleaned)
    flat = re.sub(r'\s+', ' ', flat).strip()
    return flat, cleaned


class CertificateOCRProcessor:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.tesseract_available = False
        if HAS_PYTESSERACT:
            if tesseract_cmd and os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                self.tesseract_available = True
            else:
                common_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
                ]
                for p in common_paths:
                    if os.path.exists(p):
                        pytesseract.pytesseract.tesseract_cmd = p
                        self.tesseract_available = True
                        break

    # ------------------------------------------------------------------
    # TEXT EXTRACTION
    # ------------------------------------------------------------------

    def extract_raw_text(self, file_path_or_bytes, filename: str) -> str:
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        text = ""

        if ext == 'pdf':
            if HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(file_path_or_bytes) as pdf:
                        text = "\n".join(page.extract_text() or '' for page in pdf.pages)
                except Exception:
                    text = ""

            if not text.strip() and HAS_PYPDF:
                try:
                    reader = pypdf.PdfReader(file_path_or_bytes)
                    text = "\n".join(p.extract_text() or '' for p in reader.pages)
                except Exception:
                    text = ""

        elif ext in ['jpg', 'jpeg', 'png']:
            if HAS_PIL:
                try:
                    img = Image.open(file_path_or_bytes)
                    if self.tesseract_available and HAS_PYTESSERACT:
                        text = pytesseract.image_to_string(img)
                    else:
                        info = getattr(img, 'info', {})
                        text = " ".join(str(v) for v in info.values() if isinstance(v, str))
                except Exception:
                    text = ""

        return text.strip()

    # ------------------------------------------------------------------
    # STRUCTURED PARSING
    # ------------------------------------------------------------------

    def parse_certificate_text(
        self,
        text: str,
        fallback_meta: Optional[Dict[str, Any]] = None,
        faculty_master: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Extracts structured fields from raw certificate text.
        faculty_master: {fid: official_name} for text-scan fallback matching.
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
            "RAW_TEXT": text,
        }

        if fallback_meta:
            for k, v in fallback_meta.items():
                if v and k in result:
                    result[k] = str(v).strip()

        if not text:
            return result

        flat, cleaned_raw = _clean_text(text)
        # Normalise dashes so all date regexes work with plain hyphen
        flat = flat.replace('\u2013', '-').replace('\u2014', '-')

        # ==============================================================
        # 1. FACULTY ID
        # ==============================================================
        if not result["FACULTY ID"]:
            m = re.search(r'\b(F\d{3}|RIT\d{3})\b', flat, re.IGNORECASE)
            if m:
                result["FACULTY ID"] = m.group(1).upper()

        # ==============================================================
        # 2. DATE RANGE
        # ==============================================================
        found_start, found_end = result["START DATE"], result["END DATE"]

        if not found_start or not found_end:
            # Pattern 0 (HIGHEST PRIORITY): "Month D1 - D2, YYYY"  e.g. "July 14 - 25, 2025"
            m = re.search(
                r'([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?\s*[-]\s*(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})',
                flat, re.IGNORECASE
            )
            if m:
                mon, d1, d2, yr = m.group(1), m.group(2), m.group(3), m.group(4)
                ns = normalize_date_to_ddmmyyyy(f"{d1} {mon} {yr}")
                ne = normalize_date_to_ddmmyyyy(f"{d2} {mon} {yr}")
                if ns and ne:
                    found_start, found_end = ns, ne

        if not found_start or not found_end:
            # Pattern A: "from 14th July to 25th July, 2025"
            m = re.search(
                r'(?:from|dated)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+(?:\s+\d{4})?)'
                r'\s*(?:to|-{1,2}|–)\s*'
                r'(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4})',
                flat, re.IGNORECASE
            )
            if m:
                g1, g2 = m.group(1).strip(), m.group(2).strip()
                if not re.search(r'\d{4}', g1):
                    yr_match = re.search(r'\d{4}', g2)
                    if yr_match:
                        g1 = f"{g1} {yr_match.group()}"
                ns, ne = normalize_date_to_ddmmyyyy(g1), normalize_date_to_ddmmyyyy(g2)
                if ns and ne:
                    found_start, found_end = ns, ne

        if not found_start or not found_end:
            # Pattern B: "July 14 to July 25, 2025"
            m = re.search(
                r'([A-Za-z]+)\s+(\d{1,2}(?:st|nd|rd|th)?)\s*(?:to|-|–)\s*'
                r'([A-Za-z]+\s+)?(\d{1,2}(?:st|nd|rd|th)?),?\s*(\d{4})',
                flat, re.IGNORECASE
            )
            if m:
                mon1, d1, mon2_opt, d2, yr = m.groups()
                mon2 = mon2_opt.strip() if mon2_opt else mon1
                ns = normalize_date_to_ddmmyyyy(f"{d1} {mon1} {yr}")
                ne = normalize_date_to_ddmmyyyy(f"{d2} {mon2} {yr}")
                if ns and ne:
                    found_start, found_end = ns, ne

        if not found_start or not found_end:
            # Pattern C: numeric DD/MM/YYYY - DD/MM/YYYY
            m = re.search(
                r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*(?:to|-|–)\s*'
                r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                flat, re.IGNORECASE
            )
            if m:
                ns = normalize_date_to_ddmmyyyy(m.group(1))
                ne = normalize_date_to_ddmmyyyy(m.group(2))
                if ns and ne:
                    found_start, found_end = ns, ne

        if not found_start or not found_end:
            all_dates = []
            for pat in [
                r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b',
                r'\b\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s+\d{4}\b',
            ]:
                for d in re.findall(pat, flat):
                    nd = normalize_date_to_ddmmyyyy(d)
                    if nd and nd not in all_dates:
                        all_dates.append(nd)

            if len(all_dates) >= 2:
                parsed = sorted(
                    [(parse_date_flexible(d), d) for d in all_dates if parse_date_flexible(d)],
                    key=lambda x: x[0]
                )
                found_start, found_end = parsed[0][1], parsed[-1][1]
            elif len(all_dates) == 1:
                found_start = found_end = all_dates[0]

        if found_start:
            result["START DATE"] = found_start
        if found_end:
            result["END DATE"] = found_end

        if result["START DATE"] and result["END DATE"] and not result["NUMBER OF DAYS"]:
            dt1 = parse_date_flexible(result["START DATE"])
            dt2 = parse_date_flexible(result["END DATE"])
            if dt1 and dt2 and dt2 >= dt1:
                result["NUMBER OF DAYS"] = str((dt2 - dt1).days + 1)

        # ==============================================================
        # 3. FACULTY NAME
        # ==============================================================
        if not result["FACULTY NAME"]:
            for pat in [
                r'(?:certified that|certify that|presented to|awarded to)\s+(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)?\s*([A-Z][a-zA-Z\. ]{2,35})',
                r'\b(Dr\.\s+[A-Z][a-zA-Z\s\.]{1,28})\b',
                r'\b(Prof\.\s+[A-Z][a-zA-Z\s\.]{1,28})\b',
            ]:
                m = re.search(pat, flat, re.IGNORECASE)
                if m:
                    cand = m.group(1).strip()
                    if "institute" not in cand.lower() and "college" not in cand.lower() and len(cand) > 2:
                        result["FACULTY NAME"] = cand
                        break

        # Master-list text scan fallback
        if faculty_master and not result["FACULTY NAME"]:
            flat_lower = flat.lower()
            for fid, official_name in faculty_master.items():
                check = official_name.lower().replace('dr.', '').replace('.', '').strip()
                if check and check in flat_lower:
                    result["FACULTY NAME"] = official_name
                    if not result["FACULTY ID"]:
                        result["FACULTY ID"] = fid
                    break

        # ==============================================================
        # 4. FDP / PROGRAM NAME
        # ==============================================================
        if not result["FDP / PROGRAM NAME"]:
            m = re.search(
                r'(?:Program|Programme|FDP|Workshop|STTP)\s+on\s+'
                r'["\-]?\s*([^"\-\n]{5,120}?)\s*["\-]?\s+'
                r'organized by',
                flat, re.IGNORECASE
            )
            if m:
                result["FDP / PROGRAM NAME"] = m.group(1).strip(" -\"'")

        if not result["FDP / PROGRAM NAME"]:
            m = re.search(
                r'(?:Faculty Development Programme on|Faculty Development Program on'
                r'|FDP on|Workshop on|STTP on)\s*["\-]?\s*([^"\n]{5,120})',
                flat, re.IGNORECASE
            )
            if m:
                title = m.group(1).strip(" -\"'")
                title = re.split(r'\s*(?:organized by|conducted by|July|August|from \d)', title, flags=re.IGNORECASE)[0]
                result["FDP / PROGRAM NAME"] = title.strip()

        if not result["FDP / PROGRAM NAME"]:
            m = re.search(
                r'(?:Two-weeks|One-Week|One Week|Two Weeks|Five Days?|5-Day)\s+'
                r'Faculty Development Prog[a-z]*\s+on\s+["\-]?\s*([^"\n]{5,120})',
                flat, re.IGNORECASE
            )
            if m:
                result["FDP / PROGRAM NAME"] = m.group(1).strip(" -\"'")

        # ==============================================================
        # 5. PROGRAM INSTITUTION
        # ==============================================================
        if not result["PROGRAM INSTITUTION"]:
            m = re.search(
                r'organized by\s+([^,\.]{4,80}(?:NIT|BITS|IIT|IIIT|College|Institute'
                r'|University|Academy|TCS|SwipeGen|RVITM)[^,\.]*)',
                flat, re.IGNORECASE
            )
            if m:
                raw_org = m.group(1).strip()
                inst_tok = re.search(
                    r'(NIT[\s,]+[A-Za-z]+|BITS Pilani[\w\s]*|IIT[\s,]+[A-Za-z]+'
                    r'|IIIT[\s,]+[A-Za-z]+|BMS College of Engineering'
                    r'|Ramaiah Institute of Technology|MSRIT|RIT)',
                    raw_org, re.IGNORECASE
                )
                result["PROGRAM INSTITUTION"] = normalize_institution(
                    inst_tok.group(1) if inst_tok else raw_org
                )

        if not result["PROGRAM INSTITUTION"]:
            for pat in [
                r'\b(NIT[\s,]+[A-Za-z]+|National Institute of Technology[\s,]+[A-Za-z]+)\b',
                r'\b(BITS Pilani[\w\s]*|IIT[\s,]+[A-Za-z]+|IIIT[\s,]+[A-Za-z]+|BMS College of Engineering)\b',
                r'\b(Ramaiah Institute of Technology|MSRIT|RIT|M\.S\.\s*Ramaiah Institute of Technology)\b',
            ]:
                m = re.search(pat, flat, re.IGNORECASE)
                if m:
                    result["PROGRAM INSTITUTION"] = normalize_institution(m.group(1).strip())
                    break

        # ==============================================================
        # 6. CERTIFICATE ID
        # ==============================================================
        if not result["CERTIFICATE ID"]:
            m = re.search(r'\b(CERT[-\s]?\d{3,4})\b', flat, re.IGNORECASE)
            if m:
                result["CERTIFICATE ID"] = m.group(1).strip()
            else:
                m = re.search(r'Ref\.?\s*No[:.]\s*([A-Za-z0-9\/\-]+)', flat)
                if m:
                    result["CERTIFICATE ID"] = m.group(1).strip()

        return result
