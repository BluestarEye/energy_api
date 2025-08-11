import re
import logging
import pandas as pd
from datetime import datetime

UTILITY_MAPPING = {
    "centerpoint": {"engie": "cpt", "atlantic": "centerpoint"},
    "aep texas central": {"engie": "aepcpl", "atlantic": "aep central"},
    "aep texas north": {"engie": "aepwtu", "atlantic": "aep north"},
    "oncor": {"engie": "oncor", "atlantic": "oncor"},
    "texas-new mexico power": {"engie": "tnmp", "atlantic": "tnmp"},
    # Add more mappings as needed
}

def normalize_start_month(val) -> str:
    #"""Normalize various date formats to 'Month YYYY'"""
    try:
        if pd.isnull(val):
            return "Unknown Start Month"
        if isinstance(val, datetime):
            return val.strftime("%B %Y")
        if not isinstance(val, str):
            val = str(val)
        val = val.strip()
        val = re.sub(r"\bstart\b", "", val, flags=re.IGNORECASE).strip()
        val = re.sub(r"[^\w\s/-]", "", val).strip()
        for fmt in ["%B %Y", "%b %Y", "%m/%d/%Y", "%Y-%m-%d"]:
            try:
                parsed = datetime.strptime(val, fmt)
                return parsed.strftime("%B %Y")
            except ValueError:
                continue
        parsed = pd.to_datetime(val, errors='coerce')
        if pd.isnull(parsed):
            raise ValueError("Unable to parse date")
        return parsed.strftime("%B %Y")
    except Exception as e:
        logging.warning(f"Failed to normalize Start Month '{val}': {e}")
        return "Unknown Start Month"
    
def normalize_utility(val: str) -> str:
    try:
        return val.strip().lower().replace(" ", "")
    except Exception as e:
        logging.warning(f"Failed to normalize Utility '{val}': {e}")
        return ""

def normalize_zone(val: str) -> str:
    try:
        return val.strip().upper()
    except Exception as e:
        logging.warning(f"Failed to normalize Zone '{val}': {e}")
        return ""
    
def resolve_utility_for_rep(input_val: str, rep_name: str) -> str:
    try:
        normalized = normalize_utility(input_val)
        rep_key = rep_name.lower()
        return UTILITY_MAPPING.get(normalized, {}).get(rep_key, normalized)
    except Exception as e:
        logging.warning(f"Failed to resolve utility for '{input_val}' and rep '{rep_name}': {e}")
        return normalized
    
def debug_column_headers(df):
    logging.info(f"Column headers: {list(df.columns)}")
    for i, col in enumerate(df.columns):
        logging.info(f"Col[{i}] = {repr(col)}")

def find_start_month_column(df):
    for col in df.columns:
        if isinstance(col, datetime):
            return col
        if isinstance(col, str) and re.search(r"start\s*date", col, re.IGNORECASE):
            return col
        if isinstance(col, str) and re.match(r"\d{4}-\d{2}-\d{2}", col.strip()):
            return col
    return None