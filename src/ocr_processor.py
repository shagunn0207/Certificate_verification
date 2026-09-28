import os
import io
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
    import pypdfium2 as pdfium
    HAS_PDFIUM = True
except ImportError:
    HAS_PDFIUM = False

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_RAPIDOCR = True
except ImportError:
    HAS_RAPIDOCR = False

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
        self.rapid_ocr = None
        if HAS_RAPIDOCR:
            try:
                self.rapid_ocr = RapidOCR()
            except Exception:
                self.rapid_ocr = None

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

    def _ocr_image(self, img) -> str:
        """
        Extracts text from an image (PIL Image, numpy array, or bytes)
        using RapidOCR (preferred) with fallback to pytesseract.
        """
        if self.rapid_ocr:
            try:
                import numpy as np
                if hasattr(img, 'convert'):
                    arr = np.array(img.convert('RGB'))
                else:
                    arr = np.array(img)
                res, _ = self.rapid_ocr(arr)
                if res:
                    return "\n".join(line[1] for line in res if line and len(line) > 1)
            except Exception:
                pass

        if self.tesseract_available and HAS_PYTESSERACT:
            try:
                return pytesseract.image_to_string(img).strip()
            except Exception:
                pass

        return ""

    # ------------------------------------------------------------------
    # TEXT EXTRACTION
    # ------------------------------------------------------------------

    def extract_raw_text(self, file_path_or_bytes, filename: str) -> str:
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        text = ""

        if ext == 'pdf':
            # 1. Try digital text extraction with pdfplumber
            if HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(file_path_or_bytes) as pdf:
                        text = "\n".join(page.extract_text() or '' for page in pdf.pages)
                except Exception:
                    text = ""

            # 2. Fallback to pypdf for digital text
            if not text.strip() and HAS_PYPDF:
                try:
                    reader = pypdf.PdfReader(file_path_or_bytes)
                    text = "\n".join(p.extract_text() or '' for p in reader.pages)
                except Exception:
                    text = ""

            # 3. If digital text is empty, it's a scanned/image PDF!
            # Render pages with pypdfium2 and OCR with RapidOCR
            if not text.strip() and HAS_PDFIUM:
                try:
                    doc = pdfium.PdfDocument(file_path_or_bytes)
                    pages_text = []
                    for page in doc:
                        pil_img = page.render(scale=2).to_pil()
                        page_ocr = self._ocr_image(pil_img)
                        if page_ocr:
                            pages_text.append(page_ocr)
                    text = "\n".join(pages_text)
                except Exception:
                    pass

        elif ext in ['jpg', 'jpeg', 'png']:
            if HAS_PIL:
                try:
                    if isinstance(file_path_or_bytes, bytes):
                        img = Image.open(io.BytesIO(file_path_or_bytes))
                    else:
                        img = Image.open(file_path_or_bytes)
                    text = self._ocr_image(img)
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
        # OCR digit correction: lowercase 'l' misread as '1' in date strings
        flat = re.sub(r'\bl(\d)', r'1\1', flat)
        # OCR ordinal correction: superscript misread as " " / # / h after digit
        # e.g. '14"' → '14', '2#' → '2', '6h ' → '6 ', '2nd' ordinals kept as-is
        flat = re.sub(r'(\d+)["\u201d\u2019]([\s-])', r'\1\2', flat)
        flat = re.sub(r'(\d+)["\u201d\u2019](-)', r'\1\2', flat)
        flat = re.sub(r'(\d+)#(\s)', r'\1\2', flat)       # "2# " → "2 "
        flat = re.sub(r'(\d+)h(\s)', r'\1\2', flat)       # "6h " → "6 "
        flat = re.sub(r'(\d+)h(-)', r'\1\2', flat)        # "6h-" → "6-"

        # OCR month misread correction: common OCR character confusions in month names
        month_ocr_fixes = [
            (r'\bFune\b', 'June'),
            (r'\bIune\b', 'June'),
            (r'\bTuly\b', 'July'),
            (r'\bIuly\b', 'July'),
            (r'\bTanuary\b', 'January'),
            (r'\bIanuary\b', 'January'),
            (r'\b0ctober\b', 'October'),
            (r'\b0ct\b', 'Oct'),
            (r'\bAupust\b', 'August'),
            (r'\bAuqust\b', 'August'),
            (r'\bFehruary\b', 'February'),
            (r'\bSeptemher\b', 'September'),
            (r'\bNovemher\b', 'November'),
            (r'\bDecemher\b', 'December'),
        ]
        for pat, repl in month_ocr_fixes:
            flat = re.sub(pat, repl, flat, flags=re.IGNORECASE)

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
            # Pattern 0 (HIGHEST PRIORITY): "Month D1 - D2, YYYY" or "from Month D1 to D2, YYYY"  e.g. "from June 16 to 19, 2026", "July 14 - 25, 2025"
            m = re.search(
                r'(?:from|dated)?\s*([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|to)\s*(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})',
                flat, re.IGNORECASE
            )
            if m:
                mon, d1, d2, yr = m.group(1), m.group(2), m.group(3), m.group(4)
                ns = normalize_date_to_ddmmyyyy(f"{d1} {mon} {yr}")
                ne = normalize_date_to_ddmmyyyy(f"{d2} {mon} {yr}")
                if ns and ne:
                    found_start, found_end = ns, ne

        if not found_start or not found_end:
            # Pattern 0b: "D1 - D2 Month, YYYY"  e.g. "14 - 18 July 2025", "15th - 19th June, 2026"
            m = re.search(
                r'(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|to)\s*(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9}),?\s*(\d{4})',
                flat, re.IGNORECASE
            )
            if m:
                d1, d2, mon, yr = m.group(1), m.group(2), m.group(3), m.group(4)
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
        # Priority order:
        #   A. Master-list text scan (most reliable — matches official names)
        #   B. Regex patterns for various certificate layouts
        # ==============================================================

        # A. Master-list scan FIRST — normalise dots so "Sushma.B" == "Sushma B"
        if faculty_master and not result["FACULTY NAME"]:
            flat_normalised = re.sub(r'[^a-z0-9\s]', ' ', flat.lower())
            flat_normalised = re.sub(r'\s+', ' ', flat_normalised)
            
            # 1. Substring match
            for fid, official_name in faculty_master.items():
                check = re.sub(r'^(dr|prof|mr|ms|mrs)\s+', '', official_name.lower()).strip()
                check_clean = re.sub(r'[^a-z0-9\s]', ' ', check)
                check_clean = re.sub(r'\s+', ' ', check_clean).strip()
                if check_clean and len(check_clean) > 3 and check_clean in flat_normalised:
                    result["FACULTY NAME"] = official_name
                    if not result["FACULTY ID"]:
                        result["FACULTY ID"] = fid
                    break

            # 2. Token overlap (e.g. Shilpa Shashikant of Chaudhari -> Shilpa, Shashikant, Chaudhari)
            if not result["FACULTY NAME"]:
                flat_words = set(w for w in flat_normalised.split() if len(w) >= 3)
                for fid, official_name in faculty_master.items():
                    check = re.sub(r'^(dr|prof|mr|ms|mrs)\s+', '', official_name.lower()).strip()
                    name_words = [w for w in re.sub(r'[^a-z0-9\s]', ' ', check).split() if len(w) >= 3]
                    overlap = sum(1 for w in name_words if w in flat_words)
                    if len(name_words) >= 2 and overlap >= 2:
                        result["FACULTY NAME"] = official_name
                        if not result["FACULTY ID"]:
                            result["FACULTY ID"] = fid
                        break
                    elif len(name_words) == 1 and overlap == 1 and len(name_words[0]) >= 6:
                        result["FACULTY NAME"] = official_name
                        if not result["FACULTY ID"]:
                            result["FACULTY ID"] = fid
                        break

            # 3. Fuzzy token scan (handles OCR artifacts like "Aks habhaKamath" -> "Akshatha Kamath")
            if not result["FACULTY NAME"]:
                import difflib
                flat_tokens = [w for w in flat_normalised.split() if len(w) >= 4]
                for fid, official_name in faculty_master.items():
                    check = re.sub(r'^(dr|prof|mr|ms|mrs)\s+', '', official_name.lower()).strip()
                    name_tokens = [w for w in re.sub(r'[^a-z0-9\s]', ' ', check).split() if len(w) >= 4]
                    matches = 0
                    for nt in name_tokens:
                        if any(nt in ft or ft in nt or difflib.SequenceMatcher(None, nt, ft).ratio() >= 0.72 for ft in flat_tokens):
                            matches += 1
                    if len(name_tokens) >= 1 and matches >= len(name_tokens):
                        result["FACULTY NAME"] = official_name
                        if not result["FACULTY ID"]:
                            result["FACULTY ID"] = fid
                        break

        # B. Regex fallback patterns
        if not result["FACULTY NAME"]:
            for pat in [
                # MSRIT internal layout: "Certify that Dr./ Mr./ Mrs./ Ms. Sushma.B" or "Ms.Aks habhaKamath"
                r'(?:certified that|certify that|presented to|awarded to)\s+'
                r'(?:(?:Dr|Prof|Mr|Ms|Mrs)\.?\s*[\/\-]\s*)*(?:Dr|Prof|Mr|Ms|Mrs)\.?\s*'
                r'([A-Za-z][a-zA-Z\.\s]{1,35})',
                # Simple "Certify that Dr. Name"
                r'(?:certified that|certify that|presented to|awarded to)\s+'
                r'(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+([A-Z][a-zA-Z\. ]{2,35})',
                r'\b(?:Dr\.|Prof\.)\s+([A-Z][a-zA-Z\s\.]{2,28})\b',
            ]:
                m = re.search(pat, flat, re.IGNORECASE)
                if m:
                    cand = m.group(1).strip()
                    cand = re.split(r'\s+(?:Dept|Dep|Department|Fac|Faculty|HOD|Incharge|Prof|of|from)\b', cand, flags=re.IGNORECASE)[0].strip()
                    cand = re.sub(r'^(?:Dr|Prof|Mr|Ms|Mrs)\.?\s*', '', cand, flags=re.IGNORECASE).strip()
                    bad_words = ["institute", "college", "university", "department", "mr.", "ms.", "mrs.", "dr.", "dr./", "five day", "faculty development"]
                    if cand and not any(b == cand.lower() or b in cand.lower() for b in bad_words) and len(cand) > 2:
                        result["FACULTY NAME"] = cand
                        break

        # ==============================================================
        # 4. FDP / PROGRAM NAME
        # ==============================================================
        if not result["FDP / PROGRAM NAME"]:
            # Pattern A: Quoted title: e.g. "Hands on Generative AI...", "Adaptive Learning..."
            m = re.search(r'["\u201c]([^"\u201d\r\n]{5,120})["\u201d]\s*,?\s*(?:from|conducted|organized)?', flat)
            if m:
                cand = m.group(1).strip(" -\"'")
                if len(cand) > 6 and not re.search(r'certificate|appreciation|participation', cand, re.IGNORECASE):
                    result["FDP / PROGRAM NAME"] = cand

        if not result["FDP / PROGRAM NAME"]:
            # Pattern B: Faculty Development Programme on X / Programme on X
            m = re.search(
                r'(?:Faculty Development Programme on|Faculty Development Program on|Programme on|Program on|FDP on|Workshop on|STTP on)\s*(?:[A-Z0-9\-]+\s+)?["\-]?\s*([^"\n\r,]{5,100})',
                flat, re.IGNORECASE
            )
            if m:
                cand = m.group(1).strip(" -\"'")
                cand = re.split(r'\s*(?:organized|conducted|from|held|during|\d{4}|January|February|March|April|May|June|July|August|September|October|November|December)\b', cand, flags=re.IGNORECASE)[0].strip()
                if len(cand) > 4:
                    result["FDP / PROGRAM NAME"] = cand

        if not result["FDP / PROGRAM NAME"]:
            # Pattern C: Title right before closing quote and from/conducted/organized (e.g. OCR missed opening quote)
            m = re.search(r'([A-Za-z0-9\s:]{8,100})["\u201d]\s*,?\s*(?:from|conducted|organized)', flat)
            if m:
                cand = m.group(1).strip(" -\"'")
                cand = re.split(r'\s+(?:Dept|Dep|CSERIT|RIT|MSRIT)\s+', cand, flags=re.IGNORECASE)[-1].strip()
                if len(cand) > 6 and not re.search(r'certificate|appreciation|participation', cand, re.IGNORECASE):
                    result["FDP / PROGRAM NAME"] = cand

        if not result["FDP / PROGRAM NAME"]:
            m = re.search(
                r'(?:Two-weeks|One-Week|One Week|Two Weeks|Five Days?|5-Day)?\s*Faculty Development Prog[a-z]*(?:\s+on)?\s*["\-]?\s*([^"\n\r,]{5,100})',
                flat, re.IGNORECASE
            )
            if m:
                cand = m.group(1).strip(" -\"'")
                cand = re.split(r'\s*(?:organized|conducted|from|held|during|\d{4}|January|February|March|April|May|June|July|August|September|October|November|December)\b', cand, flags=re.IGNORECASE)[0].strip()
                if len(cand) > 4:
                    result["FDP / PROGRAM NAME"] = cand

        if not result["FDP / PROGRAM NAME"]:
            # Pattern D: Standalone uppercase/block program titles (e.g. FEAI \n FOUNDATIONS OF ETHICAL AI)
            m = re.search(r'\b(?:FEAI|FDP|PROGRAMME|WORKSHOP)\s*\n?\s*([A-Z\s]{6,80})\b', text)
            if m:
                cand = m.group(1).strip()
                if not any(w in cand.lower() for w in ['certificate', 'participation', 'technology', 'hyderabad', 'ramaiah']):
                    result["FDP / PROGRAM NAME"] = cand.title()

        # ==============================================================
        # 5. PROGRAM INSTITUTION
        # ==============================================================
        if not result["PROGRAM INSTITUTION"]:
            m = re.search(
                r'(?:organized|conducted)\s+by\s+([^,\.]{4,100}(?:NIT|BITS|IIT|IIIT|College|Institute|University|Academy|TCS|SwipeGen|RVITM)[^,\.]*)',
                flat, re.IGNORECASE
            )
            if m:
                raw_org = m.group(1).strip()
                inst_tok = re.search(
                    r'(NIT[\s,]+[A-Za-z]+|BITS Pilani[\w\s]*|IIT[\s,]+[A-Za-z]+|IIIT[\s,]+[A-Za-z]+|BMS College of Engineering|Ramaiah Institute of Technology|MSRIT|RIT|Electronics and ICT Academy[\w\s,]*)',
                    raw_org, re.IGNORECASE
                )
                result["PROGRAM INSTITUTION"] = normalize_institution(
                    inst_tok.group(1) if inst_tok else raw_org
                )

        if not result["PROGRAM INSTITUTION"]:
            for pat in [
                r'\b(Electronics and ICT Academy[\w\s,]*)\b',
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
            # Multilevel alphanumeric IDs like MNITJ/APSCHE/QCOMP/48688/2025 or EICT/NITP/61/25-26/3776
            m = re.search(r'\b([A-Z0-9]{3,10}(?:\/[A-Z0-9_\-]+){2,6})\b', flat)
            if m:
                result["CERTIFICATE ID"] = m.group(1).strip()
            elif re.search(r'\b(CERT[-\s]?\d{3,4})\b', flat, re.IGNORECASE):
                result["CERTIFICATE ID"] = re.search(r'\b(CERT[-\s]?\d{3,4})\b', flat, re.IGNORECASE).group(1).strip()
            else:
                m = re.search(r'Ref\.?\s*No[:.]\s*([A-Za-z0-9\/\-]+)', flat)
                if m:
                    result["CERTIFICATE ID"] = m.group(1).strip()

        return result
