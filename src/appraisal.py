"""
src/appraisal.py
Faculty Self-Appraisal Module for Points 16 and 17.

Institutional Appraisal Rules:
- Point 16: No. of events participated outside the institute (FDP/Seminar/Workshop/Conference)
- Point 17: No. of events participated inside the institute (FDP/Seminar/Workshop/Conference)

Key Principles:
1. Points 16 and 17 are counted from ALL certificates/events regardless of verification outcome
   (Valid or Invalid certificates are both counted — only the venue classification matters).
2. Events at Ramaiah Institute of Technology (MSRIT/RIT) are Internal (Point 17).
3. Events at other institutions are External (Point 16).
4. Events with unknown/unconfirmed venues are flagged as 'Pending Classification'.
5. Scoring rules are configurable; when not provided, scores are not fabricated.
"""

import os
import json
import re
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from src.utils import normalize_institution, is_internal_program, generate_date_range, normalize_date_to_ddmmyyyy

INTERNAL_ALIASES = [
    "ramaiah institute of technology",
    "m.s. ramaiah institute of technology",
    "msrit",
    "msrit bangalore",
    "rit"
]

def _safe_str(val: Any) -> str:
    """Convert None, float('nan'), or any non-string into a clean stripped string."""
    if val is None:
        return ""
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return ""
    return str(val).strip()

def norm_str(s: Any) -> str:
    """Normalizes string for comparison by removing non-alphanumeric chars."""
    if s is None:
        return ""
    return re.sub(r'[^a-z0-9]+', ' ', _safe_str(s).lower()).strip()

def classify_venue(venue: str, aliases: Optional[List[str]] = None) -> str:
    """
    Classifies an event venue as 'Internal', 'External', or 'Unknown'.
    """
    v = norm_str(venue)
    if not v or v in ["unknown", "none", "not available"]:
        return "Unknown"
    
    check_aliases = aliases or INTERNAL_ALIASES
    for a in check_aliases:
        if norm_str(a) in v:
            return "Internal"
            
    # Also check our central utils helper
    if is_internal_program(normalize_institution(venue)):
        return "Internal"
        
    return "External"

def normalize_status(status_str: Any) -> str:
    """Standardizes certificate verification status to Valid, Invalid, or Pending Review."""
    s = norm_str(status_str)
    if s == "valid":
        return "Valid"
    if s == "invalid":
        return "Invalid"
    return "Pending Review"

def parse_iso_date(d_str: str) -> Optional[datetime]:
    """Parses DD/MM/YYYY or YYYY-MM-DD into a datetime object."""
    if not d_str:
        return None
    d_clean = str(d_str).strip()
    # Try DD/MM/YYYY
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', d_clean):
        try:
            return datetime.strptime(d_clean, "%d/%m/%Y")
        except ValueError:
            pass
    # Try YYYY-MM-DD
    if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', d_clean):
        try:
            return datetime.strptime(d_clean, "%Y-%m-%d")
        except ValueError:
            pass
    return None

def is_in_period(date_str: str, period_range: Optional[Tuple[datetime, datetime]]) -> bool:
    """Checks whether date falls within [start, end) period."""
    if not period_range or not date_str:
        return True
    dt = parse_iso_date(date_str)
    if not dt:
        return False
    return period_range[0] <= dt < period_range[1]

def calculate_scores(p16: int, p17: int, scoring_config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Calculates appraisal scores using configured rules.
    Returns None if scoring rules are not configured, avoiding fabricated scores.
    """
    if not scoring_config:
        return None
    
    w16 = scoring_config.get("w16")
    w17 = scoring_config.get("w17")
    if w16 is None or w17 is None:
        return None
        
    total = p16 * float(w16) + p17 * float(w17)
    max_score = scoring_config.get("max")
    if max_score is not None:
        total = min(total, float(max_score))
        
    bonus_fn = scoring_config.get("bonus")
    bonus = 0.0
    if callable(bonus_fn):
        bonus = float(bonus_fn(p16, p17))
    elif isinstance(bonus_fn, (int, float)):
        bonus = float(bonus_fn)
        
    return {
        "total": total,
        "bonus": bonus,
        "final": total + bonus
    }

def compute_appraisal(
    faculty: Dict[str, Any],
    data: Dict[str, List[Dict[str, Any]]],
    start_year: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Core calculation function for Faculty Self-Appraisal Points 16 and 17.
    Accepts faculty dict and data dict containing 'attendance' and 'certificates'.
    """
    cfg = config or {}
    fac_id = str(faculty.get("id", "")).strip()
    fac_name = str(faculty.get("name", "")).strip()
    
    # Filter for this faculty member (guard against None data on connection failure)
    att_list = [a for a in (data.get("attendance") or []) if str(a.get("facultyId", "")).strip() == fac_id]
    certs_all = [c for c in (data.get("certificates") or []) if str(c.get("facultyId", "")).strip() == fac_id]
    
    # Event unification map
    events: Dict[str, Dict[str, Any]] = {}
    dup_events = 0
    dup_certs = 0
    
    def get_event_key(item: Dict[str, Any]) -> str:
        if item.get("eventId"):
            return f"id:{item['eventId']}"
        e_name = norm_str(item.get("eventName", ""))
        s_date = str(item.get("startDate", "")).strip()
        return f"n:{e_name}|{s_date}"

    # 1. Ingest Attendance participation evidence
    for a in att_list:
        k = get_event_key(a)
        if k not in events:
            events[k] = {
                "key": k,
                "name": a.get("eventName", "") or "",
                "venue": a.get("venue", "") or "",
                "start": a.get("startDate", "") or "",
                "end": a.get("endDate", "") or "",
                "attended": None,
                "cert": None,
                "has_att": False
            }
        e = events[k]
        if e["attended"] is not None or e["has_att"]:
            dup_events += 1
        e["has_att"] = True
        e["name"] = e["name"] or a.get("eventName", "")
        e["venue"] = e["venue"] or a.get("venue", "")
        e["start"] = e["start"] or a.get("startDate", "")
        e["end"] = e["end"] or a.get("endDate", "")
        
        att_val = a.get("attended")
        if att_val is True:
            e["attended"] = True
        elif att_val is False and e["attended"] is not True:
            e["attended"] = False

    # 2. Ingest Certificate verification submissions
    rank_order = {"Valid": 3, "Pending Review": 2, "Invalid": 1}
    for c in certs_all:
        k = get_event_key(c)
        if k not in events:
            events[k] = {
                "key": k,
                "name": c.get("eventName", "") or "",
                "venue": c.get("venue", "") or "",
                "start": c.get("startDate", "") or "",
                "end": c.get("endDate", "") or "",
                "attended": None,
                "cert": None,
                "has_att": False
            }
        e = events[k]
        st = normalize_status(c.get("status", "Pending Review"))
        
        if e["cert"]:
            dup_certs += 1
            curr_st = e["cert"]["st"]
            if rank_order.get(st, 0) <= rank_order.get(curr_st, 0):
                continue
                
        e["cert"] = {"c": c, "st": st}
        e["name"] = e["name"] or c.get("eventName", "")
        e["venue"] = e["venue"] or c.get("venue", "")
        e["start"] = e["start"] or c.get("startDate", "")
        e["end"] = e["end"] or c.get("endDate", "")

    # Period range if configured
    p_cfg = cfg.get("period")
    period_range = None
    if p_cfg and start_year:
        sm = p_cfg.get("startMonth", 8)
        sd = p_cfg.get("startDay", 1)
        s_dt = datetime(start_year, sm, sd)
        e_dt = datetime(start_year + 1, sm, sd)
        period_range = (s_dt, e_dt)

    p16 = 0
    p17 = 0
    report_rows = []

    # 3. Classify and evaluate each unique event
    # All events are counted into Point 16 or Point 17 based solely on venue.
    # Certificate validity (Valid/Invalid) and attendance status do NOT gate inclusion.
    for e in events.values():
        cls_venue = classify_venue(e["venue"], cfg.get("internalAliases"))
        contrib = "Neither"
        why = ""

        if cls_venue == "Unknown":
            contrib = "Pending Classification"
            why = "Event venue could not be established."
        elif period_range and not e["start"]:
            contrib = "Pending Classification"
            why = "Event dates require confirmation."
        elif period_range and not is_in_period(e["start"], period_range):
            contrib = "Neither"
            why = "Event falls outside the appraisal period."
        elif cls_venue == "Internal":
            contrib = "Point 17"
            p17 += 1
        else:
            contrib = "Point 16"
            p16 += 1

        # Determine certificate verification outcome and reason
        st = None
        reason = ""
        if e["cert"]:
            c_raw = e["cert"]["c"]
            st = e["cert"]["st"]
            if c_raw.get("reason"):
                reason = c_raw["reason"]
            elif st != "Valid":
                c_fname = c_raw.get("facultyName", "")
                if c_fname and norm_str(c_fname) != norm_str(fac_name):
                    reason = "Faculty name does not match the available faculty record."
                elif not e["venue"]:
                    reason = "Event venue could not be established."
                elif not e["start"]:
                    reason = "Event dates require confirmation."

        def fmt_dates(s, end):
            if not s:
                return ""
            if end and end != s:
                return f"{s} to {end}"
            return s

        report_rows.append({
            "name": e["name"],
            "venue": e["venue"] or "Not available",
            "dates": fmt_dates(e["start"], e["end"]) or "Not available",
            "cls": "Unknown (review)" if cls_venue == "Unknown" else cls_venue,
            "st": st or "No certificate submitted",
            "reason": reason or "—",
            "contrib": contrib,
            "why": why
        })

    # Certificate statistics (counted from events with submitted certificates)
    submitted_rows = [r for r in report_rows if r["st"] != "No certificate submitted"]
    stats = {
        "total": len(submitted_rows),
        "valid": sum(1 for r in submitted_rows if r["st"] == "Valid"),
        "invalid": sum(1 for r in submitted_rows if r["st"] == "Invalid"),
        "pending": sum(1 for r in submitted_rows if r["st"] == "Pending Review")
    }

    # Score calculation
    scores = calculate_scores(p16, p17, cfg.get("scoring"))

    return {
        "p16": p16,
        "p17": p17,
        "rows": report_rows,
        "stats": stats,
        "dup_events": dup_events,
        "dup_certs": dup_certs,
        "flagged": sum(1 for r in report_rows if r["contrib"] == "Pending Classification"),
        "period_applied": period_range is not None,
        "scores": scores
    }

def build_appraisal_datasets(data_loader) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transforms the repository's DataLoader records into the standardized
    JSON datasets for faculty, attendance, and certificates.
    """
    tracker_rows = data_loader.get_certificate_tracker_rows()
    
    # 1. Faculty dataset
    faculty_list = []
    for fid, fname in data_loader.faculty_by_id.items():
        s_fid = _safe_str(fid)
        s_fname = _safe_str(fname)
        dept = _safe_str(data_loader.faculty_department_by_id.get(s_fid, "")) or "Artificial Intelligence & Machine Learning"
        faculty_list.append({
            "id": s_fid,
            "name": s_fname,
            "department": dept,
            "designation": "Assistant Professor"
        })

    # 2. Certificates & Attendance datasets
    cert_list = []
    att_list = []

    for idx, r in enumerate(tracker_rows, 1):
        cid = _safe_str(r.get("CERTIFICATE ID")) or f"CERT-{idx:03d}"
        fid = _safe_str(r.get("FACULTY ID"))
        fname = _safe_str(r.get("FACULTY NAME"))
        pname = _safe_str(r.get("FDP / PROGRAM NAME"))
        venue = _safe_str(r.get("PROGRAM INSTITUTION"))
        ptype = _safe_str(r.get("PROGRAM TYPE")).upper()
        s_date = _safe_str(r.get("START DATE"))
        e_date = _safe_str(r.get("END DATE"))
        vres = _safe_str(r.get("VERIFICATION RESULT")).upper()
        reason = _safe_str(r.get("VERIFICATION REASON"))
        
        status_str = "Valid" if vres == "VALID" else ("Invalid" if vres == "INVALID" else "Pending Review")
        event_id = f"EVT-{idx:03d}"
        
        cert_list.append({
            "certId": cid,
            "facultyId": fid,
            "facultyName": fname,
            "eventId": event_id,
            "eventName": pname,
            "venue": venue,
            "startDate": s_date,
            "endDate": e_date,
            "status": status_str,
            "reason": reason
        })
        
        # Determine attendance participation
        is_internal = is_internal_program(normalize_institution(venue)) or ptype == "INTERNAL"
        
        try:
            dates, _ = generate_date_range(s_date, e_date)
        except Exception:
            dates = []
            
        if not dates:
            attended = None
        else:
            statuses = [data_loader.get_attendance(fid, d) for d in dates]
            has_none = any(st is None for st in statuses)
            
            has_conflict = False
            for st in statuses:
                if st is None:
                    continue
                st_u = st.strip().upper()
                if st_u in ["CASUAL LEAVE", "EMERGENCY LEAVE", "UNPAID LEAVE"]:
                    has_conflict = True
                    break
                if not is_internal and st_u == "PRESENT":
                    has_conflict = True
                    break
                    
            if has_conflict:
                attended = False
            elif has_none:
                attended = None
            else:
                attended = True
                
        att_list.append({
            "facultyId": fid,
            "eventId": event_id,
            "eventName": pname,
            "venue": venue,
            "startDate": s_date,
            "endDate": e_date,
            "attended": attended
        })

    return {
        "faculty": faculty_list,
        "attendance": att_list,
        "certificates": cert_list
    }

def export_appraisal_json_files(data_loader, output_dir: Optional[str] = None):
    """
    Exports data/faculty.json, data/attendance.json, and data/certificates.json
    so that frontend static HTML can fetch or load them directly.
    """
    if not output_dir:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, "data")
    os.makedirs(output_dir, exist_ok=True)

    datasets = build_appraisal_datasets(data_loader)
    for k in ["faculty", "attendance", "certificates"]:
        fpath = os.path.join(output_dir, f"{k}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(datasets[k], f, indent=2, ensure_ascii=False)
            
    return datasets
