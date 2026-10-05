"""
Google Sheets Synchronization Module for MSRIT Training Feedback System.
Synchronizes the canonical 19-field Feedback record with the live Google Sheet:
https://docs.google.com/spreadsheets/d/1xxtuaEqJ8ygGhcMDlPLiZK8OgPicUh-qIPSEa7MjPL4/edit

Supports:
1. Google Service Account via gspread (GOOGLE_APPLICATION_CREDENTIALS, st.secrets, or service_account.json)
2. Google Apps Script Web App Webhook (GOOGLE_SHEETS_WEBHOOK_URL)
3. Graceful fallback & status reporting (SYNCED, PENDING, FAILED, NOT_CONFIGURED)
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Auto-load .env from project root so the webhook URL is picked up without
# any manual `export` command — just paste the URL in .env and restart.
# ---------------------------------------------------------------------------
def _load_dotenv():
    """Minimal .env loader — no external dependency needed."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value and value != "PASTE_YOUR_WEB_APP_URL_HERE":
                    os.environ.setdefault(key, value)
    except Exception:
        pass

_load_dotenv()

logger = logging.getLogger("sheets_sync")

DEFAULT_SPREADSHEET_ID = "1xxtuaEqJ8ygGhcMDlPLiZK8OgPicUh-qIPSEa7MjPL4"
DEFAULT_TAB_NAME = "TRAINING FEEDBACK"

CANONICAL_HEADERS = [
    "Feedback ID",
    "Created At",
    "Approved At",
    "Verification ID",
    "Certificate ID",
    "Faculty ID",
    "Faculty Name",
    "Department",
    "Training Date",
    "Training Program",
    "Program Type",
    "Presentation Rating",
    "Coverage of Topics",
    "Understanding Level",
    "Understanding Reason",
    "Future Programs",
    "Recommended Topics",
    "Feedback Status",
    "Rejection Reason"
]

def get_spreadsheet_id() -> str:
    """Retrieve spreadsheet ID from environment or default."""
    return os.environ.get("GOOGLE_SHEETS_SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID).strip()

def get_tab_name() -> str:
    """Retrieve worksheet tab name from environment or default."""
    return os.environ.get("GOOGLE_SHEETS_TAB_NAME", DEFAULT_TAB_NAME).strip()

def get_webhook_url() -> Optional[str]:
    """Retrieve optional Apps Script Webhook URL from environment or secrets."""
    url = os.environ.get("GOOGLE_SHEETS_WEBHOOK_URL") or os.environ.get("GOOGLE_APPS_SCRIPT_URL")
    if url and url.strip():
        return url.strip()
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "google_sheets_webhook" in st.secrets:
            return str(st.secrets["google_sheets_webhook"]).strip()
    except Exception:
        pass
    return None

def get_gspread_client():
    """
    Authenticate and return a gspread client if credentials exist.
    Checks:
    1. GOOGLE_APPLICATION_CREDENTIALS env var
    2. credentials/service_account.json or service_account.json
    3. GOOGLE_SERVICE_ACCOUNT_JSON env var (raw json)
    4. streamlit st.secrets["gcp_service_account"]
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        logger.warning("gspread or google-auth not installed.")
        return None

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # 1. Path from env var
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        try:
            creds = Credentials.from_service_account_file(cred_path, scopes=scopes)
            return gspread.authorize(creds)
        except Exception as e:
            logger.error(f"Error loading service account from {cred_path}: {e}")

    # 2. Local candidate files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "credentials", "service_account.json"),
        os.path.join(base_dir, "service_account.json"),
        os.path.expanduser("~/.config/gspread/service_account.json")
    ]
    for c_path in candidates:
        if os.path.exists(c_path):
            try:
                creds = Credentials.from_service_account_file(c_path, scopes=scopes)
                return gspread.authorize(creds)
            except Exception as e:
                logger.error(f"Error loading credentials from {c_path}: {e}")

    # 3. Raw JSON from env var
    raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw_json and raw_json.strip():
        try:
            info = json.loads(raw_json)
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            return gspread.authorize(creds)
        except Exception as e:
            logger.error(f"Error parsing GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

    # 4. Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "gcp_service_account" in st.secrets:
                creds_dict = dict(st.secrets["gcp_service_account"])
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                return gspread.authorize(creds)
    except Exception:
        pass

    return None

def extract_canonical_row_values(record: Dict[str, Any]) -> List[str]:
    """
    Extracts the exact 19 values matching CANONICAL_HEADERS from record.
    Preserves multi-line comments and strings with commas/quotes without splitting.
    """
    values = []
    for col in CANONICAL_HEADERS:
        val = record.get(col)
        if val is None:
            # Check lowercase alternatives
            alt_key = col.lower().replace(" ", "_")
            val = record.get(alt_key, "")
        values.append("" if val is None else str(val))
    return values

def get_sheets_sync_status() -> Dict[str, Any]:
    """
    Returns diagnostic information about Google Sheets connectivity.
    """
    spreadsheet_id = get_spreadsheet_id()
    tab_name = get_tab_name()
    webhook_url = get_webhook_url()
    client = get_gspread_client()

    has_client = client is not None
    has_webhook = webhook_url is not None

    if has_client:
        method = "Google Service Account (gspread)"
    elif has_webhook:
        method = "Apps Script Webhook"
    else:
        method = "None (Credentials not configured)"

    return {
        "spreadsheet_id": spreadsheet_id,
        "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
        "tab_name": tab_name,
        "is_configured": has_client or has_webhook,
        "auth_method": method,
        "has_service_account": has_client,
        "has_webhook": has_webhook
    }

def sync_feedback_to_google_sheet(feedback_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronizes a training-feedback record to the live Google Sheet.
    Uses Feedback ID as primary key.
    Updates in-place if record already exists; appends if new.
    Returns:
    {
        "success": bool,
        "status": "SYNCED" | "FAILED" | "NOT_CONFIGURED",
        "message": str,
        "row_index": Optional[int]
    }
    """
    if not feedback_record:
        return {"success": False, "status": "FAILED", "message": "Empty feedback record"}

    fid = str(feedback_record.get("Feedback ID") or feedback_record.get("feedback_id") or "").strip()
    if not fid:
        return {"success": False, "status": "FAILED", "message": "Record missing Feedback ID"}

    spreadsheet_id = get_spreadsheet_id()
    tab_name = get_tab_name()
    row_values = extract_canonical_row_values(feedback_record)

    # 1. Try Google Service Account via gspread
    client = get_gspread_client()
    if client:
        try:
            sh = client.open_by_key(spreadsheet_id)
            try:
                worksheet = sh.worksheet(tab_name)
            except Exception:
                # Worksheet does not exist, create it with canonical headers
                worksheet = sh.add_worksheet(title=tab_name, rows=100, cols=25)
                worksheet.append_row(CANONICAL_HEADERS)

            # Check if Feedback ID already exists in Column 1
            col_fids = worksheet.col_values(1)
            row_idx = None
            for idx, existing_id in enumerate(col_fids, start=1):
                if existing_id.strip() == fid:
                    row_idx = idx
                    break

            if row_idx is not None:
                # Update existing row
                cell_range = f"A{row_idx}:S{row_idx}"
                worksheet.update(cell_range, [row_values])
                msg = f"Updated row {row_idx} in Google Sheet tab '{tab_name}'"
                logger.info(msg)
                return {"success": True, "status": "SYNCED", "message": msg, "row_index": row_idx}
            else:
                # Append new row
                worksheet.append_row(row_values)
                row_idx = len(col_fids) + 1
                msg = f"Appended row {row_idx} to Google Sheet tab '{tab_name}'"
                logger.info(msg)
                return {"success": True, "status": "SYNCED", "message": msg, "row_index": row_idx}
        except Exception as e:
            err_msg = f"Google Sheets API error: {e}"
            logger.error(err_msg)
            return {"success": False, "status": "FAILED", "message": err_msg}

    # 2. Try Apps Script Webhook
    webhook_url = get_webhook_url()
    if webhook_url:
        try:
            payload = {
                "action": "sync_feedback",
                "spreadsheet_id": spreadsheet_id,
                "tab_name": tab_name,
                "headers": CANONICAL_HEADERS,
                "record": feedback_record,
                "row_values": row_values
            }
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                if resp_data.get("success"):
                    msg = resp_data.get("message", "Synced via Apps Script Webhook")
                    return {"success": True, "status": "SYNCED", "message": msg, "row_index": resp_data.get("row_index")}
                else:
                    return {"success": False, "status": "FAILED", "message": resp_data.get("error", "Webhook returned failure")}
        except Exception as e:
            err_msg = f"Apps Script Webhook error: {e}"
            logger.error(err_msg)
            return {"success": False, "status": "FAILED", "message": err_msg}

    # 3. Not configured
    return {
        "success": False,
        "status": "NOT_CONFIGURED",
        "message": "Google Sheets integration is active in application logic, but credentials (service_account.json or webhook URL) are not yet configured."
    }
