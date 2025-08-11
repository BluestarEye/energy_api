import pandas as pd
import logging
import re
from datetime import datetime

def auto_detect_header(path: str, sheet_name=0, preview_rows=10) -> int:
    preview_df = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=preview_rows, engine="openpyxl")
    target_cols = {"start month", "utility", "congestion zone", "load factor"}
    for idx, row in preview_df.iterrows():
        row_set = set(str(cell).strip().lower() for cell in row if pd.notnull(cell))
        if target_cols.issubset(row_set):
            return idx
    raise ValueError(f"Could not detect header row for {path}")

def normalize_start_month(val):
    if pd.isnull(val):
        logging.warning("Start Month null value found")
        return "Unknown Start Month"
    try:
        if isinstance(val, pd.Timestamp):
            return val.strftime("%B %Y Start")
        if isinstance(val, str):
            val = val.strip()
            val = re.sub(r"\bstart\b", "", val, flags=re.IGNORECASE).strip()
            val = re.sub(r"[^\w\s/-]", "", val).strip()
        for fmt in ["%B %Y", "%b %Y", "%m/%d/%Y", "%Y-%m-%d"]:
            try:
                parsed = datetime.strptime(val, fmt)
                return parsed.strftime("%B %Y Start")
            except ValueError:
                continue
        parsed = pd.to_datetime(val, errors='coerce')
        if pd.isnull(parsed):
            raise ValueError("Unable to parse date")
        return parsed.strftime("%B %Y Start")
    except Exception as e:
        logging.warning(f"Failed to normalize Start Month '{val}': {e}")
        return "Unknown Start Month"

def load_freepoint(freepoint_path, sheet_name=0):
    header_row = auto_detect_header(freepoint_path, sheet_name=sheet_name)
    df = pd.read_excel(freepoint_path, sheet_name=sheet_name, header=header_row, engine="openpyxl")
    for col in df.columns:
        if col.strip().lower() == "start month":
            df.rename(columns={col: "Start Month"}, inplace=True)
            break
    df["Start Month"] = df["Start Month"].apply(normalize_start_month)
    return df
