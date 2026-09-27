import re
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

INTERNAL_ALIASES = {
    "MSRIT",
    "MSRITBANGALORE",
    "RIT",
    "RAMAIAHINSTITUTEOFTECHNOLOGY",
    "MSRAMAIAHINSTITUTEOFTECHNOLOGY",
    "RAMAIAHINSTITUTEOFTECHNOLOGYBANGALORE",
    "MSRAMAIAHINSTITUTEOFTECHNOLOGYBANGALORE"
}

def normalize_institution(inst_str: str) -> str:
    """
    Normalize institution name aliases for Ramaiah Institute of Technology.
    Known aliases: MSRIT, RIT, M.S. Ramaiah Institute of Technology,
    MSRIT Bangalore, etc.
    Does NOT merge genuinely different Ramaiah institutions such as
    Ramaiah University of Applied Sciences or Ramaiah Institute of Management.
    """
    if not inst_str:
        return "Unknown"
    
    clean_str = inst_str.strip()
    normalized = clean_str.upper().replace('.', '').strip()
    condensed = normalized.replace(' ', '').replace('-', '').replace(',', '')

    if condensed in INTERNAL_ALIASES:
        return "Ramaiah Institute of Technology"

    if "RAMAIAH INSTITUTE OF TECHNOLOGY" in normalized:
        return "Ramaiah Institute of Technology"

    return clean_str

def is_internal_program(institution_name: str) -> bool:
    """
    Internal/External refers to the FDP/program institution, NOT the faculty member.
    """
    norm = normalize_institution(institution_name)
    return norm.strip().lower() == "ramaiah institute of technology"

def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """
    Converts various date strings to a datetime object.
    Supports formats like:
    - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    - YYYY-MM-DD
    - 10 September 2026, September 10, 2026, 10th Sep 2026
    - 10/09/26 (two-digit year)
    """
    if not date_str:
        return None

    clean_str = str(date_str).strip()
    # Remove ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
    clean_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', clean_str, flags=re.IGNORECASE)
    clean_str = clean_str.replace(',', ' ').strip()
    clean_str = re.sub(r'\s+', ' ', clean_str)

    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
        "%Y-%m-%d", "%Y/%m/%d",
        "%d %B %Y", "%d %b %Y",
        "%B %d %Y", "%b %d %Y",
        "%d %B %y", "%d %b %y",
        "%B %d %y", "%b %d %y"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(clean_str, fmt)
            # Two digit year adjustment (if < 2000, e.g., 26 -> 2026)
            if dt.year < 100:
                dt = dt.replace(year=dt.year + 2000)
            elif dt.year < 1970:
                dt = dt.replace(year=dt.year + 100)
            return dt
        except ValueError:
            continue

    return None

def normalize_date_to_ddmmyyyy(date_str: str) -> Optional[str]:
    """
    Normalizes any supported date string to DD/MM/YYYY.
    """
    dt = parse_date_flexible(date_str)
    if dt:
        return dt.strftime("%d/%m/%Y")
    return None

def generate_date_range(start_str: str, end_str: str) -> Tuple[List[str], int]:
    """
    Generates list of dates formatted as DD/MM/YYYY and total day count.
    Raises ValueError if dates cannot be parsed or if end < start.
    """
    start_dt = parse_date_flexible(start_str)
    end_dt = parse_date_flexible(end_str)

    if not start_dt or not end_dt:
        raise ValueError(f"Unable to parse start date ({start_str}) or end date ({end_str})")

    if end_dt < start_dt:
        raise ValueError(f"End date ({end_str}) is earlier than start date ({start_str})")

    date_list = []
    curr = start_dt
    while curr <= end_dt:
        date_list.append(curr.strftime("%d/%m/%Y"))
        curr += timedelta(days=1)

    return date_list, (end_dt - start_dt).days + 1

def extract_month_year(date_str: str) -> Optional[str]:
    """
    Returns MM/YYYY for a given date string, or None if unparseable.
    """
    dt = parse_date_flexible(date_str)
    if dt:
        return dt.strftime("%m/%Y")
    return None

def extract_month_name_year(date_str: str) -> Optional[str]:
    """
    Returns e.g. "September 2026" for a given date string.
    """
    dt = parse_date_flexible(date_str)
    if dt:
        return dt.strftime("%B %Y")
    return None

def is_valid_file_extension(filename: str) -> bool:
    """
    Validates if file is PDF, JPG, JPEG, or PNG.
    """
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in ['pdf', 'jpg', 'jpeg', 'png']
